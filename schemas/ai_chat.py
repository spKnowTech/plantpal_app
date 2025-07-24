from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class AIChatRequest(BaseModel):
    input_text: str
    plant_id: Optional[int] = None
    type: str = "chat"

class AIChatResponse(BaseModel):
    ai_response: str
    type: str
