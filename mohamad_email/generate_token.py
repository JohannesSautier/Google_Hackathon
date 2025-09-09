import os
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
import json

# The scope for the Gmail API.
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
# The file to store the user's access and refresh tokens.
TOKEN_JSON_PATH = 'token.json'
# The file downloaded from Google Cloud Console containing OAuth 2.0 client ID.
CLIENT_SECRETS_FILE = 'credentials.json'

def generate_token():
    """
    Generates a token.json file for Gmail API access.
    This function will open a browser window for user authorization.
    """
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first time.
    if os.path.exists(TOKEN_JSON_PATH):
        print(f"'{TOKEN_JSON_PATH}' already exists. If you want to re-authenticate, please delete it first.")
        return

    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(CLIENT_SECRETS_FILE):
                print(f"Error: '{CLIENT_SECRETS_FILE}' not found.")
                print("Please download it from the Google Cloud Console and place it in the same directory.")
                return
            
            flow = InstalledAppFlow.from_client_secrets_file(
                CLIENT_SECRETS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        
        # Save the credentials for the next run
        with open(TOKEN_JSON_PATH, 'w') as token:
            token.write(creds.to_json())
        
        print(f"\nAuthorization successful. Credentials saved to '{TOKEN_JSON_PATH}'.")
        print("\nYou can now copy the contents of this file and set it as your GMAIL_TOKEN_JSON environment variable.")

if __name__ == '__main__':
    generate_token()
