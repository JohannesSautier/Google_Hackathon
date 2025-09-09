import firebase_admin
from firebase_admin import firestore
from firebase_functions import https_fn, options, firestore_fn
from datetime import datetime, timedelta, timezone
import json 
from firebase_admin import storage
from firebase_functions import storage_fn
import requests
from io import BytesIO
from firebase_admin import storage
from google.cloud import aiplatform
import vertexai
from vertexai.generative_models import GenerativeModel, Part
from firebase_functions import pubsub_fn


# We will move our data classes to a separate file for better organization
# from models import ProcessStep, AgentFinding, JourneyEvent 

# --- App Initialization ---
options.set_global_options(region="europe-west1")

# --- Helpers --- 
def _run_mail_agent_logic(db):
    print("Executing Mail Agent logic...")
    journeys_query = db.collection("journeys").where("status", "==", "IN_PROGRESS").stream()
    
    for journey in journeys_query:
        journey_id = journey.id
        journey_data = journey.to_dict()
        timeline = journey_data.get("timeline", [])
        
        if not timeline:
            continue

        print(f"  -> Processing mail for journey: {journey_id}")
        
        # 1. De-duplication: Fetch existing email content to avoid reprocessing
        existing_dps = db.collection("data_points").where("journeyId", "==", journey_id).where("sourceType", "==", "EMAIL_AGENT").stream()
        existing_contents = {dp.to_dict().get("rawContent") for dp in existing_dps}

        # 2. Prepare and call the external Mail API
        api_payload = {"timeline": {step['stepId']: {"start_date": step['estimatedStartDate'], "end_date": step['estimatedEndDate']} for step in timeline}}
        mail_api_url = "https://dream-team-mail-api-958207203523.europe-west1.run.app/analyze-emails"
        
        try:
            response = requests.post(mail_api_url, json=api_payload)
            response.raise_for_status()
            api_response = response.json()
            
            # The API returns a list with the results object at index 0
            results = api_response[0].get("results", [])

            # 3. Process new results
            new_results_count = 0
            for result in results:
                if result.get("rawContent") not in existing_contents:
                    new_results_count += 1
                    # Add sourceType and journeyId to the result to form a complete dataPoint
                    result_as_datapoint = {**result, "sourceType": "EMAIL_AGENT", "journeyId": journey_id}
                    
                    dp_ref = db.collection("data_points").document()
                    dp_ref.set(result_as_datapoint)
                    
                    event_data = {
                        "journeyId": journey_id, "dataPointId": dp_ref.id,
                        "status": "PENDING", "createdAt": datetime.now(timezone.utc).isoformat()
                    }
                    db.collection("journey_events").add(event_data)
            print(f"  -> Found {len(results)} results, added {new_results_count} new data points.")
        except Exception as e:
            print(f"  -> ERROR processing mail for journey {journey_id}: {e}")

def add_new_data_points_and_create_events(db, data_points):
    """Helper to save data points and create their processing events."""
    for data_point in data_points:
        dp_ref = db.collection("data_points").document()
        dp_ref.set(data_point)
        event_data = {
            "journeyId": data_point.get("journeyId"), "dataPointId": dp_ref.id,
            "status": "PENDING", "createdAt": datetime.now(timezone.utc).isoformat()
        }
        db.collection("journey_events").add(event_data)

            
# --- Helper Logic for the News Agent ---
def _run_news_agent_logic(db):
    print("Executing News Agent logic...")
    journeys_query = db.collection("journeys").where("status", "==", "IN_PROGRESS").stream()

    # 1. De-duplication: Fetch all existing news source URIs to avoid reprocessing
    existing_dps = db.collection("data_points").where("sourceType", "==", "NEWS_API").stream()
    existing_uris = {dp.to_dict().get("sourceURI") for dp in existing_dps}

    for journey in journeys_query:
        journey_id = journey.id
        journey_data = journey.to_dict()
        
        print(f"  -> Processing news for journey: {journey_id}")
        
        # 2. Prepare and call the external News API
        api_payload = {
            "origin": journey_data.get("originCountry"),
            "destination": journey_data.get("destinationCountry"),
            "since_days": 7, "max_articles": 20, "use_llm": True
        }
        news_api_url = "https://dream-team-news-api-958207203523.europe-west1.run.app/run" # Using a placeholder for your live URL
        
        try:
            response = requests.post(news_api_url, json=api_payload)
            response.raise_for_status()
            data_points = response.json().get("dataPoints", [])

            # 3. Filter out duplicates and add journeyId
            new_data_points = []
            for dp in data_points:
                if dp.get("sourceURI") not in existing_uris:
                    dp["journeyId"] = journey_id
                    new_data_points.append(dp)
            
            # 4. Proxy the new data points to our own /add_agent_finding endpoint
            if new_data_points:
                # We can call our own function directly for efficiency instead of a full HTTP request.
                add_new_data_points_and_create_events(db, new_data_points)
                print(f"  -> Found {len(data_points)} articles, added {len(new_data_points)} new data points.")
            else:
                print("  -> Found 0 new articles.")
        except Exception as e:
            print(f"  -> ERROR processing news for journey {journey_id}: {e}")


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


