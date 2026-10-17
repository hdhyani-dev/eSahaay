"""SQLAlchemy models for Sahaay Emergency Response & Triage System."""
import datetime
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime, Text, JSON, ForeignKey, Index
)
from sqlalchemy.orm import relationship
from sahaay.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(String(50), unique=True, index=True, nullable=False)
    full_name = Column(String(100), nullable=False)
    email = Column(String(120), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False)  # operator, supervisor, liaison, linguist, admin, judge
    assigned_service = Column(String(50), nullable=True) # for liaison (police, medical, shelter, legal)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    last_login = Column(DateTime, nullable=True)

class Incident(Base):
    __tablename__ = "incidents"

    id = Column(String(50), primary_key=True, index=True)  # e.g. INC-1042
    caller_masked_phone = Column(String(30), nullable=True) # e.g. +91 98765 ***10
    phone_hmac = Column(String(64), index=True, nullable=True) # HMAC-SHA256
    caller_name = Column(String(100), nullable=True)
    name_phonetic = Column(String(50), index=True, nullable=True)
    
    current_urgency = Column(String(10), default="P2", index=True, nullable=False) # P0, P1, P2, P3
    original_urgency = Column(String(10), default="P2", nullable=False)
    is_urgent_pinned = Column(Boolean, default=False)
    status = Column(String(30), default="active", index=True) # active, in_progress, dispatched, resolved, closed
    
    primary_threat = Column(String(100), nullable=True)
    
    # Location
    location_text = Column(String(255), nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    location_confidence = Column(Float, default=0.0)
    location_source = Column(String(50), default="transcript") # verified_gps, transcript, approximate, missing
    location_type = Column(String(50), nullable=True) # locality, landmark, metro_station, area
    
    # Safety & Human-in-the-loop flags
    safe_contact_flag = Column(Boolean, default=True) # False if covert signal or perpetrator near
    requires_verification = Column(Boolean, default=False) # VERIFY flag
    verification_reasons = Column(JSON, default=list)
    
    # Operator confirmation & overrides
    confirmed_by = Column(String(50), nullable=True)
    confirmed_at = Column(DateTime, nullable=True)
    override_reason = Column(Text, nullable=True)
    override_by = Column(String(50), nullable=True)
    
    created_at = Column(DateTime, default=datetime.datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)
    resolution_notes = Column(Text, nullable=True)

    # Relationships
    transcripts = relationship("TranscriptSegment", back_populates="incident", cascade="all, delete-orphan")
    assessments = relationship("TriageAssessment", back_populates="incident", cascade="all, delete-orphan")
    dispatches = relationship("DispatchAssignment", back_populates="incident", cascade="all, delete-orphan")

class TranscriptSegment(Base):
    __tablename__ = "transcript_segments"

    id = Column(Integer, primary_key=True, index=True)
    incident_id = Column(String(50), ForeignKey("incidents.id"), index=True, nullable=False)
    timestamp_offset = Column(String(20), default="00:00")
    speaker = Column(String(30), default="Caller") # Caller, Operator, System
    raw_text = Column(Text, nullable=False)
    normalized_text = Column(Text, nullable=True)
    lang_mix = Column(String(50), default="Hinglish")
    asr_confidence = Column(Float, default=0.92)
    is_whisper = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    incident = relationship("Incident", back_populates="transcripts")

class TriageAssessment(Base):
    __tablename__ = "triage_assessments"

    id = Column(Integer, primary_key=True, index=True)
    incident_id = Column(String(50), ForeignKey("incidents.id"), index=True, nullable=False)
    call_id = Column(String(50), nullable=True)
    
    urgency = Column(String(10), nullable=False) # P0, P1, P2, P3
    confidence = Column(Float, default=0.85)
    rules_floor = Column(String(10), nullable=False)
    model_level = Column(String(10), nullable=False)
    covert_signal_level = Column(String(10), default="P3")
    
    flags = Column(JSON, default=list) # e.g. ["VERIFY", "COVERT_SIGNAL", "MISSING_LOCATION"]
    threat_types = Column(JSON, default=list) # [{"type": "domestic_violence", "p": 0.94}]
    details = Column(JSON, default=dict) # victim, weapon, injury, ongoing, etc.
    suggested_routes = Column(JSON, default=list) # ["police", "shelter"]
    confirmed_routes = Column(JSON, default=list)
    evidence_spans = Column(JSON, default=list) # [{"field": "urgency", "span": "maar raha", "rule": "R1"}]
    missing_fields = Column(JSON, default=list) # ["exact_address", "safe_status"]
    
    suggested_follow_up = Column(Text, nullable=True)
    suggested_safe_question = Column(Text, nullable=True)
    
    model_version = Column(String(50), default="sahaay-hybrid-1.0")
    latency_ms = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    incident = relationship("Incident", back_populates="assessments")

class ResponseUnit(Base):
    __tablename__ = "response_units"

    id = Column(String(50), primary_key=True, index=True) # e.g. AMB-01, POL-02
    service_type = Column(String(30), nullable=False) # medical, police, fire, shelter, legal
    unit_name = Column(String(100), nullable=False)
    call_sign = Column(String(50), nullable=True)
    
    status = Column(String(30), default="available", index=True) # available, assigned, dispatched, acknowledged, en_route, arrived, completed, maintenance
    current_lat = Column(Float, nullable=False)
    current_lon = Column(Float, nullable=False)
    base_lat = Column(Float, nullable=False)
    base_lon = Column(Float, nullable=False)
    speed_kmh = Column(Float, default=45.0)
    
    current_assignment_id = Column(Integer, nullable=True)
    last_updated = Column(DateTime, default=datetime.datetime.utcnow)

class DispatchAssignment(Base):
    __tablename__ = "dispatch_assignments"

    id = Column(Integer, primary_key=True, index=True)
    incident_id = Column(String(50), ForeignKey("incidents.id"), index=True, nullable=False)
    unit_id = Column(String(50), ForeignKey("response_units.id"), index=True, nullable=False)
    service_type = Column(String(30), nullable=False)
    
    status = Column(String(30), default="assigned", index=True) # assigned, dispatched, acknowledged, en_route, arrived, completed, cancelled
    dispatched_at = Column(DateTime, default=datetime.datetime.utcnow)
    acknowledged_at = Column(DateTime, nullable=True)
    en_route_at = Column(DateTime, nullable=True)
    arrived_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    distance_km = Column(Float, default=0.0)
    eta_minutes = Column(Float, default=0.0)
    delay_escalated = Column(Boolean, default=False)
    notes = Column(Text, nullable=True)
    assigned_by = Column(String(50), default="System")

    incident = relationship("Incident", back_populates="dispatches")
    unit = relationship("ResponseUnit")

class RepeatLink(Base):
    __tablename__ = "repeat_links"

    id = Column(Integer, primary_key=True, index=True)
    incident_a_id = Column(String(50), index=True, nullable=False)
    incident_b_id = Column(String(50), index=True, nullable=False)
    score = Column(Float, nullable=False)
    band = Column(String(30), nullable=False) # auto, suggest, new
    signals = Column(JSON, default=dict) # phone_hmac, phonetic_name, place_sim, etc.
    
    status = Column(String(30), default="active") # active, rejected, undone
    created_by = Column(String(50), default="system") # system, supervisor
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    undone_at = Column(DateTime, nullable=True)
    undo_reason = Column(Text, nullable=True)
    undone_by = Column(String(50), nullable=True)

class LexiconEntry(Base):
    __tablename__ = "lexicon_entries"

    id = Column(String(50), primary_key=True, index=True) # COV-001
    phrase = Column(String(100), index=True, nullable=False)
    variants = Column(JSON, default=list)
    canonical_meaning = Column(Text, nullable=False)
    threat_type = Column(String(50), nullable=False)
    risk_class = Column(String(10), default="P1")
    region = Column(String(50), default="Pan-India")
    context_rules = Column(JSON, default=list)
    suggested_safe_question = Column(Text, nullable=True)
    suggested_safe_question_hi = Column(Text, nullable=True)
    
    status = Column(String(30), default="approved") # proposed, approved, retired
    version = Column(String(20), default="1.0.0")
    created_by = Column(String(50), default="Linguist")
    approved_by = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    approved_at = Column(DateTime, nullable=True)

class AuditEvent(Base):
    __tablename__ = "audit_events"

    id = Column(Integer, primary_key=True, index=True)
    actor_id = Column(String(50), nullable=False)
    actor_role = Column(String(50), nullable=False)
    action = Column(String(100), nullable=False) # e.g. PRIORITY_OVERRIDE, REPEAT_LINK_APPROVED, DISPATCH_ASSIGNED
    object_type = Column(String(50), nullable=False) # incident, dispatch, repeat_link, lexicon, policy
    object_id = Column(String(50), nullable=False)
    before_state = Column(JSON, nullable=True)
    after_state = Column(JSON, nullable=True)
    reason = Column(Text, nullable=True)
    ip_address = Column(String(50), default="127.0.0.1")
    timestamp = Column(DateTime, default=datetime.datetime.utcnow, index=True)

class AppSetting(Base):
    __tablename__ = "app_settings"

    key = Column(String(100), primary_key=True)
    value = Column(JSON, nullable=False)
    description = Column(Text, nullable=True)
    requires_two_person_approval = Column(Boolean, default=False)
    pending_value = Column(JSON, nullable=True)
    pending_by = Column(String(50), nullable=True)
    updated_by = Column(String(50), default="admin")
    updated_at = Column(DateTime, default=datetime.datetime.utcnow)
