"""
Test script to verify Google Cloud credentials are working correctly.
Run this after setting up your credentials to make sure everything is configured properly.
"""

import os
import json
from google.cloud import vision
from google.oauth2 import service_account

def test_google_credentials(credentials_path: str):
    """
    Test if Google Cloud credentials are working properly.
    
    Args:
        credentials_path: Path to the Google Cloud service account JSON file
    """
    print("🔍 Testing Google Cloud credentials...")
    print(f"📁 Credentials file: {credentials_path}")
    
    # Check if file exists
    if not os.path.exists(credentials_path):
        print("❌ Error: Credentials file not found!")
        print(f"   Expected location: {credentials_path}")
        return False
    
    # Check if file is valid JSON
    try:
        with open(credentials_path, 'r') as f:
            creds_data = json.load(f)
        print("✅ Credentials file is valid JSON")
    except json.JSONDecodeError as e:
        print(f"❌ Error: Invalid JSON in credentials file: {e}")
        return False
    
    # Check required fields
    required_fields = ['type', 'project_id', 'private_key', 'client_email']
    missing_fields = [field for field in required_fields if field not in creds_data]
    
    if missing_fields:
        print(f"❌ Error: Missing required fields in credentials: {missing_fields}")
        return False
    
    print("✅ All required fields present in credentials")
    print(f"📋 Project ID: {creds_data.get('project_id', 'Unknown')}")
    print(f"📧 Service Account: {creds_data.get('client_email', 'Unknown')}")
    
    # Test Vision API client initialization
    try:
        credentials = service_account.Credentials.from_service_account_file(credentials_path)
        client = vision.ImageAnnotatorClient(credentials=credentials)
        print("✅ Vision API client initialized successfully")
        return True
    except Exception as e:
        print(f"❌ Error initializing Vision API client: {e}")
        print("\n🔧 Troubleshooting tips:")
        print("   1. Make sure Vision API is enabled in your Google Cloud project")
        print("   2. Check that your service account has 'Cloud Vision API User' role")
        print("   3. Verify billing is enabled for your project")
        print("   4. Wait a few minutes if you just enabled the API")
        return False

def main():
    """Main function to run the credential test."""
    print("=" * 60)
    print("🧪 Google Cloud Credentials Test")
    print("=" * 60)
    
    # Default credentials path
    credentials_path = "/home/damian/Desktop/cloud/google-credentials.json"
    
    # Check if user provided a different path
    if len(os.sys.argv) > 1:
        credentials_path = os.sys.argv[1]
    
    success = test_google_credentials(credentials_path)
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 SUCCESS: Your Google Cloud credentials are working!")
        print("   You can now use OCR functionality with your PDF extractor.")
    else:
        print("💥 FAILED: There are issues with your credentials setup.")
        print("   Please follow the setup guide in GOOGLE_CLOUD_SETUP.md")
    print("=" * 60)

if __name__ == "__main__":
    main()