# --- Background Function: Process Document (Live API Call) ---
@storage_fn.on_object_finalized(memory=options.MemoryOption.GB_1) 
def process_document(event: storage_fn.CloudEvent) -> None:
    """
    Triggers on file upload, downloads the file, and sends it to the
    external document parsing API.
    """
    if not firebase_admin._apps:
        firebase_admin.initialize_app()
    db = firestore.client()

    bucket_name = event.data.bucket
    file_path = event.data.name
    
    if not file_path.startswith("user_documents/"):
        return

    print(f"Processing new document: gs://{bucket_name}/{file_path}")
    try:
        parts = file_path.split("/")
        journey_id = parts[1]
        
        # 1. Download the file content from Cloud Storage into memory
        bucket = storage.bucket(bucket_name)
        blob = bucket.blob(file_path)
        file_bytes = blob.download_as_bytes()
        file_in_memory = BytesIO(file_bytes)

        # 2. Call your external Document Parsing API
        doc_api_url = "https://dream-team-doc-api-958207203523.europe-west1.run.app/process-document/"
        source_uri = f"gs://{bucket_name}/{file_path}"
        
        files = {'file': (file_path.split('/')[-1], file_in_memory, 'application/octet-stream')}
        data = {'source_uri': source_uri}
        
        print(f"Calling Document Parsing API for {source_uri}...")
        response = requests.post(doc_api_url, files=files, data=data)
        response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)
        
        # 3. Get the JSON response and enrich it
        parsed_metadata = response.json()
        parsed_metadata["journeyId"] = journey_id
        parsed_metadata["processedAt"] = firestore.SERVER_TIMESTAMP
        
        # 4. Save the live response to Firestore
        db.collection("parsed_documents").add(parsed_metadata)
        print(f"Successfully saved parsed metadata for journey '{journey_id}' from live API.")

    except Exception as e:
        print(f"Error processing document {file_path}: {e}")
        
# --- Helper Function: Live Gemini Call for Timeline Generation ---
def _generate_timeline_from_docs(docs: list) -> list:
    """
    Takes a list of relevant parsed documents, constructs a prompt,
    and calls the Gemini API to generate a structured timeline.
    """
    print("Calling live Gemini API to generate timeline...")
    
    # Initialize Vertex AI - ensure your region is correct
    vertexai.init(project="tum-cdtm25mun-8742", location="europe-west1")
    model = GenerativeModel("gemini-2.5-flash")

    # 1. Filter for only relevant documents, as you requested
    required_processes = {"VISA_APPLICATION", "INSURANCE", "PROOFFINANCE", "BANKACCOUNT"}
    relevant_docs_content = []
    for doc in docs:
        is_relevant = False
        for timeline_info in doc.get("extractedTimelines", []):
            process_type = timeline_info.get("processType")
            if process_type in required_processes:
                is_relevant = True
                break
        if is_relevant:
            relevant_docs_content.append(json.dumps(doc))

    # 2. Construct the prompt for Gemini
    prompt = f"""
    You are an expert immigration logistics planner. Your task is to create a detailed, step-by-step timeline for a student's immigration process based on the provided JSON data extracted from their documents.

    CONTEXT:
    - The student is preparing to study in Germany.
    - Today's date is {datetime.now(timezone.utc).date().isoformat()}.
    - You must create a logical sequence of events, estimate start and end dates, and identify dependencies between steps.

    INPUT DATA FROM PARSED DOCUMENTS:
    ```json
    {json.dumps(relevant_docs_content, indent=2)}
    ```

    TASK:
    Generate a JSON array of timeline events. Each event must be an object with the following keys: "stepId", "title", "description", "status", "estimatedStartDate", "estimatedEndDate", "dependencies".
    - "stepId" must be a unique, uppercase_snake_case string.
    - "status" must be "NOT_STARTED".
    - Dates must be in 'YYYY-MM-DDTHH:MM:SS' ISO 8601 format.
    - "dependencies" must be an array of "stepId"s that this step depends on.
    - Base your timeline ONLY on the information provided in the input data.
    - Do not output any text other than the JSON array itself.
    """
    
    # 3. Call the Gemini API and parse the response
    response = model.generate_content(prompt)
    
    # Clean up the response to ensure it's valid JSON
    json_string = response.text.replace("```json", "").replace("```", "").strip()
    generated_timeline = json.loads(json_string)
    
    return generated_timeline


