from pydantic import BaseModel, Field


class QuestionRequest(BaseModel):
    application_id: int|None = Field(None, description="アプリID")
    question: str = Field(..., description="質問内容")
