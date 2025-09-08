"""
Document Processor

This module provides functionality to process both PDF and HTML documents,
extract text, and generate structured JSON output.
"""

import os
import json
import logging
from typing import Dict, List, Optional, Union
from pathlib import Path
import hashlib
import uuid
from datetime import datetime

# Import our extractors
from pdf_text_extractor import extract_pdf_text
from html_text_extractor import HTMLTextExtractor
from gemini_json_generator import GeminiJSONGenerator

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DocumentProcessor:
    """
    A class to process documents and generate structured JSON output.
    """
    
    def __init__(self, gemini_api_key: Optional[str] = None, output_dir: str = "processed_documents"):
        """Initialize the document processor."""
        self.html_extractor = HTMLTextExtractor()
        self.gemini_generator = GeminiJSONGenerator(gemini_api_key)
        self.processed_documents = []
        self.output_dir = output_dir
        
        # Create output directory if it doesn't exist
        os.makedirs(self.output_dir, exist_ok=True)
        logger.info(f"Output directory: {os.path.abspath(self.output_dir)}")
    
    def process_document(self, file_path: str, source_uri: Optional[str] = None) -> Dict:
        """
        Process a single document (PDF or HTML) and return structured data.
        
        Args:
            file_path: Path to the document file
            source_uri: Optional source URI (if different from file path)
            
        Returns:
            Dictionary with structured document data
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Document not found: {file_path}")
        
        file_extension = Path(file_path).suffix.lower()
        source_uri = source_uri or file_path
        
        logger.info(f"Processing document: {file_path}")
        
        # Extract text based on file type
        if file_extension == '.pdf':
            extracted_text = extract_pdf_text(file_path)
        elif file_extension in ['.html', '.htm']:
            extracted_text = self.html_extractor.extract_text_from_html_file(file_path)
        else:
            raise ValueError(f"Unsupported file type: {file_extension}")
        
        # Generate document ID
        document_id = self._generate_document_id(file_path, extracted_text)
        
        # Use Gemini to generate structured JSON
        logger.info(f"Generating structured JSON with Gemini for: {document_id}")
        document_data = self.gemini_generator.generate_document_json(
            extracted_text, source_uri, document_id
        )
        
        # Add metadata
        document_data["metadata"] = {
            "filePath": file_path,
            "fileSize": os.path.getsize(file_path),
            "processedAt": datetime.now().isoformat(),
            "textLength": len(extracted_text),
            "fileExtension": file_extension
        }
        
        self.processed_documents.append(document_data)
        
        # Save individual JSON file immediately
        self._save_individual_json(document_data, document_id)
        
        logger.info(f"Successfully processed document: {document_id}")
        
        return document_data
    
    def _generate_document_id(self, file_path: str, text: str) -> str:
        """Generate a unique document ID."""
        # Create a hash based on file path and content
        content_hash = hashlib.md5(f"{file_path}_{text[:1000]}".encode()).hexdigest()[:8]
        return f"doc_parsed_{content_hash}"
    
    def _save_individual_json(self, document_data: Dict, document_id: str):
        """Save individual document as JSON file."""
        try:
            # Create filename from document ID
            filename = f"{document_id}.json"
            filepath = os.path.join(self.output_dir, filename)
            
            # Save JSON file
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(document_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Saved individual JSON: {filepath}")
            
        except Exception as e:
            logger.error(f"Error saving individual JSON for {document_id}: {e}")
    
    
    def process_folder(self, folder_path: str) -> List[Dict]:
        """
        Process all supported documents in a folder.
        
        Args:
            folder_path: Path to the folder to process
            
        Returns:
            List of processed document data
        """
        if not os.path.exists(folder_path):
            raise FileNotFoundError(f"Folder not found: {folder_path}")
        
        logger.info(f"Processing folder: {folder_path}")
        
        processed_docs = []
        supported_extensions = ['.pdf', '.html', '.htm']
        
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                file_path = os.path.join(root, file)
                file_extension = Path(file_path).suffix.lower()
                
                if file_extension in supported_extensions:
                    try:
                        doc_data = self.process_document(file_path)
                        processed_docs.append(doc_data)
                    except Exception as e:
                        logger.error(f"Error processing {file_path}: {e}")
                        continue
        
        logger.info(f"Processed {len(processed_docs)} documents from folder: {folder_path}")
        return processed_docs
    
    def process_folders(self, folder_paths: List[str]) -> List[Dict]:
        """
        Process multiple folders.
        
        Args:
            folder_paths: List of folder paths to process
            
        Returns:
            List of all processed document data
        """
        all_documents = []
        
        for folder_path in folder_paths:
            try:
                folder_docs = self.process_folder(folder_path)
                all_documents.extend(folder_docs)
            except Exception as e:
                logger.error(f"Error processing folder {folder_path}: {e}")
                continue
        
        return all_documents
    
    def save_results(self, documents: List[Dict], output_file: str = "processed_documents.json"):
        """Save processed documents to a JSON file."""
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(documents, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Saved {len(documents)} documents to {output_file}")


def process_document(file_path: str, source_uri: Optional[str] = None) -> Dict:
    """
    Convenience function to process a single document.
    
    Args:
        file_path: Path to the document file
        source_uri: Optional source URI
        
    Returns:
        Dictionary with structured document data
    """
    processor = DocumentProcessor()
    return processor.process_document(file_path, source_uri)


# Example usage
if __name__ == "__main__":
    # Example usage
    processor = DocumentProcessor()
    
    # Process a single document
    # doc_data = processor.process_document("/path/to/document.pdf")
    # print(json.dumps(doc_data, indent=2))
    
    # Process a folder
    # docs = processor.process_folder("/path/to/folder")
    # processor.save_results(docs)
    pass
