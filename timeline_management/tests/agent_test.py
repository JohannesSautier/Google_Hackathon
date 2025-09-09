import firebase_admin
from firebase_admin import firestore
import uuid
import time
import requests
from datetime import datetime, timezone

# --- SETUP ---
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
    
# --- AGENT LOGIC (copied from main.py for isolated testing) ---

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
        
        existing_dps = db.collection("data_points").where("journeyId", "==", journey_id).where("sourceType", "==", "EMAIL_AGENT").stream()
        existing_contents = {dp.to_dict().get("rawContent") for dp in existing_dps}

        api_payload = {"timeline": {step['stepId']: {"start_date": step['estimatedStartDate'], "end_date": step['estimatedEndDate']} for step in timeline}}
        mail_api_url = "https://dream-team-mail-api-958207203523.europe-west1.run.app/analyze-emails"
        
        try:
            response = requests.post(mail_api_url, json=api_payload)
            response.raise_for_status()
            api_response = response.json()
            results = api_response[0].get("results", [])

            new_results_count = 0
            for result in results:
                if result.get("rawContent") not in existing_contents:
                    new_results_count += 1
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

def _run_news_agent_logic(db):
    print("Executing News Agent logic...")
    journeys_query = db.collection("journeys").where("status", "==", "IN_PROGRESS").stream()

    existing_dps = db.collection("data_points").where("sourceType", "==", "NEWS_API").stream()
    existing_uris = {dp.to_dict().get("sourceURI") for dp in existing_dps}

    for journey in journeys_query:
        journey_id = journey.id
        journey_data = journey.to_dict()
        
        print(f"  -> Processing news for journey: {journey_id}")
        
        api_payload = {
            "origin": journey_data.get("originCountry"), "destination": journey_data.get("destinationCountry"),
            "since_days": 7, "max_articles": 20, "use_llm": True
        }
        news_api_url = "https://dream-team-news-api-958207203523.europe-west1.run.app/run"
        
        try:
            response = requests.post(news_api_url, json=api_payload)
            response.raise_for_status()
            data_points = response.json().get("dataPoints", [])

            new_data_points = []
            for dp in data_points:
                if dp.get("sourceURI") not in existing_uris:
                    dp["journeyId"] = journey_id
                    new_data_points.append(dp)
            
            if new_data_points:
                add_new_data_points_and_create_events(db, new_data_points)
                print(f"  -> Found {len(data_points)} articles, added {len(new_data_points)} new data points.")
            else:
                print("  -> Found 0 new articles.")
        except Exception as e:
            print(f"  -> ERROR processing news for journey {journey_id}: {e}")

# --- TEST RUNNER ---

def run_isolated_agent_tests():
    """
    Tests the agent helper functions directly to ensure their internal logic is correct.
    """
    print("\n🚀 Starting ISOLATED test for agent helper functions...")
    
    journey_id = None
    
    try:
        # === Step 1: Create a realistic test journey for the agents to find ===
        print("\n--- Step 1: Creating a test 'IN_PROGRESS' journey in Firestore ---")
        user_id = f"isolated-agent-test-{uuid.uuid4()}"
        
        test_timeline = [
            {"stepId": "VISA_APPLICATION", "estimatedStartDate": "2025-10-01", "estimatedEndDate": "2025-12-01"},
            {"stepId": "INSURANCE", "estimatedStartDate": "2025-09-15", "estimatedEndDate": "2025-09-20"},
        ]

        journey_data = {
            "userId": user_id, "originCountry": "IN", "destinationCountry": "DE",
            "status": "IN_PROGRESS",
            "timeline": test_timeline,
            "createdAt": firestore.SERVER_TIMESTAMP,
        }
        _ , journey_ref = db.collection("journeys").add(journey_data)
        journey_id = journey_ref.id
        print(f"✔️ Test journey created with ID: {journey_id}")

        # === Step 2: Directly call the helper functions ===
        print("\n--- Step 2: Calling agent helper functions directly ---")
        
        print("   > Executing _run_news_agent_logic...")
        _run_news_agent_logic(db)
        print("   > News agent logic finished.")

        print("\n   > Executing _run_mail_agent_logic...")
        _run_mail_agent_logic(db)
        print("   > Mail agent logic finished.")

        # === Step 3: Wait for any asynchronous event creation to settle ===
        wait_time = 10
        print(f"\n--- Step 3: Waiting {wait_time} seconds for Firestore writes to complete... ---")
        time.sleep(wait_time)

        # === Step 4: Verify the results in Firestore ===
        print("\n--- Step 4: Verifying that data points were created ---")
        
        news_query = db.collection("data_points").where("journeyId", "==", journey_id).where("sourceType", "==", "NEWS_API").stream()
        news_points = list(news_query)
        assert len(news_points) > 0, "TEST FAILED: No data points were created by the News Agent."
        print(f"   ✔️ Verified: Found {len(news_points)} data point(s) from the News Agent.")
        
        mail_query = db.collection("data_points").where("journeyId", "==", journey_id).where("sourceType", "==", "EMAIL_AGENT").stream()
        mail_points = list(mail_query)
        assert len(mail_points) > 0, "TEST FAILED: No data points were created by the Mail Agent."
        print(f"   ✔️ Verified: Found {len(mail_points)} data point(s) from the Mail Agent.")

    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
    else:
        print("\n🎉 All isolated agent tests passed successfully!")
    finally:
        # === Cleanup ===
        if journey_id:
            print(f"\n--- Cleaning up test journey '{journey_id}' ---")
            db.collection("journeys").document(journey_id).delete()
            print("   > Test journey deleted.")

if __name__ == "__main__":
    run_isolated_agent_tests()

