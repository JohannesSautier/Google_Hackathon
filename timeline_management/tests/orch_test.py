# test_backend.py (Live Orchestration Test)

import os
import time
import requests
import uuid
import firebase_admin
from firebase_admin import firestore

# --- ⚙️ CONFIGURATION: UPDATE THESE VALUES ---
# Get these URLs from the output of `firebase deploy`
CREATE_JOURNEY_URL = "https://create-journey-w3spnqcwla-ew.a.run.app"
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
    
# --- Main Test Function ---
def test_live_orchestration_flow():
    """
    Tests the full, live, asynchronous flow from journey creation to
    AI-powered timeline generation.
    """
    print("\n🚀 Starting LIVE end-to-end orchestration test...")
    
    journey_id = None
    dummy_files = []

    try:
        # === Step 1: Create a New Journey ===
        print("\n--- Step 1: Creating a new journey ---")
        test_user_id = f"live-test-user-{uuid.uuid4()}"
        journey_data = {
            "userId": test_user_id, "originCountry": "IN",
            "destinationCountry": "DE", "nationality": "IN", "purpose": "EDUCATION"
        }
        response = requests.post(CREATE_JOURNEY_URL, json=journey_data)
        assert response.status_code == 201, f"Create Journey failed with status {response.status_code}"
        journey_id = response.text.split(":")[-1].strip()
        print(f"✔️ Journey created successfully. ID: {journey_id}")

        # === Step 2: Simulate User Uploading All Required Documents ===
        print("\n--- Step 2: Simulating the upload of 4 required documents ---")
        # NOTE: The content of these files does not matter for this test.
        # What matters is that the act of uploading triggers your backend.
        # Your document parsing API will handle the content.
        required_doc_types = ["visa_doc.pdf"]
        
        for doc_name in required_doc_types:
            # Create a small dummy file
            with open(doc_name, "w") as f:
                f.write(f"This is a dummy file for {doc_name}")
            dummy_files.append(doc_name)
            
            # Prepare and send the upload request
            files = {"document": (doc_name, open("infostudents-data.pdf", "rb"), "application/pdf")}
            form_data = {"journeyId": journey_id}
            
            print(f"   > Uploading '{doc_name}'...")
            upload_response = requests.post(UPLOAD_DOCUMENT_URL, files=files, data=form_data)
            assert upload_response.status_code == 200, f"Upload for {doc_name} failed!"
            print(f"   ✔️ '{doc_name}' uploaded.")
            time.sleep(2) # Small delay between uploads

        # === Step 3: Wait for the entire backend process to complete ===
        # This is the most critical part of an async test. We must wait long
        # enough for all functions to trigger and complete.
        # (Upload -> process_document -> parse API -> create_parsed_doc -> orchestrate -> Gemini API)
        wait_time = 45 # seconds
        print(f"\n--- Step 3: Waiting {wait_time} seconds for all background processing to complete... ---")
        time.sleep(wait_time)

        # === Step 4: Verify the Final Result in Firestore ===
        print("\n--- Step 4: Verifying the final state of the journey document ---")
        final_journey_doc_ref = db.collection("journeys").document(journey_id)
        final_journey_doc = final_journey_doc_ref.get()

        assert final_journey_doc.exists, "The journey document was not found after processing!"
        
        final_data = final_journey_doc.to_dict()
        
        # Assertion 1: Check the status flags
        assert final_data.get("timelineStatus") == "GENERATED", \
            f"Expected timelineStatus to be 'GENERATED', but it was '{final_data.get('timelineStatus')}'"
        print("   ✔️ timelineStatus is 'GENERATED'.")

        # Assertion 2: Check that the timeline exists and is not empty
        assert "timeline" in final_data and isinstance(final_data["timeline"], list) and len(final_data["timeline"]) > 0, \
            "The 'timeline' field is missing, not a list, or is empty."
        print(f"   ✔️ Timeline was generated with {len(final_data['timeline'])} steps.")

    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
    except Exception as e:
        print(f"\n❌ AN UNEXPECTED ERROR OCCURRED: {e}")
    else:
        print("\n🎉 All tests passed successfully! The full orchestration pipeline is working.")
    finally:
        # === Cleanup: Remove local dummy files and Firestore documents ===
        print("\n--- Cleaning up ---")
        for file_path in dummy_files:
            if os.path.exists(file_path):
                os.remove(file_path)
                print(f"   > Removed local file: {file_path}")
        
        # You can uncomment these lines to automatically delete test data from Firestore
        # if journey_id:
        #     # In a real CI/CD, you would also query and delete all related
        #     # parsed_documents, data_points, etc.
        #     db.collection("journeys").document(journey_id).delete()
        #     print(f"   > Deleted journey '{journey_id}' from Firestore.")

