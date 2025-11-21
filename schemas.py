"""
Database Schemas for Wisp

Each Pydantic model below corresponds to a MongoDB collection.
The collection name is the lowercase of the class name.
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class User(BaseModel):
    name: str = Field(..., description="Full name")
    email: str = Field(..., description="Email address")
    avatar_url: Optional[str] = Field(None, description="Profile image URL")
    plan: str = Field("free", description="Current subscription plan")


class TestResult(BaseModel):
    user_id: str = Field(..., description="User identifier")
    answers: List[str] = Field(..., description="List of color choices in order")
    archetype: str = Field(..., description="Computed personality archetype")
    summary: str = Field(..., description="Short summary of the result")
    score_map: dict = Field(..., description="Raw scoring by trait")
    taken_at: Optional[datetime] = None


class Professional(BaseModel):
    name: str
    specialty: str
    bio: Optional[str] = None
    availability: List[str] = Field(default_factory=list, description="ISO datetime strings")
    rating: Optional[float] = Field(default=4.8, ge=0, le=5)


class Session(BaseModel):
    user_id: str
    professional_id: str
    datetime_iso: str
    notes: Optional[str] = None
    status: str = Field("scheduled")


class Message(BaseModel):
    user_id: str
    role: str = Field(..., description="user or assistant")
    content: str


class Plan(BaseModel):
    id: str
    name: str
    price: float
    interval: str = Field("month")
    features: List[str] = Field(default_factory=list)
