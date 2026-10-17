"""Pydantic schemas for data validation and API payloads."""
from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field
import datetime

class LocationCandidate(BaseModel):
    text: str
    type: str = "locality" # locality, landmark, metro_station, area, relative
    confidence: float = 0.80
    lat: Optional[float] = None
    lon: Optional[float] = None

class ThreatPrediction(BaseModel):
    type: str
    p: float
    description: Optional[str] = None

class ExtractedDetails(BaseModel):
    victim: Optional[str] = None
    perpetrator_rel: Optional[str] = None
    weapon: Optional[str] = None
    injury: Optional[str] = None
    ongoing: bool = True
    time_phrase: Optional[str] = None
    people_affected: Optional[int] = 1
    children_present: bool = False

class EvidenceSpan(BaseModel):
    field: str
    span: str
    start: int = 0
    end: int = 0
    rule: str
    reason: Optional[str] = None

class TriageResult(BaseModel):
    call_id: str
    urgency: str # P0, P1, P2, P3
    confidence: float
    rules_floor: str
    model_level: str
    covert_signal_level: str = "P3"
    flags: List[str] = Field(default_factory=list)
    threat_types: List[ThreatPrediction] = Field(default_factory=list)
    location: List[LocationCandidate] = Field(default_factory=list)
    details: ExtractedDetails = Field(default_factory=ExtractedDetails)
    routes: List[str] = Field(default_factory=list)
    evidence: List[EvidenceSpan] = Field(default_factory=list)
    missing_fields: List[str] = Field(default_factory=list)
    suggested_follow_up: Optional[str] = None
    suggested_safe_question: Optional[str] = None
    model_version: str = "esahaay-0.1.0"
    latency_ms: float = 0.0

class RepeatSignal(BaseModel):
    phone: float = 0.0
    alias: float = 0.0
    name: float = 0.0
    place: float = 0.0
    time: float = 0.0

class RepeatCandidate(BaseModel):
    case_id: str
    score: float
    band: str # auto, suggest, new
    signals: Dict[str, Any] = Field(default_factory=dict)
    summary: Optional[str] = None

class UserLogin(BaseModel):
    employee_id: str
    password: str

class UserProfile(BaseModel):
    id: int
    employee_id: str
    full_name: str
    email: str
    role: str
    assigned_service: Optional[str] = None

class PriorityOverride(BaseModel):
    incident_id: str
    new_urgency: str
    reason: str
    actor_id: str
    actor_role: str

class ServiceRouteUpdate(BaseModel):
    incident_id: str
    routes: List[str]
    reason: Optional[str] = None
    actor_id: str
