# live_scenario_test.py
import os
import time
import requests
import uuid
import firebase_admin
from firebase_admin import firestore

# --- ⚙️ CONFIGURATION: UPDATE THESE VALUES ---
CREATE_JOURNEY_URL = "https://create-journey-w3spnqcwla-ew.a.run.app"
GET_JOURNEY_URL = "https://get-journey-w3spnqcwla-ew.a.run.app"
ADD_AGENT_FINDING_URL = "https://add-agent-finding-w3spnqcwla-ew.a.run.app"
UPLOAD_DOCUMENT_URL = "https://upload-document-w3spnqcwla-ew.a.run.app"
GET_DATA_POINTS_URL = "https://europe-west1-tum-cdtm25mun-8742.cloudfunctions.net/get_data_points"


# --- Firebase Admin SDK Initialization (for verification only) ---
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
    

# --- Main Test Function ---
def run_live_student_scenario():
    """
    Creates a journey and simulates document uploads VIA LIVE API ENDPOINTS
    to trigger the full, real-time orchestration pipeline.
    """
    print("\n🚀 Starting LIVE end-to-end student scenario for India -> Germany (TUM)...")
    
    journey_id = None
    dummy_files = []

    try:
        # === Step 1: Create the student's journey via the API ===
        print("\n--- Step 1: Calling /create_journey endpoint ---")
        user_id = f"live-student-{uuid.uuid4()}"
        journey_data = {
            "userId": user_id, "originCountry": "IN", "destinationCountry": "DE",
            "nationality": "IN", "purpose": "EDUCATION",
            "destinationEntity": "Technical University of Munich (TUM)"
        }
        response = requests.post(CREATE_JOURNEY_URL, json=journey_data)
        response.raise_for_status() # Will stop the test if the API call fails
        journey_id = response.text.split(":")[-1].strip()
        print(f"✔️ Journey created successfully via API. ID: {journey_id}")

        # === Step 2: Simulate the user uploading 4 documents via the API ===
        print("\n--- Step 2: Calling /upload_document endpoint for each document ---")
        # NOTE: The content of these files does not matter for the test itself.
        # Your live document parsing API is responsible for processing them.
        # This test just confirms that our upload mechanism triggers the flow.

        # Create a small dummy file to upload
        doc_name = "MasterData (1).pdf"
        
        # Prepare and send the multipart/form-data request to the upload endpoint
        files = {"document": (doc_name, open(doc_name, "rb"), "application/pdf")}
        form_data = {"journeyId": journey_id}
        
        print(f"   > Uploading '{doc_name}'...")
        upload_response = requests.post(UPLOAD_DOCUMENT_URL, files=files, data=form_data)
        upload_response.raise_for_status()
        print(f"   ✔️ '{doc_name}' uploaded successfully.")
        time.sleep(2)

        # === Step 3: Wait for the full backend pipeline to complete ===
        wait_time = 60 # Using a safe wait time for 4 live API calls + Gemini
        print(f"\n--- Step 3: Waiting {wait_time} seconds for all background processing... ---")
        time.sleep(wait_time)

        # === Step 4: Verify the final, AI-generated timeline in Firestore ===
        print("\n--- Step 4: Verifying the final journey state in Firestore ---")
        final_journey_doc_ref = db.collection("journeys").document(journey_id)
        final_journey_doc = final_journey_doc_ref.get()

        assert final_journey_doc.exists, "The journey document was not found after processing!"
        final_data = final_journey_doc.to_dict()
        
        assert final_data.get("timelineStatus") == "GENERATED", \
            f"Expected timelineStatus to be 'GENERATED', but it was '{final_data.get('timelineStatus')}'"
        
        timeline = final_data.get("timeline")
        assert timeline and len(timeline) > 0, "The timeline was not generated or is empty."
        
        print("\n🎉 SCENARIO SUCCEEDED! 🎉")
        print("The live, AI-Generated timeline is now in your Firestore database.")
        print("--------------------------------------------------")
        for step in timeline:
            start = step.get('estimatedStartDate', 'N/A').split('T')[0]
            end = step.get('estimatedEndDate', 'N/A').split('T')[0]
            print(f"  - {step.get('title')} ({start} to {end})")
        print("--------------------------------------------------")

    except Exception as e:
        print(f"\n❌ SCENARIO FAILED: {e}")

if __name__ == "__main__":
    if "YOUR_CREATE_JOURNEY_URL" in CREATE_JOURNEY_URL:
        print("🛑 Please update the placeholder URLs in the script before running.")
    else:
        run_live_student_scenario()