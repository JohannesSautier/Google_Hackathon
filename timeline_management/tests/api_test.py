# test_backend.py (Updated for ADC)

import time
import requests
import uuid
import firebase_admin
from firebase_admin import firestore
from datetime import datetime, timedelta, timezone
import os

# --- ⚙️ CONFIGURATION: UPDATE THESE VALUES ---

# Get these URLs from the output of `firebase deploy`
CREATE_JOURNEY_URL = "https://create-journey-w3spnqcwla-ew.a.run.app"
GET_JOURNEY_URL = "https://get-journey-w3spnqcwla-ew.a.run.app"
ADD_AGENT_FINDING_URL = "https://add-agent-finding-w3spnqcwla-ew.a.run.app"
UPLOAD_DOCUMENT_URL = "https://upload-document-w3spnqcwla-ew.a.run.app"

# --- Firebase Admin SDK Initialization (using ADC) ---
try:
    # With ADC, you don't need to provide a credential file.
    # The library finds the credentials set by the `gcloud` command.
    firebase_admin.initialize_app(options={"projectId": "tum-cdtm25mun-8742"}    )
    db = firestore.client()
    print("✅ Firebase Admin SDK initialized successfully using Application Default Credentials.")
except Exception as e:
    print(f"❌ ERROR: Could not initialize Firebase Admin SDK.")
    print(f"   Have you run 'gcloud auth application-default login'?")
    print(f"   Error details: {e}")
    exit()
    
# --- Add this new function to your test script ---
def test_document_upload_and_processing(journey_id):
    """Tests the file upload and the subsequent background processing."""
    print("\n--- Testing: Document Upload & Background Processing ---")

    # Step 4a: Create a dummy file to upload
    dummy_filename = "test_document.txt"
    with open(dummy_filename, "w") as f:
        f.write("This is the content of our test document for the visa application.")
    
    # Step 4b: Prepare the multipart/form-data request
    files = {"document": (dummy_filename, open(dummy_filename, "rb"), "text/plain")}
    form_data = {"journeyId": journey_id}
    
    print(f"   > Uploading '{dummy_filename}' for journey '{journey_id}'...")
    response = requests.post(UPLOAD_DOCUMENT_URL, files=files, data=form_data)
    
    assert response.status_code == 200, f"Expected status 200, but got {response.status_code}"
    print("   > File uploaded successfully via HTTP endpoint.")

    # Step 4c: Wait for the background function to process the file
    print("   > Waiting 20 seconds for storage trigger and processing...")
    time.sleep(20)

    # Step 4d: Verify that the parsed metadata was created in Firestore
    print("   > Verifying parsed metadata in Firestore...")
    docs_query = db.collection("parsed_documents").where("journeyId", "==", journey_id).limit(1).stream()
    
    found_docs = list(docs_query)
    assert len(found_docs) > 0, "No parsed document metadata was found in Firestore!"
    
    parsed_doc = found_docs[0].to_dict()
    assert parsed_doc["documentType"] == "OFFICIAL_VISA_GUIDE"
    assert len(parsed_doc["extractedTimelines"]) == 2
    
    print("✔️ Document processing flow PASSED. Metadata created successfully.")
    
def test_timeline_orchestration():
    """
    Tests the full asynchronous flow:
    1. Create a journey (it will have no timeline).
    2. Add some, but not all, required parsed documents.
    3. Verify the journey enters a 'AWAITING_DOCUMENTS' state.
    4. Add the final required document.
    5. Verify the timeline is generated and added to the journey.
    """
    print("\n--- Testing: Full Timeline Orchestration Flow ---")
    
    # === Step 1: Create a fresh journey for the test ===
    test_user_id = f"orchestration-user-{uuid.uuid4()}"
    journey_data = {"userId": test_user_id, "originCountry": "IN", "destinationCountry": "DE", "nationality": "IN", "purpose": "EDUCATION"}
    response = requests.post(CREATE_JOURNEY_URL, json=journey_data)
    assert response.status_code == 201
    journey_id = response.text.split(":")[-1].strip()
    print(f"   > Created new journey with ID: {journey_id}")

    # === Step 2: Simulate arrival of INCOMPLETE documents (Latent State) ===
    print("   > Simulating arrival of 3 of 4 required document types...")
    docs_to_add = [
        {"journeyId": journey_id, "extractedTimelines": [{"processType": "VISA_APPLICATION"}]},
        {"journeyId": journey_id, "extractedTimelines": [{"processType": "INSURANCE"}]},
        {"journeyId": journey_id, "extractedTimelines": [{"processType": "PROOFFINANCE"}]},
    ]
    for doc in docs_to_add:
        db.collection("parsed_documents").add(doc)
    
    print("   > Waiting 15 seconds for latent state processing...")
    time.sleep(15)

    # === Step 3: Verify the journey is in the AWAITING state ===
    journey_doc = db.collection("journeys").document(journey_id).get().to_dict()
    assert journey_doc.get("timelineStatus") == "AWAITING_DOCUMENTS"
    assert "timeline" not in journey_doc or not journey_doc.get("timeline")
    print("   > ✔️ Verified: Journey is correctly in AWAITING_DOCUMENTS state.")

    # === Step 4: Simulate arrival of the FINAL document (Trigger Gemini State) ===
    print("   > Simulating arrival of final document type (BANKACCOUNT)...")
    final_doc = {"journeyId": journey_id, "extractedTimelines": [{"processType": "BANKACCOUNT"}]}
    db.collection("parsed_documents").add(final_doc)
    
    print("   > Waiting 20 seconds for timeline generation...")
    time.sleep(20)

    # === Step 5: Verify the timeline has been generated ===
    final_journey_doc = db.collection("journeys").document(journey_id).get().to_dict()
    assert final_journey_doc.get("timelineStatus") == "GENERATED"
    assert "timeline" in final_journey_doc and len(final_journey_doc["timeline"]) > 0
    # Check for a specific step from our mock Gemini output
    assert any(step["stepId"] == "VISA_APPLICATION_SUBMIT" for step in final_journey_doc["timeline"])
    print("   > ✔️ Verified: Timeline was successfully generated and added to the journey.")
    print("✔️ Timeline Orchestration Flow PASSED.")

