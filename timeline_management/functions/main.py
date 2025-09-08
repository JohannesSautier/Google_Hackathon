import firebase_admin
from firebase_admin import firestore
from firebase_functions import https_fn, options, firestore_fn
from datetime import datetime, timedelta, timezone
import json 
from firebase_admin import storage
from firebase_functions import storage_fn

# We will move our data classes to a separate file for better organization
# from models import ProcessStep, AgentFinding, JourneyEvent 

# --- App Initialization ---
options.set_global_options(region="europe-west1")

# --- API Endpoint 1: Create a Journey ---
@https_fn.on_request()
def create_journey(req: https_fn.Request) -> https_fn.Response:
    """HTTP endpoint to create a new journey document in Firestore."""
    if not firebase_admin._apps:
        firebase_admin.initialize_app()
    db = firestore.client()
    
    if req.method != "POST":
        return https_fn.Response("Method Not Allowed", status=405)
    try:
        data = req.get_json()
        required_fields = ["userId", "originCountry", "destinationCountry", "nationality", "purpose"]
        if not all(field in data for field in required_fields):
            return https_fn.Response("Missing required fields.", status=400)
        
        journey_doc = {**data, "status": "PENDING", "timeline": [], "createdAt": firestore.SERVER_TIMESTAMP}
        _ , doc_ref = db.collection("journeys").add(journey_doc)
        print(f"Successfully created journey with ID: {doc_ref.id}")
        return https_fn.Response(f"Journey created successfully with ID: {doc_ref.id}", status=201)
    except Exception as e:
        print(f"Error creating journey: {e}")
        return https_fn.Response("An internal error occurred.", status=500)

@https_fn.on_request()
def get_journey(req: https_fn.Request) -> https_fn.Response:
    """HTTP endpoint to retrieve a journey document from Firestore."""

    # This is a helper function to handle non-serializable types
    def json_converter(o):
        if isinstance(o, datetime):
            return o.isoformat()
        raise TypeError(f"Object of type {o.__class__.__name__} is not JSON serializable")

    if not firebase_admin._apps:
        firebase_admin.initialize_app()
    db = firestore.client()
    
    if req.method != "GET":
        return https_fn.Response("Method Not Allowed", status=405)
        
    journey_id = req.args.get("id")
    if not journey_id:
        return https_fn.Response("Missing 'id' query parameter.", status=400)
        
    try:
        doc = db.collection("journeys").document(journey_id).get()
        if doc.exists:
            # THE FIX IS HERE: Use the 'default' parameter in json.dumps()
            response_body = json.dumps(doc.to_dict(), default=json_converter)
            
            return https_fn.Response(
                response_body,
                status=200,
                headers={"Content-Type": "application/json"}
            )
        else:
            return https_fn.Response("Journey not found.", status=404)
    except Exception as e:
        print(f"Error getting journey: {e}")
        return https_fn.Response("An internal error occurred.", status=500)

# --- API Endpoint: Add Agent Finding (Updated for Data Points) ---
@https_fn.on_request()
def add_agent_finding(req: https_fn.Request) -> https_fn.Response:
    """Accepts a batch of data points, saves them, and queues them for processing."""
    if not firebase_admin._apps:
        firebase_admin.initialize_app()
    db = firestore.client()

    if req.method != "POST":
        return https_fn.Response("Method Not Allowed", status=405)

    try:
        request_data = req.get_json()
        data_points = request_data.get("dataPoints", [])
        
        if not data_points:
            return https_fn.Response("Request body must contain a 'dataPoints' array.", status=400)

        # Batch process each data point
        for data_point in data_points:
            # Add journeyId to each data point for easier querying
            journey_id = data_point.get("journeyId")
            if not journey_id:
                print("Skipping data point with no journeyId")
                continue

            # Save the data point to its own collection
            dp_ref = db.collection("data_points").document()
            dp_ref.set(data_point)
            
            # Create a corresponding event to trigger the processing logic
            event_data = {
                "journeyId": journey_id,
                "dataPointId": dp_ref.id, # Link to the data point
                "status": "PENDING",
                "createdAt": datetime.now(timezone.utc).isoformat(),
            }
            db.collection("journey_events").add(event_data)

        return https_fn.Response(f"{len(data_points)} data points received and queued.", status=202)
    except Exception as e:
        print(f"Error adding data points: {e}")
        return https_fn.Response("Internal Server Error", status=500)

