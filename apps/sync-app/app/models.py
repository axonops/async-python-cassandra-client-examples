from pydantic import BaseModel, Field
from datetime import datetime
from typing import Dict, List, Optional
from uuid import UUID, uuid4


class User(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    username: str
    email: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    profile_data: Dict = Field(default_factory=dict)
    
    class Config:
        json_encoders = {
            UUID: str,
            datetime: lambda v: v.isoformat()
        }


class SensorData(BaseModel):
    device_id: UUID
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    temperature: float
    humidity: float
    pressure: float
    metadata: Dict = Field(default_factory=dict)
    
    class Config:
        json_encoders = {
            UUID: str,
            datetime: lambda v: v.isoformat()
        }


class Document(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    title: str
    content: str
    tags: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_encoders = {
            UUID: str,
            datetime: lambda v: v.isoformat()
        }


class PaginationParams(BaseModel):
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=1000)
    
    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size


class SearchParams(BaseModel):
    query: Optional[str] = None
    sort_by: Optional[str] = None
    sort_order: str = Field(default="asc", pattern="^(asc|desc)$")
    filters: Dict[str, str] = Field(default_factory=dict)