def run_tests():
    """
    Main function to orchestrate the integration tests.
    """
    print("\n🚀 Starting LIVE end-to-end orchestration test...")
    
    journey_id = None
    dummy_files = []

    try:
        # === Step 1: Create a New Journey ===
        print("\n--- Step 1: Creating a new journey ---")
        test_user_id = f"live-test-user-{uuid.uuid4()}"
        journey_data = {
            "userId": test_user_id, "originCountry": "IN",
            "destinationCountry": "DE", "nationality": "IN", "purpose": "EDUCATION"
        }
        response = requests.post(CREATE_JOURNEY_URL, json=journey_data)
        assert response.status_code == 201, f"Create Journey failed with status {response.status_code}"
        journey_id = response.text.split(":")[-1].strip()
        print(f"✔️ Journey created successfully. ID: {journey_id}")

        # === Step 2: Simulate User Uploading All Required Documents ===
        print("\n--- Step 2: Simulating the upload of 4 required documents ---")
        required_doc_types = ["visa_doc.pdf"]
        
        for doc_name in required_doc_types:
            with open(doc_name, "w") as f:
                f.write(f"This is a dummy file for {doc_name}")
            dummy_files.append(doc_name)
            
            files = {"document": (doc_name, open("infostudents-data.pdf", "rb"), "application/pdf")}
            form_data = {"journeyId": journey_id}
            
            print(f"   > Uploading '{doc_name}'...")
            upload_response = requests.post(UPLOAD_DOCUMENT_URL, files=files, data=form_data)
            assert upload_response.status_code == 200, f"Upload for {doc_name} failed!"
            print(f"   ✔️ '{doc_name}' uploaded.")
            time.sleep(2)

        # === Step 3: Wait for all background processing to complete ===
        wait_time = 45
        print(f"\n--- Step 3: Waiting {wait_time} seconds for all background processing to complete... ---")
        time.sleep(wait_time)

        # === Step 4: Verify the Final Result in Firestore ===
        print("\n--- Step 4: Verifying the final state of the journey document ---")
        final_journey_doc_ref = db.collection("journeys").document(journey_id)
        final_journey_doc = final_journey_doc_ref.get()

        assert final_journey_doc.exists, "The journey document was not found after processing!"
        final_data = final_journey_doc.to_dict()
        
        assert final_data.get("timelineStatus") == "GENERATED", \
            f"Expected timelineStatus to be 'GENERATED', but it was '{final_data.get('timelineStatus')}'"
        print("   ✔️ timelineStatus is 'GENERATED'.")

        assert "timeline" in final_data and isinstance(final_data["timeline"], list) and len(final_data["timeline"]) > 0, \
            "The 'timeline' field is missing, not a list, or is empty."
        print(f"   ✔️ Timeline was generated with {len(final_data['timeline'])} steps.")

    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
    except Exception as e:
        print(f"\n❌ AN UNEXPECTED ERROR OCCURRED: {e}")
    else:
        print("\n🎉 All tests passed successfully! The full orchestration pipeline is working.")
    finally:
        # === Cleanup ===
        print("\n--- Cleaning up ---")
        for file_path in dummy_files:
            if os.path.exists(file_path):
                os.remove(file_path)
                print(f"   > Removed local file: {file_path}")
                
if __name__ == "__main__":
    if "YOUR_CREATE_JOURNEY_URL" in CREATE_JOURNEY_URL:
        print("🛑 Please update the placeholder URLs in the script before running.")
    else:
        run_tests()