# --- Background Function: Process Journey Event (Updated for Data Points) ---
@firestore_fn.on_document_created(document="journey_events/{eventId}")
def process_journey_event(event: firestore_fn.Event[firestore_fn.Change]) -> None:
    """Processes events triggered by new data points."""
    if not firebase_admin._apps:
        firebase_admin.initialize_app()
    db = firestore.client()

    event_id = event.params["eventId"]
    event_data = event.data.to_dict()

    if event_data.get("status") != "PENDING":
        return

    try:
        data_point_id = event_data["dataPointId"]
        journey_id = event_data["journeyId"]
        
        # Fetch the relevant documents
        data_point_doc = db.collection("data_points").document(data_point_id).get()
        journey_doc = db.collection("journeys").document(journey_id).get()

        if not data_point_doc.exists or not journey_doc.exists:
            raise ValueError("DataPoint or Journey document not found.")

        data_point = data_point_doc.to_dict()
        journey = journey_doc.to_dict()
        
        # --- NEW LOGIC: Check the dataType ---
        if data_point.get("dataType") == "INFORMATIONAL":
            note = "Informational data point stored. No action taken."
            db.collection("journey_events").document(event_id).update({"status": "PROCESSED", "notes": note})
            return

        elif data_point.get("dataType") == "PROPOSAL":
            proposal = data_point.get("proposal")
            confidence = data_point.get("confidenceScore", 0)

            if not proposal or confidence < 0.7:
                note = f"Proposal ignored due to low confidence ({confidence}) or missing proposal."
                db.collection("journey_events").document(event_id).update({"status": "IGNORED", "notes": note})
                return

            # --- NEW LOGIC: Process the proposal action ---
            if proposal.get("action") == "UPDATE_STEP_STATUS":
                target_key = proposal.get("targetStepKey")
                payload = proposal.get("payload", {})
                shift_days = payload.get("shiftDays")
                
                if not target_key or shift_days is None:
                    raise ValueError("Proposal is missing targetStepKey or shiftDays.")

                updated_timeline = journey.get("timeline", [])
                step_updated = False
                for step in updated_timeline:
                    if step.get("stepId") == target_key:
                        # --- NEW LOGIC: Date shifting ---
                        old_end_date_str = step["estimatedEndDate"]
                        # Convert string to datetime object
                        old_end_date = datetime.fromisoformat(old_end_date_str)
                        # Apply the shift
                        new_end_date = old_end_date + timedelta(days=shift_days)
                        # Convert back to string and update
                        step["estimatedEndDate"] = new_end_date.isoformat()
                        
                        step_updated = True
                        break
                
                if step_updated:
                    db.collection("journeys").document(journey_id).update({"timeline": updated_timeline})
                    note = f"Timeline for step '{target_key}' shifted by {shift_days} days."
                    db.collection("journey_events").document(event_id).update({"status": "PROCESSED", "notes": note})
                else:
                    note = f"Target step '{target_key}' not found in timeline."
                    db.collection("journey_events").document(event_id).update({"status": "IGNORED", "notes": note})

    except Exception as e:
        print(f"Error processing event {event_id}: {e}")
        db.collection("journey_events").document(event_id).update({"status": "ERROR", "notes": str(e)})

