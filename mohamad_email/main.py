import os
import json
import base64
import datetime
from fastapi import FastAPI, Request
from pydantic import BaseModel

# Your existing imports
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import google.generativeai as genai

# --- FastAPI App Initialization ---
app = FastAPI()

# --- GCP Cloud Run Environment Variables ---
# Your Gmail token JSON string.
GMAIL_TOKEN_JSON = os.environ.get("GMAIL_TOKEN_JSON", "token.json")
# Your Gemini API key.
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
if not GMAIL_TOKEN_JSON:
    raise ValueError("GMAIL_TOKEN_JSON not found in environment variables.")
# Define the scope for Gmail API
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

# Define the JSON structure for the initial timeline
DEFAULT_TIMELINE = {
    "VISA_APPLICATION": {"start_date": "2025-09-01", "end_date": "2025-09-30"},
    "INSURANCE": {"start_date": "2025-09-08", "end_date": "2025-09-14"},
    "BANKACCOUNT": {"start_date": "2025-09-15", "end_date": "2025-09-21"},
    "PROOFFINANCE": {"start_date": "2025-09-22", "end_date": "2025-09-28"}
}

# Define a Pydantic model for the request body
class TimelineRequest(BaseModel):
    timeline: dict = DEFAULT_TIMELINE

# Your existing helper functions remain the same
def get_email_body(payload):
    """Recursively extracts the plain text body from the email payload."""
    if 'body' in payload and 'data' in payload['body']:
        body_data = payload['body']['data']
        if body_data:
            return base64.urlsafe_b64decode(body_data).decode('utf-8')
    if 'parts' in payload:
        for part in payload['parts']:
            body = get_email_body(part)
            if body:
                return body
    return ""

def analyze_with_gemini(email_content, initial_timeline):
    """
    Sends email content to the Gemini API for analysis and returns the
    structured JSON output.
    """
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY not found in environment variables.")

    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-2.0-flash')

    prompt = f"""
    You are an expert AI assistant for a tool that helps with migration to a new country.
    Your task is to analyze an email related to the migration process and extract relevant information to populate a JSON object.

    The email is from: {email_content.get('sender', 'Unknown')}
    The email subject is: {email_content.get('subject', 'No Subject')}
    The email body is: {email_content.get('body', '')}

    The migration process involves these steps: Visa Application, Insurance, Bank Account, Proof of Finance.

    The current timeline for these stages is:
    {json.dumps(initial_timeline, indent=2)}

    Based on the email content, determine the following:
    1. The 'processType' (e.g., 'VISA_APPLICATION', 'INSURANCE', 'BANKACCOUNT', 'PROOFFINANCE') the email is relevant to.
    2. A brief, raw summary of the content for 'rawContent'.
    3. The 'dataType', which is either 'INFORMATIONAL' (for pure information) or 'PROPOSAL' (if the information can be used to adjust the timeline).
    4. A 'confidenceScore' (from 0.0 to 1.0) on how confident you are in your analysis.
    5. If the dataType is 'PROPOSAL', also provide a 'proposal' object:
       a. The 'targetStepKey' should be the process type (e.g., 'VISA_APPLICATION').
       b. The 'action' should be 'UPDATE_STEP_STATUS'.
       c. The 'payload' should contain 'shiftDays' (negative for moving earlier, positive for moving later), a 'startDate', and an 'endDate'. Calculate 'shiftDays' based on the email's content and the provided timeline. For example, if the email confirms a step is completed 5 days ahead of schedule, 'shiftDays' should be -5.
       d. The 'reason' should be a concise explanation of why the change is proposed.
    
    Output the final result as a single JSON object. Do not include any text before or after the JSON.
    """

    response = model.generate_content(prompt)
    
    try:
        cleaned_response_text = response.text.strip().replace('```json\n', '').replace('```', '')
        return json.loads(cleaned_response_text)
    except json.JSONDecodeError as e:
        print(f"JSONDecodeError: {e}")
        print(f"Raw response from Gemini: {response.text}")
        return None

# The new API endpoint
@app.post("/analyze-emails")
async def analyze_emails_api(request_body: TimelineRequest):
    """
    An API endpoint to trigger email scraping and analysis with a customizable timeline.
    """
    initial_timeline = request_body.timeline

    # A list of keywords related to the migration stages
    relevant_keywords = [
        "visa", "appointment", "biometrics", "embassy", "consulate", "immigration",
        "insurance", "health plan", "coverage", "policy", "premium",
        "bank account", "opening", "deposit", "transfer", "statement",
        "proof of finance", "financial statement", "bank balance", "scholarship", "loan"
    ]
    
    try:
        json_payload = None
        with open(GMAIL_TOKEN_JSON if GMAIL_TOKEN_JSON == "token.json" else "token.json", 'r') as token_file:
            json_payload = json.load(token_file)
        creds = Credentials.from_authorized_user_info(
            json_payload,
            SCOPES
        )
    except (json.JSONDecodeError, TypeError) as e:
        return {"error": f"Error loading credentials: {e}"}, 500

    if not creds.valid and creds.refresh_token:
        try:
            creds.refresh(Request())
        except Exception as e:
            return {"error": f"Error refreshing token: {e}"}, 500

    service = build('gmail', 'v1', credentials=creds)

    try:
        results = service.users().messages().list(userId='me', maxResults=10).execute()
        messages = results.get('messages', [])
        
        if not messages:
            return {"status": "No new messages found."}, 200

        analysis_results = []
        for message in messages:
            msg = service.users().messages().get(userId='me', id=message['id'], format='full').execute()
            
            email_body = get_email_body(msg['payload'])
            subject = next((header['value'] for header in msg['payload']['headers'] if header['name'] == 'Subject'), "No Subject")
            sender = next((header['value'] for header in msg['payload']['headers'] if header['name'] == 'From'), "Unknown Sender")

            email_content_str = (subject + " " + email_body).lower()

            is_relevant = any(keyword in email_content_str for keyword in relevant_keywords)
            
            if not is_relevant:
                continue

            email_to_analyze = {
                'subject': subject,
                'sender': sender,
                'body': email_body
            }

            gemini_output = analyze_with_gemini(email_to_analyze, initial_timeline)
            
            if gemini_output:
                analysis_results.append(gemini_output)

        return {"results": analysis_results, "status": "Email analysis completed successfully."}, 200
        
    except HttpError as error:
        return {"error": f'An HTTP error occurred: {error}'}, 500
    