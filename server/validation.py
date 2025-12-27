from pydantic import BaseModel, EmailStr, Field, ValidationError
from typing import List, Optional, Any, Dict

class UserRegisterSchema(BaseModel):
    name: str = Field(..., min_length=2, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=6, description="Minimum 6 caractères")

class UserLoginSchema(BaseModel):
    email: EmailStr
    password: str

class QuestionSchema(BaseModel):
    id: str | int
    text: str = Field(..., min_length=5)
    type: str  # ex: 'radio', 'text'
    options: Optional[List[str]] = None

class SurveyCreateSchema(BaseModel):
    title: str = Field(..., min_length=5, max_length=100)
    description: Optional[str] = None
    questions: List[QuestionSchema]