# --- API Endpoint 4: Upload a Document ---
@https_fn.on_request()
def upload_document(req: https_fn.Request) -> https_fn.Response:
    """
    HTTP endpoint to upload a document to Cloud Storage.
    Expects a 'multipart/form-data' request with a 'document' file
    and a 'journeyId' field.
    """
    if not firebase_admin._apps:
        firebase_admin.initialize_app()

    # This is a security check. In a real app, you'd also verify the user's auth token.
    if req.method != "POST":
        return https_fn.Response("Method Not Allowed", status=405)

    try:
        # Extract file and journeyId from the multipart request
        document_file = req.files.get("document")
        journey_id = req.form.get("journeyId")

        if not document_file or not journey_id:
            return https_fn.Response("Missing 'document' file or 'journeyId' field.", status=400)

        # Get the default storage bucket
        bucket = storage.bucket() # Your default Cloud Storage bucket
        
        # Define the path in the bucket where the file will be stored
        # e.g., user_documents/abc-123/visa_application.pdf
        destination_blob_name = f"user_documents/{journey_id}/{document_file.filename}"
        
        blob = bucket.blob(destination_blob_name)

        print(f"Uploading file '{document_file.filename}' to '{destination_blob_name}'...")
        
        # Upload the file from memory
        blob.upload_from_file(document_file)

        print("File uploaded successfully.")
        return https_fn.Response(f"File {document_file.filename} uploaded successfully.", status=200)

    except Exception as e:
        print(f"Error uploading document: {e}")
        return https_fn.Response("Internal Server Error", status=500)


# --- Background Function 3: Process a Document on Upload ---
@storage_fn.on_object_finalized()
def process_document(event: storage_fn.CloudEvent) -> None:
    """
    Triggered when a new file is uploaded to Cloud Storage. This function
    simulates document parsing and saves the metadata to Firestore.
    """
    if not firebase_admin._apps:
        firebase_admin.initialize_app()
    db = firestore.client()

    bucket_name = event.data.bucket
    file_path = event.data.name
    
    # We only want to process files in our 'user_documents' folder.
    if not file_path.startswith("user_documents/"):
        print(f"Ignoring file '{file_path}' as it's not in 'user_documents/'.")
        return

    print(f"Processing new document: gs://{bucket_name}/{file_path}")

    try:
        # Extract journeyId from the file path (e.g., 'user_documents/abc-123/file.pdf')
        parts = file_path.split("/")
        if len(parts) < 3:
            print(f"Could not extract journeyId from path: {file_path}")
            return
        journey_id = parts[1]
        
        # --- SIMULATE AI DOCUMENT PARSING ---
        # In a real app, you would download the file content and send it to
        # Document AI or the Gemini API to generate this payload.
        # For the hackathon, we'll use the hardcoded structure you provided.
        print("Simulating document parsing with an AI model...")
        parsed_metadata = {
            "journeyId": journey_id,
            "sourceURI": f"gs://{bucket_name}/{file_path}", # Link to the file in Storage
            "documentType": "OFFICIAL_VISA_GUIDE",
            "llmSummary": "This is the primary U.S. Department of State guide for student visas...",
            "extractedTimelines": [
                {
                    "processType": "VISA_APPLICATION",
                    "description": "Students can receive their I-20 up to 365 days before the program start date.",
                    "value": 365,
                    "unit": "days_before_start"
                },
                {
                    "timelineKey": "INSURANCE",
                    "description": "You may apply for your Insurance as soon as you receive your Form I-20.",
                    "value": None,
                    "unit": None
                }
            ],
            "processedAt": firestore.SERVER_TIMESTAMP
        }

        # Save the structured metadata to the 'parsed_documents' collection
        db.collection("parsed_documents").add(parsed_metadata)
        print(f"Successfully saved parsed metadata for journey '{journey_id}' to Firestore.")

    except Exception as e:
        print(f"Error processing document {file_path}: {e}")
        
