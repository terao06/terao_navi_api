from pydantic import BaseModel, Field


class QuestionResponse(BaseModel):
    answer: str = Field(..., description="回答内容")
