"""
Example usage of the PDF text extractor
"""

from pdf_text_extractor import extract_pdf_text, PDFTextExtractor

def main():
    # Example PDF file path (replace with your actual PDF)
    pdf_path = "/home/damian/Desktop/cloud/immigration-service/documents IN - DE/infostudents-data.pdf"
    
    # Option 1: Simple usage with the convenience function
    try:
        print("Extracting text from PDF...")
        text = extract_pdf_text(pdf_path)
        print(f"Extracted text length: {len(text)} characters")
        print("\nFirst 500 characters:")
        print(text[:500])
        print("...")
    except Exception as e:
        print(f"Error: {e}")
    
    # Option 2: Using the class directly (useful for multiple extractions)
    # extractor = PDFTextExtractor()
    # text = extractor.extract_text_from_pdf(pdf_path)
    
    # Option 3: With Google Vision API for OCR (requires credentials)
    # google_creds_path = "/path/to/your/google-credentials.json"
    # extractor = PDFTextExtractor(google_creds_path)
    # text = extractor.extract_text_from_pdf(pdf_path)

if __name__ == "__main__":
    main()
