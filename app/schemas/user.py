from pydantic import BaseModel, EmailStr, validator
from uuid import UUID
class UserRegister(BaseModel):
    full_name: str
    email: EmailStr
    password: str

    @validator("email")
    def validate_usiu_email(cls, email):
        if not email.endswith("@usiu.ac.ke"):
            raise ValueError("Only USIU-A university email addresses are allowed")
        return email.lower()

class UserResponse(BaseModel):
    id: UUID
    full_name: str
    email: str

    class Config:
        from_attributes = True