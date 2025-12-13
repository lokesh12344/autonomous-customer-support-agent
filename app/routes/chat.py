"""Chat routes for the FastAPI application."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from app.agent import get_agent


router = APIRouter(prefix="/chat", tags=["chat"])


class ChatRequest(BaseModel):
    """Chat request model."""
    message: str
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    """Chat response model."""
    response: str
    session_id: Optional[str] = None


@router.post("/", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """
    Main chat endpoint that receives user messages and returns agent responses.
    
    Args:
        request: ChatRequest containing the user's message and optional session_id
        
    Returns:
        ChatResponse: The agent's response with session_id
    """
    try:
        # Get or create agent instance with session_id
        agent = get_agent()
        
        # Update agent with session ID if provided
        if request.session_id:
            agent.session_id = request.session_id
            agent.memory.session_id = request.session_id
        
        # Run the agent with the user's message
        response = agent.run(request.message)
        
        return ChatResponse(
            response=response,
            session_id=agent.session_id
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing chat request: {str(e)}"
        )


@router.get("/health")
async def chat_health():
    """Health check endpoint for the chat service."""
    return {
        "status": "healthy",
        "service": "chat"
    }
