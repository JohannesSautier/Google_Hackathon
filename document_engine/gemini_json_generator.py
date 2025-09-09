"""
Gemini JSON Generator

This module uses Google's Gemini 2.5 Pro to generate structured JSON output
from extracted document text, following the specified schema.
"""

import json
import logging
import uuid
from typing import Dict, List, Optional
import google.generativeai as genai

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GeminiJSONGenerator:
    """
    A class to generate structured JSON using Gemini 2.5 Pro.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the Gemini JSON generator.
        
        Args:
            api_key: Google AI API key. If None, will use environment variable.
        """
        if api_key:
            genai.configure(api_key=api_key)
        else:
            # Try to get from environment variable
            import os
            api_key = os.getenv('GEMINI_API_KEY')
            if api_key:
                genai.configure(api_key=api_key)
            else:
                logger.warning("No Gemini API key provided. Set GEMINI_API_KEY environment variable.")
        
        # Initialize the model
        self.model = genai.GenerativeModel('gemini-2.5-flash')

        example_output_format = """
        {"parsedDocuments": [
    {
      "documentId": "doc_parsed_001",
      "sourceURI": "https://travel.state.gov/content/travel/en/us-visas/study-exchange/student-visa.html",
      "documentType": "OFFICIAL_VISA_GUIDE",
      "llmSummary": "This is the primary U.S. Department of State guide for student visas. It outlines the F-1 visa category, defines eligibility, and lists the core application steps. It emphasizes the importance of the I-20 form as a prerequisite for the entire process.",
      "extractedTimelines": [
        {
          "processType": "VISA_APPLICATION", // INSURANCE, PROOFFINANCE, BANKACCOUNT
          "description": "Students can receive their I-20 up to 365 days before the program start date.",
          "value": 365,
          "unit": "days_before_start"
        },
        {
          "timelineKey": "INSURANCE",
          "description": "You may apply for your Insurance as soon as you receive your Form I-20.",
          "value": null,
          "unit": null
        }
      ]
    }
  ]
}"""
        
        # Define the JSON schema prompt with your example
        self.json_schema_prompt = f"""
You are an expert document analyzer specializing in immigration and visa documents. 
Your task is to analyze the provided document text and extract structured information 
according to the following JSON schema:

EXAMPLE OUTPUT FORMAT:
{example_output_format}

Document Types should be one of:
- STUDENT_VISA_GUIDE
- WORK_VISA_GUIDE
- VISA_GUIDE
- CHECKLIST
- APPLICATION_FORM
- OFFICIAL_DOCUMENT
- OFFICIAL_VISA_GUIDE
- INFORMATION_PAGE

For checklist items, extract specific, actionable requirements that applicants must complete.
For milestones, identify key steps in the process with meaningful milestoneKey values.
For timelines, extract time-related requirements with appropriate units (days, weeks, months, years).

Return ONLY valid JSON, no additional text or explanations.
"""
    
    def generate_document_json(self, document_text: str, source_uri: str, document_id: str) -> Dict:
        """
        Generate structured JSON for a document using Gemini.
        
        Args:
            document_text: Extracted text from the document
            source_uri: Source URI of the document
            document_id: Unique document ID
            
        Returns:
            Dictionary with structured document data
        """
        logger.info(f"Generating JSON for document: {document_id}")
        
        try:
            # Prepare the prompt
            full_prompt = f"""
{self.json_schema_prompt}

Document Text:
{document_text[:8000]}  # Limit to 8000 characters to stay within token limits

Source URI: {source_uri}
Document ID: {document_id}

Please analyze this document and return the structured JSON according to the schema above.
"""
            
            # Generate response using Gemini
            response = self.model.generate_content(full_prompt)
            
            # Extract JSON from response
            json_text = response.text.strip()
            
            # Clean up the response (remove markdown formatting if present)
            if json_text.startswith('```json'):
                json_text = json_text[7:]
            if json_text.endswith('```'):
                json_text = json_text[:-3]
            
            # Parse JSON
            document_data = json.loads(json_text)
            
            # Ensure required fields are present
            document_data['documentId'] = f"{str(uuid.uuid4())}"
            document_data['sourceURI'] = source_uri
            
            # Validate and clean the data
            document_data = self._validate_and_clean_json(document_data)
            
            logger.info(f"Successfully generated JSON for document: {document_id}")
            return document_data
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON from Gemini response: {e}")
            logger.error(f"Raw response: {response.text if 'response' in locals() else 'No response'}")
            return self._create_fallback_json(document_text, source_uri, document_id)
        
        except Exception as e:
            logger.error(f"Error generating JSON with Gemini: {e}")
            return self._create_fallback_json(document_text, source_uri, document_id)
    
    def _validate_and_clean_json(self, data: Dict) -> Dict:
        """
        Validate and clean the generated JSON data.
        
        Args:
            data: Raw JSON data from Gemini
            
        Returns:
            Cleaned and validated JSON data
        """
        # Handle the new parsedDocuments array format
        if 'parsedDocuments' in data and isinstance(data['parsedDocuments'], list) and len(data['parsedDocuments']) > 0:
            # Extract the first document from the array
            data = data['parsedDocuments'][0]
        
        # Ensure all required fields exist
        required_fields = ['documentId', 'sourceURI', 'documentType', 'llmSummary', 
                          'extractedChecklistItems', 'extractedMilestones', 'extractedTimelines']
        
        for field in required_fields:
            if field not in data:
                data[field] = [] if field.endswith('s') else ""
        
        # Ensure arrays are lists
        if not isinstance(data.get('extractedChecklistItems'), list):
            data['extractedChecklistItems'] = []
        if not isinstance(data.get('extractedMilestones'), list):
            data['extractedMilestones'] = []
        if not isinstance(data.get('extractedTimelines'), list):
            data['extractedTimelines'] = []
        
        # Clean checklist items
        data['extractedChecklistItems'] = [
            item.strip() for item in data['extractedChecklistItems'] 
            if isinstance(item, str) and len(item.strip()) > 5
        ][:10]  # Limit to 10 items
        
        # Clean milestones
        cleaned_milestones = []
        for milestone in data['extractedMilestones']:
            if isinstance(milestone, dict) and all(key in milestone for key in ['milestoneKey', 'name', 'description']):
                cleaned_milestones.append({
                    'milestoneKey': milestone['milestoneKey'].strip(),
                    'name': milestone['name'].strip(),
                    'description': milestone['description'].strip()
                })
        data['extractedMilestones'] = cleaned_milestones[:5]  # Limit to 5 milestones
        
        # Clean timelines
        cleaned_timelines = []
        for timeline in data['extractedTimelines']:
            if isinstance(timeline, dict) and 'description' in timeline:
                cleaned_timeline = {
                    'description': timeline['description'].strip(),
                    'value': timeline.get('value'),
                    'unit': timeline.get('unit')
                }
                
                # Handle both old and new timeline formats
                if 'timelineKey' in timeline:
                    cleaned_timeline['timelineKey'] = timeline['timelineKey'].strip()
                if 'processType' in timeline:
                    cleaned_timeline['processType'] = timeline['processType'].strip()
                
                cleaned_timelines.append(cleaned_timeline)
        data['extractedTimelines'] = cleaned_timelines[:5]  # Limit to 5 timelines
        
        return data
    
    def _create_fallback_json(self, document_text: str, source_uri: str, document_id: str) -> Dict:
        """
        Create a fallback JSON structure when Gemini fails.
        
        Args:
            document_text: Extracted text from the document
            source_uri: Source URI of the document
            document_id: Unique document ID
            
        Returns:
            Basic JSON structure
        """
        logger.info("Creating fallback JSON structure")
        
        # Simple text analysis for fallback
        text_lower = document_text.lower()
        
        # Determine document type
        if 'visa' in text_lower and 'student' in text_lower:
            doc_type = "STUDENT_VISA_GUIDE"
        elif 'visa' in text_lower:
            doc_type = "VISA_GUIDE"
        elif 'checklist' in text_lower:
            doc_type = "CHECKLIST"
        else:
            doc_type = "OFFICIAL_DOCUMENT"
        
        # Create basic summary
        sentences = document_text.split('.')[:2]
        summary = '. '.join(sentences).strip()
        if len(summary) > 200:
            summary = summary[:200] + "..."
        
        return {
            "documentId": document_id,
            "sourceURI": source_uri,
            "documentType": doc_type,
            "llmSummary": summary or "Document processed successfully.",
            "extractedChecklistItems": [],
            "extractedMilestones": [],
            "extractedTimelines": []
        }


def generate_document_json_with_gemini(document_text: str, source_uri: str, document_id: str, api_key: Optional[str] = None) -> Dict:
    """
    Convenience function to generate JSON using Gemini.
    
    Args:
        document_text: Extracted text from the document
        source_uri: Source URI of the document
        document_id: Unique document ID
        api_key: Google AI API key
        
    Returns:
        Dictionary with structured document data
    """
    generator = GeminiJSONGenerator(api_key)
    return generator.generate_document_json(document_text, source_uri, document_id)


# Example usage
if __name__ == "__main__":
    # Example usage
    sample_text = "This is a sample document about student visa requirements..."
    source_uri = "https://example.com/visa-guide.html"
    document_id = "doc_parsed_001"
    
    # Generate JSON
    # json_data = generate_document_json_with_gemini(sample_text, source_uri, document_id)
    # print(json.dumps(json_data, indent=2))
    pass
