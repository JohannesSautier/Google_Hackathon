"""
PDF Text Extractor with OCR Support

This module provides functionality to extract text from PDF files,
including scanned documents using Google Vision API OCR.
"""

import os
import io
import logging
from typing import Optional, List
from pathlib import Path

# PDF processing
import fitz  # PyMuPDF
from PIL import Image

# Google Vision API
from google.cloud import vision
from google.oauth2 import service_account

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PDFTextExtractor:
    """
    A class to extract text from PDF files, including OCR for scanned documents.
    """
    
    def __init__(self, google_credentials_path: Optional[str] = None):
        """
        Initialize the PDF text extractor.
        
        Args:
            google_credentials_path: Path to Google Cloud service account JSON file.
                                   If None, will use default credentials or environment variable.
        """
        self.google_credentials_path = google_credentials_path
        self.vision_client = None
        
        # Initialize Google Vision client
        try:
            if google_credentials_path and os.path.exists(google_credentials_path):
                # Use service account key file
                credentials = service_account.Credentials.from_service_account_file(
                    google_credentials_path
                )
                self.vision_client = vision.ImageAnnotatorClient(credentials=credentials)
                logger.info("Google Vision API client initialized with service account key")
            else:
                # Use default credentials (Application Default Credentials)
                self.vision_client = vision.ImageAnnotatorClient()
                logger.info("Google Vision API client initialized with default credentials")
        except Exception as e:
            logger.warning(f"Failed to initialize Google Vision API: {e}")
            logger.warning("OCR functionality will not be available")
            logger.warning("Make sure you're authenticated with: gcloud auth application-default login")
    
    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """
        Extract all text from a PDF file, including OCR for scanned pages.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Extracted text as a string
            
        Raises:
            FileNotFoundError: If the PDF file doesn't exist
            Exception: If there's an error processing the PDF
        """
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        
        logger.info(f"Processing PDF: {pdf_path}")
        
        try:
            # Open the PDF document
            doc = fitz.open(pdf_path)
            extracted_text = []
            
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                logger.info(f"Processing page {page_num + 1}/{len(doc)}")
                
                # First, try to extract text directly
                page_text = page.get_text()
                
                # If no text found or very little text, try OCR
                if not page_text.strip() or len(page_text.strip()) < 50:
                    logger.info(f"Page {page_num + 1} appears to be scanned, attempting OCR")
                    ocr_text = self._extract_text_with_ocr(page)
                    if ocr_text:
                        page_text = ocr_text
                        logger.info(f"OCR extracted {len(ocr_text)} characters from page {page_num + 1}")
                    else:
                        logger.warning(f"No text extracted from page {page_num + 1}")
                
                if page_text.strip():
                    extracted_text.append(f"--- Page {page_num + 1} ---\n{page_text.strip()}\n")
            
            doc.close()
            
            final_text = "\n".join(extracted_text)
            logger.info(f"Successfully extracted {len(final_text)} characters from PDF")
            
            return final_text
            
        except Exception as e:
            logger.error(f"Error processing PDF {pdf_path}: {e}")
            raise
    
    def _extract_text_with_ocr(self, page) -> Optional[str]:
        """
        Extract text from a PDF page using Google Vision API OCR.
        
        Args:
            page: PyMuPDF page object
            
        Returns:
            Extracted text or None if OCR fails
        """
        if not self.vision_client:
            logger.warning("Google Vision API client not available for OCR")
            return None
        
        try:
            # Convert page to image
            mat = fitz.Matrix(2.0, 2.0)  # 2x zoom for better OCR quality
            pix = page.get_pixmap(matrix=mat)
            img_data = pix.tobytes("png")
            
            # Prepare image for Google Vision API
            image = vision.Image(content=img_data)
            
            # Perform OCR
            response = self.vision_client.text_detection(image=image)
            
            if response.error.message:
                logger.error(f"Google Vision API error: {response.error.message}")
                return None
            
            # Extract text from response
            texts = response.text_annotations
            if texts:
                # The first annotation contains all detected text
                return texts[0].description
            
            return None
            
        except Exception as e:
            logger.error(f"OCR extraction failed: {e}")
            return None
    
    def extract_text_from_pdf_simple(self, pdf_path: str) -> str:
        """
        Simple text extraction without OCR (for regular PDFs with selectable text).
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Extracted text as a string
        """
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        
        try:
            doc = fitz.open(pdf_path)
            text = ""
            
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                page_text = page.get_text()
                text += f"\n--- Page {page_num + 1} ---\n{page_text}"
            
            doc.close()
            return text
            
        except Exception as e:
            logger.error(f"Error extracting text from PDF {pdf_path}: {e}")
            raise


def extract_pdf_text(pdf_path: str, google_credentials_path: Optional[str] = None) -> str:
    """
    Convenience function to extract text from a PDF file.
    
    Args:
        pdf_path: Path to the PDF file
        google_credentials_path: Path to Google Cloud service account JSON file
        
    Returns:
        Extracted text as a string
    """
    extractor = PDFTextExtractor(google_credentials_path)
    return extractor.extract_text_from_pdf(pdf_path)


# Example usage
if __name__ == "__main__":
    # Example usage
    pdf_file = "/path/to/your/document.pdf"
    
    # Option 1: With Google Vision API for OCR
    # google_creds = "/path/to/your/google-credentials.json"
    # text = extract_pdf_text(pdf_file, google_creds)
    
    # Option 2: Simple extraction without OCR
    # text = extract_pdf_text(pdf_file)
    
    # print(text)
    pass
