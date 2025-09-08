"""
Test script to verify Google Cloud default credentials are working.
This is for when you can't use service account keys due to organization policies.
"""

from google.cloud import vision
import subprocess
import sys

def test_default_credentials():
    """
    Test if Google Cloud default credentials are working properly.
    """
    print("🔍 Testing Google Cloud default credentials...")
    
    try:
        # Try to initialize Vision API client with default credentials
        client = vision.ImageAnnotatorClient()
        print("✅ Vision API client initialized successfully with default credentials")
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def check_gcloud_auth():
    """
    Check if user is authenticated with gcloud.
    """
    try:
        result = subprocess.run(['gcloud', 'auth', 'list'], 
                              capture_output=True, text=True, check=True)
        
        if "ACTIVE" in result.stdout:
            print("✅ gcloud authentication found")
            return True
        else:
            print("❌ No active gcloud authentication found")
            return False
    except subprocess.CalledProcessError:
        print("❌ gcloud command not found or failed")
        return False
    except FileNotFoundError:
        print("❌ gcloud CLI not installed")
        return False

def check_application_default_credentials():
    """
    Check if application default credentials are set.
    """
    try:
        result = subprocess.run(['gcloud', 'auth', 'application-default', 'print-access-token'], 
                              capture_output=True, text=True, check=True)
        
        if result.stdout.strip():
            print("✅ Application default credentials are set")
            return True
        else:
            print("❌ Application default credentials not set")
            return False
    except subprocess.CalledProcessError:
        print("❌ Application default credentials not set")
        return False

def main():
    """Main function to run the credential test."""
    print("=" * 60)
    print("🧪 Google Cloud Default Credentials Test")
    print("=" * 60)
    
    # Check gcloud authentication
    gcloud_auth = check_gcloud_auth()
    
    # Check application default credentials
    app_default_creds = check_application_default_credentials()
    
    # Test Vision API
    vision_api_works = test_default_credentials()
    
    print("\n" + "=" * 60)
    
    if vision_api_works:
        print("🎉 SUCCESS: Your Google Cloud credentials are working!")
        print("   You can now use OCR functionality with your PDF extractor.")
    else:
        print("💥 FAILED: There are issues with your credentials setup.")
        print("\n🔧 To fix this, run these commands:")
        
        if not gcloud_auth:
            print("   1. gcloud auth login")
        
        if not app_default_creds:
            print("   2. gcloud auth application-default login")
        
        print("   3. gcloud config set project YOUR_PROJECT_ID")
        print("   4. gcloud services enable vision.googleapis.com")
        
        print("\n📖 See ALTERNATIVE_AUTH_SETUP.md for detailed instructions")
    
    print("=" * 60)

if __name__ == "__main__":
    main()
