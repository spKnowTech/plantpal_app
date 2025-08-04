from pydantic import BaseModel
from typing import Optional, Literal
from datetime import datetime

class AIChatRequest(BaseModel):
    """Request model for AI chat interaction."""
    input_text: str
    plant_id: Optional[int] = None
    type: Literal["chat", "diagnosis"] = "chat"

class AIChatResponse(BaseModel):
    """Response model for AI chat output."""
    ai_response: str
    type: str
