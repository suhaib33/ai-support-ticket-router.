"""The contract: the LLM must return THIS shape, or the answer is rejected."""
from typing import Literal, List
from pydantic import BaseModel, Field

Category = Literal["Sales", "Product", "Billing", "IT", "General", "Spam", "Unclear"]

class Classification(BaseModel):
    categories: List[Category] = Field(
        min_length=1, max_length=2,
        description="One category, or two if the message clearly has two separate intents.")
    priority: Literal["High", "Medium", "Low"]
    summary: str = Field(max_length=160, description="One line for the team, no personal data.")
    confidence: float = Field(ge=0.0, le=1.0, description="0 = guessing, 1 = certain.")