# --- Test Script ---


def run_tests_old():
    """Main function to orchestrate the integration tests."""
    print("\n🚀 Starting backend integration tests...")
    
    test_user_id = f"test-user-{uuid.uuid4()}"
    journey_id = None
    
    try:
        # === Test 1: Create a Journey ===
        print("\n--- Testing: POST /create_journey ---")
        journey_data = {
            "userId": test_user_id,
            "originCountry": "IN",
            "destinationCountry": "DE",
            "nationality": "IN",
            "purpose": "EDUCATION"
        }
        response = requests.post(CREATE_JOURNEY_URL, json=journey_data)
        
        assert response.status_code == 201, f"Expected status 201, but got {response.status_code}"
        journey_id = response.text.split(":")[-1].strip()
        print(f"✔️ create_journey PASSED. New journey ID: {journey_id}")

        # === Test 2: Get the Journey ===
        print(f"\n--- Testing: GET /get_journey?id={journey_id} ---")
        response = requests.get(f"{GET_JOURNEY_URL}?id={journey_id}")
        
        assert response.status_code == 200, f"Expected status 200, but got {response.status_code}"
        retrieved_data = response.json()
        assert retrieved_data["userId"] == test_user_id, "User ID does not match."
        print("✔️ get_journey PASSED. Retrieved data matches.")

        # === Test 3: Data Point Flow (Replaces Agent Finding Test) ===
        print("\n--- Testing: Data Point & Background Processing ---")

        # Step 3a: Set up initial timeline with an ISO 8601 date string
        print("   > Setting up initial timeline in Firestore...")
        initial_end_date = "2025-11-30T00:00:00"
        initial_timeline = [{
            "stepId": "visa_application",
            "estimatedEndDate": initial_end_date,
        }]
        db.collection("journeys").document(journey_id).update({"timeline": initial_timeline})
        print("   > Initial timeline set.")

        # Step 3b: Submit a Data Point with a proposal to shift the date
        print("   > Submitting data point via POST /add_agent_finding...")
        data_point_payload = {
            "dataPoints": [
                {
                    "journeyId": journey_id,
                    "dataType": "PROPOSAL",
                    "sourceType": "TEST_AGENT",
                    "sourceURI": "https://test.com/new-visa-rules",
                    "retrievedAt": "2025-09-08T21:00:00Z",
                    "rawContent": "A new law accelerates visa processing.",
                    "confidenceScore": 0.9,
                    "proposal": {
                        "targetStepKey": "visa_application",
                        "action": "UPDATE_STEP_STATUS",
                        "payload": {
                            "shiftDays": -10  # Proposing to finish 10 days earlier
                        },
                        "reason": "New accelerated processing law."
                    }
                }
            ]
        }
        response = requests.post(ADD_AGENT_FINDING_URL, json=data_point_payload)
        assert response.status_code == 202, f"Expected status 202, but got {response.status_code}"
        print("   > Data point submitted successfully.")

        # Step 3c: Wait for the background function
        print("   > Waiting 15 seconds for background function to execute...")
        time.sleep(15)

        # Step 3d: Verify the change in Firestore
        print("   > Verifying timeline update in Firestore...")
        updated_journey_doc = db.collection("journeys").document(journey_id).get()
        updated_timeline = updated_journey_doc.to_dict()["timeline"]
        visa_step = updated_timeline[0]

        # Calculate the expected new date
        expected_date = datetime.fromisoformat(initial_end_date) + timedelta(days=-10)
        expected_date_str = expected_date.isoformat()

        assert visa_step["estimatedEndDate"] == expected_date_str, \
            f"Timeline was not shifted correctly! Expected '{expected_date_str}', but found '{visa_step['estimatedEndDate']}'"

        print("✔️ Data point flow PASSED. Timeline was shifted correctly.")
        
        # === Test 4: Document Flow ===
        # We re-use the journey_id created in the first test
        if journey_id:
            test_document_upload_and_processing(journey_id)

    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
    except Exception as e:
        print(f"\n❌ AN UNEXPECTED ERROR OCCURRED: {e}")
    else:
        print("\n🎉 All tests passed successfully!")

# --- Main run_tests function ---
def run_tests():
    """Main function to orchestrate the integration tests."""
    print("\n🚀 Starting backend integration tests...")
    try:
        # We will run our new self-contained test
        test_timeline_orchestration()

    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
    except Exception as e:
        print(f"\n❌ AN UNEXPECTED ERROR OCCURRED: {e}")
    else:
        print("\n🎉 All tests passed successfully!")
        
if __name__ == "__main__":
    if "YOUR_CREATE_JOURNEY_URL" in CREATE_JOURNEY_URL:
        print("🛑 Please update the placeholder URLs in the script before running.")
    else:
        run_tests()