# --- Background Function 4: Timeline Orchestrator (More Flexible) ---
@firestore_fn.on_document_created(document="parsed_documents/{docId}")
def orchestrate_timeline_generation(event: firestore_fn.Event[firestore_fn.Change]) -> None:
    """
    Triggered when new parsed document metadata is created. Checks if enough
    information exists to generate a timeline, and if so, triggers the process.
    This version uses a map to handle variations in processType names.
    """
    # This map translates various possible LLM outputs into our canonical process names.
    # You can easily add more variations here as you discover them.
    PROCESS_MAP = {
        # Potential API Output -> Our App's Standard Name
        "VISA_APPLICATION": "VISA_APPLICATION",
        "INSURANCE": "INSURANCE",
        "TRAVEL_HEALTH_INSURANCE": "INSURANCE",
        "PROOF_OF_FINANCE": "PROOF_OF_FINANCE",
        "BANKACCOUNT": "BANKACCOUNT",
        "BLOCKED_ACCOUNT_RULES": "BANKACCOUNT",
    }
    
    # These are our app's standard names. The check is against these.
    required_processes = {"VISA_APPLICATION", "INSURANCE", "PROOF_OF_FINANCE", "BANKACCOUNT"}
    
    if not firebase_admin._apps:
        firebase_admin.initialize_app()
    db = firestore.client()

    parsed_doc_data = event.data.to_dict()
    journey_id = parsed_doc_data.get("journeyId")

    if not journey_id:
        return

    try:
        docs_query = db.collection("parsed_documents").where("journeyId", "==", journey_id).stream()
        all_parsed_docs = [doc.to_dict() for doc in docs_query]
        
        found_processes = set()
        
        # --- NEW FLEXIBLE LOGIC ---
        for doc in all_parsed_docs:
            for timeline_info in doc.get("extractedTimelines", []):
                api_process_type = timeline_info.get("processType") or timeline_info.get("timelineKey")
                if api_process_type:
                    # Look up the canonical name in our map
                    canonical_name = PROCESS_MAP.get(api_process_type)
                    if canonical_name:
                        found_processes.add(canonical_name)
        
        print(f"Journey {journey_id}: Found canonical processes: {found_processes}")

        # if not required_processes.issubset(found_processes):
        #     print(f"Still waiting for all required documents. Need {required_processes - found_processes}.")
        #     db.collection("journeys").document(journey_id).set({"timelineStatus": "AWAITING_DOCUMENTS"}, merge=True)
        #     return
        
        print("All required document types found! Proceeding to generate timeline.")
        
        generated_timeline = _generate_timeline_from_docs(all_parsed_docs)
        
        journey_update_data = {
            "timeline": generated_timeline, "timelineStatus": "GENERATED", "status": "IN_PROGRESS"
        }
        db.collection("journeys").document(journey_id).update(journey_update_data)
        
        print(f"Successfully generated and saved timeline for journey {journey_id}.")

    except Exception as e:
        print(f"Error orchestrating timeline for journey {journey_id}: {e}")
        db.collection("journeys").document(journey_id).set({"timelineStatus": "ERROR"}, merge=True)

@https_fn.on_request()
def get_data_points(req: https_fn.Request) -> https_fn.Response:
    """
    HTTP endpoint to retrieve historical data points for a given journey.
    Accepts a required 'journeyId' and an optional 'sourceType' query parameter.
    """
    def json_converter(o):
        if isinstance(o, datetime):
            return o.isoformat()
        raise TypeError(f"Object of type {o.__class__.__name__} is not JSON serializable")

    if not firebase_admin._apps:
        firebase_admin.initialize_app()
    db = firestore.client()
    
    if req.method != "GET":
        return https_fn.Response("Method Not Allowed", status=405)
        
    # --- Parameter Handling ---
    journey_id = req.args.get("journeyId")
    source_type = req.args.get("sourceType") # This will be None if not provided

    if not journey_id:
        return https_fn.Response("Missing required 'journeyId' query parameter.", status=400)
        
    try:
        # --- Dynamic Query Building ---
        # Start with the base query
        query = db.collection("data_points").where("journeyId", "==", journey_id)
        
        # If sourceType is provided, add it to the query
        if source_type:
            print(f"Filtering by sourceType: {source_type}")
            query = query.where("sourceType", "==", source_type)
        
        # Execute the query
        docs = query.stream()
        results = [doc.to_dict() for doc in docs]

        response_body = json.dumps(results, default=json_converter)
        
        return https_fn.Response(
            response_body,
            status=200,
            headers={"Content-Type": "application/json"}
        )
    except Exception as e:
        print(f"Error getting data points: {e}")
        return https_fn.Response("An internal error occurred.", status=500)
    
# --- Main Cron Job Entry Point ---
@pubsub_fn.on_message_published(topic="agent-triggers") # <-- THE FIX IS HERE
def run_scheduled_agent(event: pubsub_fn.CloudEvent) -> None:
    """
    Receives a message from Cloud Scheduler and runs the specified agent logic.
    """
    if not firebase_admin._apps:
        firebase_admin.initialize_app()
    db = firestore.client()

    try:
        # Decode the message from Pub/Sub
        message_data = json.loads(event.data.message.data.decode("utf-8"))
        agent_type = message_data.get("agent_type")
        print(f"Received trigger for agent type: {agent_type}")
        
        if agent_type == "MAIL":
            _run_mail_agent_logic(db)
        elif agent_type == "NEWS":
            _run_news_agent_logic(db)
        else:
            print(f"Unknown agent type: {agent_type}")
            
    except Exception as e:
        print(f"Error in scheduled agent runner: {e}")