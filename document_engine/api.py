"""
FastAPI application for the Document Engine.

This API provides endpoints to process documents and folders using the DocumentProcessor.
"""

import os
import shutil
from typing import List, Optional

from fastapi import FastAPI, File, UploadFile, HTTPException, Body
from pydantic import BaseModel

from document_processor import DocumentProcessor

# Initialize FastAPI app
app = FastAPI(
    title="Document Engine API",
    description="Process documents to extract structured data.",
    version="1.0.0"
)

# Initialize DocumentProcessor
# You can configure the API key and output directory via environment variables
gemini_api_key = os.environ.get("GEMINI_API_KEY")
output_dir = os.environ.get("PROCESSED_DOCS_OUTPUT_DIR", "processed_documents")
processor = DocumentProcessor(gemini_api_key=gemini_api_key, output_dir=output_dir)

# Define a temporary directory for file uploads
TEMP_UPLOAD_DIR = "temp_uploads"
os.makedirs(TEMP_UPLOAD_DIR, exist_ok=True)


class FolderRequest(BaseModel):
    """Request model for processing a single folder."""
    folder_path: str

class FoldersRequest(BaseModel):
    """Request model for processing multiple folders."""
    folder_paths: List[str]


@app.post("/process-document/", summary="Process a single uploaded document")
async def process_uploaded_document(
    file: UploadFile = File(...),
    source_uri: Optional[str] = Body(None)
):
    """
    Upload a document (PDF or HTML), process it, and return the structured data.

    - **file**: The document file to process.
    - **source_uri**: Optional source URI for the document.
    """
    temp_file_path = os.path.join(TEMP_UPLOAD_DIR, file.filename)
    try:
        # Save the uploaded file to a temporary location
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Process the document using the DocumentProcessor
        document_data = processor.process_document(temp_file_path, source_uri)
        return document_data

    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {e}")
    finally:
        # Clean up the temporary file
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)


@app.post("/process-folder/", summary="Process a folder of documents on the server")
def process_folder_on_server(request: FolderRequest):
    """
    Process all supported documents within a specified folder on the server.

    - **folder_path**: The absolute path to the folder to process.
    """
    try:
        processed_docs = processor.process_folder(request.folder_path)
        return {
            "message": f"Successfully processed {len(processed_docs)} documents.",
            "processed_documents": processed_docs
        }
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {e}")


@app.post("/process-folders/", summary="Process multiple folders of documents on the server")
def process_folders_on_server(request: FoldersRequest):
    """
    Process all supported documents within a list of specified folders on the server.

    - **folder_paths**: A list of absolute paths to the folders to process.
    """
    try:
        all_documents = processor.process_folders(request.folder_paths)
        return {
            "message": f"Successfully processed {len(all_documents)} documents from all folders.",
            "processed_documents": all_documents
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
