"""
Debug script to test PDF extraction and identify any issues
"""

import sys
import os

def test_imports():
    """Test if all required modules can be imported"""
    print("🔍 Testing imports...")
    
    try:
        import fitz
        print("✅ PyMuPDF (fitz) imported successfully")
    except ImportError as e:
        print(f"❌ PyMuPDF import failed: {e}")
        return False
    
    try:
        from google.cloud import vision
        print("✅ Google Cloud Vision imported successfully")
    except ImportError as e:
        print(f"❌ Google Cloud Vision import failed: {e}")
        return False
    
    try:
        from pdf_text_extractor import extract_pdf_text
        print("✅ pdf_text_extractor imported successfully")
    except ImportError as e:
        print(f"❌ pdf_text_extractor import failed: {e}")
        return False
    
    return True

def test_credentials():
    """Test Google Cloud credentials"""
    print("\n🔍 Testing Google Cloud credentials...")
    
    try:
        from google.cloud import vision
        client = vision.ImageAnnotatorClient()
        print("✅ Google Vision API client created successfully")
        return True
    except Exception as e:
        print(f"❌ Google Vision API client creation failed: {e}")
        return False

def test_pdf_extraction():
    """Test PDF text extraction"""
    print("\n🔍 Testing PDF text extraction...")
    
    try:
        from pdf_text_extractor import extract_pdf_text
        
        # Test with a simple PDF
        pdf_path = "/home/damian/Desktop/cloud/immigration-service/documents IN - DE/infostudents-data.pdf"
        
        if not os.path.exists(pdf_path):
            print(f"❌ PDF file not found: {pdf_path}")
            return False
        
        print(f"📁 Testing with: {pdf_path}")
        text = extract_pdf_text(pdf_path)
        print(f"✅ Successfully extracted {len(text)} characters")
        return True
        
    except Exception as e:
        print(f"❌ PDF extraction failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main debug function"""
    print("=" * 60)
    print("🧪 PDF Text Extractor Debug Test")
    print("=" * 60)
    
    print(f"Python version: {sys.version}")
    print(f"Python executable: {sys.executable}")
    print(f"Current directory: {os.getcwd()}")
    
    # Test imports
    if not test_imports():
        print("\n💥 Import test failed - check your dependencies")
        return
    
    # Test credentials
    if not test_credentials():
        print("\n💥 Credentials test failed - check your Google Cloud setup")
        return
    
    # Test PDF extraction
    if not test_pdf_extraction():
        print("\n💥 PDF extraction test failed")
        return
    
    print("\n" + "=" * 60)
    print("🎉 All tests passed! Your PDF extractor is working correctly.")
    print("=" * 60)

if __name__ == "__main__":
    main()
