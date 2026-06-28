"""Request/response shapes for the auth endpoints (validated by Pydantic)."""

import uuid

from pydantic import BaseModel, EmailStr

from app.models.enums import Role


class LoginRequest(BaseModel):
    email: EmailStr


class UserOut(BaseModel):
    id: uuid.UUID
    email: str
    name: str
    role: Role

    model_config = {"from_attributes": True}
