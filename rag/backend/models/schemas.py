from pydantic import BaseModel
from typing import List, Optional

class ChatRequest(BaseModel):
    query: str
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    answer: str
    confidence: float
    sources: List[str]
    supporting_cases: List[str]
    related_cases: List[str]
    suggested_follow_ups: List[str]

class UploadResponse(BaseModel):
    filename: str
    status: str
    message: str
    collection_id: Optional[str] = None

class CompareRequest(BaseModel):
    collection_id: str
    query: Optional[str] = "Compare this FIR with previous cases."

class CompareResponse(BaseModel):
    answer: str
    similar_cases: List[dict]
