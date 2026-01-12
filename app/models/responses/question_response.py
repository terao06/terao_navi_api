from pydantic import BaseModel, Field


class QuestionResponse(BaseModel):
    answer: str = Field(..., description="質問内容")
