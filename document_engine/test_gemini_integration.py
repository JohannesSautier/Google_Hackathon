"""
Test script for Gemini integration

This script demonstrates how to use the document processor with Gemini API.
"""

import os
import json
from document_processor import DocumentProcessor

def test_with_gemini_api_key():
    """Test the document processor with a Gemini API key."""
    
    # Get API key from environment or prompt user
    api_key = os.getenv('GEMINI_API_KEY')
    
    if not api_key:
        print("🔑 No Gemini API key found in environment variables!")
        print("\nTo get your Gemini API key:")
        print("1. Go to: https://makersuite.google.com/app/apikey")
        print("2. Sign in with your Google account")
        print("3. Click 'Create API Key'")
        print("4. Copy the API key")
        print("\nThen set it as an environment variable:")
        print("export GEMINI_API_KEY='your_api_key_here'")
        print("\n🔄 Testing with fallback mode only...")
        return test_fallback_mode()
    
    print(f"✅ Using Gemini API key: {api_key[:10]}...")
    
    # Test with a single document
    processor = DocumentProcessor(gemini_api_key=api_key, output_dir="test_output")
    
    pdf_path = '/home/damian/Desktop/cloud/immigration-service/documents IN - DE/infostudents-data.pdf'
    
    print(f"\n🔍 Processing document with Gemini: {pdf_path}")
    
    try:
        doc_data = processor.process_document(pdf_path)
        
        print("✅ Successfully processed document with Gemini!")
        print(f"📄 Document ID: {doc_data['documentId']}")
        print(f"📋 Document Type: {doc_data['documentType']}")
        print(f"📝 Summary: {doc_data['llmSummary'][:150]}...")
        print(f"📊 Checklist Items: {len(doc_data['extractedChecklistItems'])}")
        print(f"🎯 Milestones: {len(doc_data['extractedMilestones'])}")
        print(f"⏰ Timelines: {len(doc_data['extractedTimelines'])}")
        
        if doc_data['extractedChecklistItems']:
            print("\n📋 Checklist Items:")
            for i, item in enumerate(doc_data['extractedChecklistItems'][:5], 1):
                print(f"   {i}. {item}")
        
        if doc_data['extractedMilestones']:
            print("\n🎯 Milestones:")
            for milestone in doc_data['extractedMilestones'][:3]:
                print(f"   • {milestone['name']}: {milestone['description']}")
        
        if doc_data['extractedTimelines']:
            print("\n⏰ Timelines:")
            for timeline in doc_data['extractedTimelines'][:3]:
                print(f"   • {timeline['description']}")
        
        # Save sample output
        with open('sample_gemini_output.json', 'w', encoding='utf-8') as f:
            json.dump(doc_data, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Sample output saved to: sample_gemini_output.json")
        
        return True
        
    except Exception as e:
        print(f"❌ Error processing with Gemini: {e}")
        print("🔄 Falling back to basic mode...")
        return test_fallback_mode()

def test_fallback_mode():
    """Test the document processor in fallback mode."""
    
    print("\n🔍 Testing fallback mode (no Gemini API key)...")
    
    processor = DocumentProcessor(output_dir="test_output")  # No API key = fallback mode
    
    pdf_path = '/home/damian/Desktop/cloud/immigration-service/documents IN - DE/infostudents-data.pdf'
    
    try:
        doc_data = processor.process_document(pdf_path)
        
        print("✅ Successfully processed document in fallback mode!")
        print(f"📄 Document ID: {doc_data['documentId']}")
        print(f"📋 Document Type: {doc_data['documentType']}")
        print(f"📝 Summary: {doc_data['llmSummary'][:150]}...")
        print(f"📊 Checklist Items: {len(doc_data['extractedChecklistItems'])}")
        print(f"🎯 Milestones: {len(doc_data['extractedMilestones'])}")
        print(f"⏰ Timelines: {len(doc_data['extractedTimelines'])}")
        
        # Save sample output
        with open('sample_fallback_output.json', 'w', encoding='utf-8') as f:
            json.dump(doc_data, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Sample output saved to: sample_fallback_output.json")
        
        return True
        
    except Exception as e:
        print(f"❌ Error in fallback mode: {e}")
        return False

def main():
    """Main test function."""
    print("=" * 80)
    print("🧪 GEMINI INTEGRATION TEST")
    print("=" * 80)
    
    success = test_with_gemini_api_key()
    
    print("\n" + "=" * 80)
    if success:
        print("✅ Test completed successfully!")
        print("💡 You can now run the full immigration schedule generator:")
        print("   python3 make_immigration_schedule.py")
    else:
        print("❌ Test failed. Please check the error messages above.")
    print("=" * 80)

if __name__ == "__main__":
    main()