# --- Helper Function: Mock Gemini Call ---
def _generate_timeline_from_docs(docs: list) -> list:
    """
    This function simulates a call to the Gemini API.
    It takes parsed document data and returns a structured timeline.
    """
    print("Simulating Gemini API call to generate timeline...")
    # In a real implementation, you would format the content of the `docs`
    # into a prompt and call a model like Gemini 1.5 Flash.
    
    # For our test, we'll return a hardcoded, plausible timeline.
    mock_timeline = [
        {
            "stepId": "BANKACCOUNT_OPEN",
            "title": "Open German Blocked Bank Account",
            "description": "Based on Proof of Finance documents, open a blocked account (Sperrkonto).",
            "status": "NOT_STARTED",
            "estimatedStartDate": "2025-10-01T00:00:00",
            "estimatedEndDate": "2025-10-07T00:00:00",
            "dependencies": [],
        },
        {
            "stepId": "INSURANCE_GET",
            "title": "Get German Health Insurance",
            "description": "Based on insurance guides, acquire valid health insurance for the visa application.",
            "status": "NOT_STARTED",
            "estimatedStartDate": "2025-10-01T00:00:00",
            "estimatedEndDate": "2025-10-05T00:00:00",
            "dependencies": [],
        },
        {
            "stepId": "VISA_APPLICATION_SUBMIT",
            "title": "Submit Visa Application",
            "description": "Compile all documents (Proof of Finance, Insurance, etc.) and submit the application.",
            "status": "NOT_STARTED",
            "estimatedStartDate": "2025-10-08T00:00:00",
            "estimatedEndDate": "2025-12-08T00:00:00",
            "dependencies": ["BANKACCOUNT_OPEN", "INSURANCE_GET"],
        },
    ]
    return mock_timeline

# --- Background Function 4: Timeline Orchestrator ---
@firestore_fn.on_document_created(document="parsed_documents/{docId}")
def orchestrate_timeline_generation(event: firestore_fn.Event[firestore_fn.Change]) -> None:
    """
    Triggered when new parsed document metadata is created. Checks if enough
    information exists to generate a timeline, and if so, triggers the process.
    """
    if not firebase_admin._apps:
        firebase_admin.initialize_app()
    db = firestore.client()

    parsed_doc_data = event.data.to_dict()
    journey_id = parsed_doc_data.get("journeyId")

    if not journey_id:
        print("Parsed document is missing a journeyId. Skipping.")
        return

    try:
        # 1. Fetch ALL parsed documents for this journey
        docs_query = db.collection("parsed_documents").where("journeyId", "==", journey_id).stream()
        all_parsed_docs = [doc.to_dict() for doc in docs_query]
        
        # 2. Check if we have documents for all required processes (State Management)
        required_processes = {"VISA_APPLICATION", "INSURANCE", "PROOFFINANCE", "BANKACCOUNT"}
        found_processes = set()
        
        for doc in all_parsed_docs:
            for timeline_info in doc.get("extractedTimelines", []):
                # Check both keys from your sample payload
                process_type = timeline_info.get("processType") or timeline_info.get("timelineKey")
                if process_type:
                    found_processes.add(process_type)
        
        print(f"Journey {journey_id}: Found documents for processes: {found_processes}")

        # 3. Decide whether to trigger timeline generation
        if not required_processes.issubset(found_processes):
            # LATENT STATE: Still waiting on more documents
            print(f"Still waiting for all required documents. Need {required_processes - found_processes}.")
            db.collection("journeys").document(journey_id).set({"timelineStatus": "AWAITING_DOCUMENTS"}, merge=True)
            return
        
        # GEMINI STATE: We have everything we need!
        print("All required document types found! Proceeding to generate timeline.")
        
        # 4. Call our (mock) Gemini function to get the timeline
        generated_timeline = _generate_timeline_from_docs(all_parsed_docs)
        
        # 5. Update the journey with the new timeline
        journey_update_data = {
            "timeline": generated_timeline,
            "timelineStatus": "GENERATED",
            "status": "IN_PROGRESS" # The journey is now actionable
        }
        db.collection("journeys").document(journey_id).update(journey_update_data)
        
        print(f"Successfully generated and saved timeline for journey {journey_id}.")

    except Exception as e:
        print(f"Error orchestrating timeline for journey {journey_id}: {e}")
        db.collection("journeys").document(journey_id).set({"timelineStatus": "ERROR"}, merge=True)
