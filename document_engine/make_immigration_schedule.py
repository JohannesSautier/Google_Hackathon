"""
Immigration Document Schedule Generator

This script processes immigration-related documents from specified folders,
extracts text from PDFs and HTML files, and generates structured JSON output
for database storage.
"""

import os
import json
import logging
from typing import List, Dict
from pathlib import Path

# Import our document processor
from document_processor import DocumentProcessor

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def process_immigration_documents(folder_paths: List[str], output_dir: str = "processed_documents", gemini_api_key: str = None) -> List[Dict]:
    """
    Process immigration documents from specified folders and generate JSON output.
    
    Args:
        folder_paths: List of folder paths containing documents to process
        output_dir: Output directory for individual JSON files
        gemini_api_key: Google AI API key for Gemini
        
    Returns:
        List of processed document data
    """
    logger.info("Starting immigration document processing...")
    logger.info(f"Processing {len(folder_paths)} folders: {folder_paths}")
    
    # Initialize document processor with Gemini and output directory
    processor = DocumentProcessor(gemini_api_key, output_dir)
    
    # Process all folders
    all_documents = processor.process_folders(folder_paths)
    
    # Save combined results to JSON file
    combined_output_file = os.path.join(output_dir, "all_documents_combined.json")
    processor.save_results(all_documents, combined_output_file)
    
    logger.info(f"Processing complete! Generated {len(all_documents)} document records.")
    logger.info(f"Individual JSON files saved to: {output_dir}/")
    logger.info(f"Combined JSON file saved to: {combined_output_file}")
    
    return all_documents


def main():
    """
    Main function to process immigration documents.
    """
    # Define the folders to process
    # You can modify this list to include your specific folders
    folder_paths = [
        "/home/damian/Desktop/cloud/immigration-service/documents IN - DE",
        "/home/damian/Desktop/cloud/immigration-service/documents IN - DE advanced"
    ]
    
    # Verify folders exist
    valid_folders = []
    for folder_path in folder_paths:
        if os.path.exists(folder_path):
            valid_folders.append(folder_path)
            logger.info(f"✅ Found folder: {folder_path}")
        else:
            logger.warning(f"❌ Folder not found: {folder_path}")
    
    if not valid_folders:
        logger.error("No valid folders found to process!")
        return
    
    # Get Gemini API key from environment
    gemini_api_key = os.getenv('GEMINI_API_KEY')
    
    if not gemini_api_key:
        print("⚠️  No Gemini API key found in environment variables.")
        print("💡 To use Gemini for better JSON generation:")
        print("   1. Get API key from: https://makersuite.google.com/app/apikey")
        print("   2. Set environment variable: export GEMINI_API_KEY='your_api_key_here'")
        print("   3. Re-run this script")
        print("🔄 Proceeding with fallback JSON generation...")
    
    # Process documents
    try:
        documents = process_immigration_documents(valid_folders, gemini_api_key=gemini_api_key)
        
        # Print summary
        print("\n" + "="*80)
        print("📊 PROCESSING SUMMARY")
        print("="*80)
        print(f"📁 Folders processed: {len(valid_folders)}")
        print(f"📄 Documents processed: {len(documents)}")
        print(f"📂 Output directory: processed_documents/")
        print(f"💾 Individual JSON files: processed_documents/*.json")
        print(f"📋 Combined file: processed_documents/all_documents_combined.json")
        
        # Show document types breakdown
        doc_types = {}
        for doc in documents:
            doc_type = doc.get('documentType', 'UNKNOWN')
            doc_types[doc_type] = doc_types.get(doc_type, 0) + 1
        
        print("\n📋 Document Types:")
        for doc_type, count in doc_types.items():
            print(f"   • {doc_type}: {count} documents")
        
        # Show sample document structure
        if documents:
            print(f"\n📝 Sample Document Structure:")
            print(json.dumps(documents[0], indent=2))
        
        print("\n" + "="*80)
        print("✅ Processing completed successfully!")
        print("💡 You can now import the JSON data into your database.")
        print("="*80)
        
    except Exception as e:
        logger.error(f"Error during processing: {e}")
        raise


if __name__ == "__main__":
    main()
