"""
Example usage of the PDF text extractor
"""

from pdf_text_extractor import extract_pdf_text
import os

def main():
    # Example PDF file path (replace with your actual PDF)
    pdf_path = "/home/damian/Desktop/cloud/immigration-service/documents IN - DE advanced/indianembassyberlin.gov.in_berlin_6jan2024_holiday.pdf"
    
    if not os.path.exists(pdf_path):
        print(f"❌ PDF file not found: {pdf_path}")
        return
    
    try:
        print("🔍 Extracting text from PDF...")
        print(f"📁 File: {pdf_path}")
        
        # Extract text (automatically uses default credentials)
        text = extract_pdf_text(pdf_path)
        
        print(f"✅ Successfully extracted {len(text)} characters")
        print("\n📄 First 1000 characters:")
        print("=" * 60)
        print(text[:1000])
        print("=" * 60)
        
        if len(text) > 1000:
            print("...")
            print(f"📊 Total text length: {len(text)} characters")
        
        # Save to file if you want
        output_file = "extracted_text.txt"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(text)
        print(f"💾 Text saved to: {output_file}")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
