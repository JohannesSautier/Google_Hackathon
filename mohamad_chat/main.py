import os
import json
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import google.generativeai as genai

# --- FastAPI App Initialization ---
app = FastAPI()

# --- Environment Variables ---
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# --- Pydantic Models for API Request and Response ---

class UserContext(BaseModel):
    """
    User-specific data for a personalized chat experience.
    This model can be expanded later with more parameters.
    """
    current_stage: str
    current_timeline: dict
    origin_country: str
    destination_country: str

class ChatRequest(BaseModel):
    user_context: UserContext
    message: str

class ChatResponse(BaseModel):
    agent_response: str
    processed_context: dict

# --- Gemini Configuration ---

def configure_gemini():
    """Configures the Gemini API key from environment variables."""
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY not found in environment variables.")
    genai.configure(api_key=GEMINI_API_KEY)

# --- API Endpoint ---

@app.post("/chat", response_model=ChatResponse)
async def chat_with_agent(request: ChatRequest):
    """
    Endpoint to interact with the AI chat agent.
    
    The user's message and context are sent to Gemini to generate a response.
    """
    try:
        configure_gemini()
        model = genai.GenerativeModel('gemini-2.5-flash')

        # Construct the prompt with comprehensive context
        prompt = f"""
        You are an expert AI assistant designed to help users with their migration process. Your name is Visard.
        You have access to the user's current migration status and timeline.
        
        User's Current Context:
        - Current Stage: {request.user_context.current_stage}
        - Timeline: {json.dumps(request.user_context.current_timeline, indent=2)}
        - Origin Country: {request.user_context.origin_country}
        - Destination Country: {request.user_context.destination_country}
        
        User's message: "{request.message}"

        Based on this information, provide a helpful and empathetic response.
        If the user asks about their timeline, use the provided timeline to give a detailed, relevant answer.
        """

        response = model.generate_content(prompt)
        
        agent_response = response.text
        
        # Return the processed response and a copy of the context for logging/debugging
        return ChatResponse(
            agent_response=agent_response,
            processed_context=request.user_context.model_dump()
        )

    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="An error occurred while communicating with the AI.")
    