from typing import Literal
from pydantic import BaseModel, Field


class TicketClassification(BaseModel):
    title: str = Field(min_length=5, max_length=100)
    category: Literal["network", "hardware", "software", "other"]
    priority: Literal["low", "medium", "high"]