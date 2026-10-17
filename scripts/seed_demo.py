import sys
import datetime
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy.orm import Session
from sahaay.database import SessionLocal, init_database
from sahaay.models import User, ResponseUnit, Incident, TranscriptSegment, TriageAssessment, RepeatLink, LexiconEntry
from sahaay.auth import hash_password
from sahaay.repeat_matching.hashing import hash_phone_hmac
from sahaay.repeat_matching.phonetic import get_phonetic_key
from sahaay.config import _load_yaml, CONFIG_DIR

def seed_database(force_reset: bool = False):
    """Initialize database and seed demo data."""
    init_database()
    db: Session = SessionLocal()

    if force_reset:
        print("Force reset requested. Clearing tables...")
        from sahaay.models import DispatchAssignment, AuditEvent
        db.query(DispatchAssignment).delete()
        db.query(RepeatLink).delete()
        db.query(TranscriptSegment).delete()
        db.query(TriageAssessment).delete()
        db.query(Incident).delete()
        db.query(ResponseUnit).delete()
        db.query(LexiconEntry).delete()
        db.query(AuditEvent).delete()
        db.query(User).delete()
        db.commit()
    elif db.query(User).count() > 0:
        print("Database already contains users. Skipping initial seed.")
        db.close()
        return

    print("Seeding demo users...")
    demo_users = [
        User(
            employee_id="OP1042",
            full_name="Riya Sharma",
            email="riya.sharma@sahaay.gov.in",
            hashed_password=hash_password("operator123"),
            role="operator",
            is_active=True
        ),
        User(
            employee_id="SUP201",
            full_name="Vikram Malhotra",
            email="vikram.malhotra@sahaay.gov.in",
            hashed_password=hash_password("super123"),
            role="supervisor",
            is_active=True
        ),
        User(
            employee_id="RES305",
            full_name="Inspector Rajesh Kumar",
            email="rajesh.kumar@delhipolice.gov.in",
            hashed_password=hash_password("police123"),
            role="responder",
            assigned_service="police",
            is_active=True
        ),
        User(
            employee_id="LIN402",
            full_name="Dr. Ananya Sen",
            email="ananya.sen@sahaay.gov.in",
            hashed_password=hash_password("linguist123"),
            role="linguist",
            is_active=True
        ),
        User(
            employee_id="ADM901",
            full_name="Pooja Verma",
            email="pooja.verma@sahaay.gov.in",
            hashed_password=hash_password("admin123"),
            role="admin",
            is_active=True
        ),
        User(
            employee_id="JUDGE01",
            full_name="Hackathon Evaluator",
            email="judge@hackbvp.in",
            hashed_password=hash_password("demo123"),
            role="judge",
            is_active=True
        )
    ]
    db.add_all(demo_users)
    db.commit()

    print("Seeding simulated response units...")
    units = [
        ResponseUnit(id="AMB-A01", service_type="medical", unit_name="Ambulance-01", call_sign="AMB-01", status="available", current_lat=28.6450, current_lon=77.1650, base_lat=28.6450, base_lon=77.1650, speed_kmh=45.0),
        ResponseUnit(id="AMB-A02", service_type="medical", unit_name="Ambulance-02", call_sign="AMB-02", status="available", current_lat=28.6550, current_lon=77.1550, base_lat=28.6550, base_lon=77.1550, speed_kmh=45.0),
        ResponseUnit(id="AMB-A03", service_type="medical", unit_name="Ambulance-03", call_sign="AMB-03", status="available", current_lat=28.6250, current_lon=77.1950, base_lat=28.6250, base_lon=77.1950, speed_kmh=45.0),
        ResponseUnit(id="POL-P01", service_type="police", unit_name="PCR-01", call_sign="PCR-01", status="available", current_lat=28.6380, current_lon=77.1850, base_lat=28.6380, base_lon=77.1850, speed_kmh=50.0),
        ResponseUnit(id="POL-P02", service_type="police", unit_name="PCR-02", call_sign="PCR-02", status="available", current_lat=28.6500, current_lon=77.1700, base_lat=28.6500, base_lon=77.1700, speed_kmh=50.0),
        ResponseUnit(id="FIR-F01", service_type="fire", unit_name="Fire Tender-01", call_sign="FT-01", status="available", current_lat=28.6350, current_lon=77.2150, base_lat=28.6350, base_lon=77.2150, speed_kmh=40.0),
        ResponseUnit(id="NGO-S01", service_type="shelter", unit_name="Saheli Van-01", call_sign="SV-01", status="available", current_lat=28.6300, current_lon=77.2100, base_lat=28.6300, base_lon=77.2100, speed_kmh=35.0),
        ResponseUnit(id="LEG-L01", service_type="legal", unit_name="Legal Clinic-01", call_sign="LC-01", status="available", current_lat=28.6200, current_lon=77.2200, base_lat=28.6200, base_lon=77.2200, speed_kmh=30.0),
        # Rohini / North Delhi units
        ResponseUnit(id="POL-P03", service_type="police", unit_name="PCR-03", call_sign="PCR-03", status="available", current_lat=28.7150, current_lon=77.1300, base_lat=28.7150, base_lon=77.1300, speed_kmh=50.0),
        ResponseUnit(id="AMB-A04", service_type="medical", unit_name="Ambulance-04", call_sign="AMB-04", status="available", current_lat=28.7170, current_lon=77.1280, base_lat=28.7170, base_lon=77.1280, speed_kmh=45.0),
        ResponseUnit(id="FIR-F02", service_type="fire", unit_name="Fire Tender-02", call_sign="FT-02", status="available", current_lat=28.7200, current_lon=77.1250, base_lat=28.7200, base_lon=77.1250, speed_kmh=40.0),
        ResponseUnit(id="NGO-S02", service_type="shelter", unit_name="Saheli Van-02", call_sign="SV-02", status="available", current_lat=28.7190, current_lon=77.1350, base_lat=28.7190, base_lon=77.1350, speed_kmh=35.0),
        # Okhla / South Delhi units
        ResponseUnit(id="POL-P04", service_type="police", unit_name="PCR-04", call_sign="PCR-04", status="available", current_lat=28.5350, current_lon=77.2650, base_lat=28.5350, base_lon=77.2650, speed_kmh=50.0),
        ResponseUnit(id="AMB-A05", service_type="medical", unit_name="Ambulance-05", call_sign="AMB-05", status="available", current_lat=28.5320, current_lon=77.2750, base_lat=28.5320, base_lon=77.2750, speed_kmh=45.0),
        ResponseUnit(id="FIR-F03", service_type="fire", unit_name="Fire Tender-03", call_sign="FT-03", status="available", current_lat=28.5300, current_lon=77.2700, base_lat=28.5300, base_lon=77.2700, speed_kmh=40.0),
        # Dhaula Kuan / SW Delhi units
        ResponseUnit(id="POL-P05", service_type="police", unit_name="PCR-05", call_sign="PCR-05", status="available", current_lat=28.5900, current_lon=77.1650, base_lat=28.5900, base_lon=77.1650, speed_kmh=50.0),
        ResponseUnit(id="AMB-A06", service_type="medical", unit_name="Ambulance-06", call_sign="AMB-06", status="available", current_lat=28.5880, current_lon=77.1620, base_lat=28.5880, base_lon=77.1620, speed_kmh=45.0),
        ResponseUnit(id="FIR-F04", service_type="fire", unit_name="Fire Tender-04", call_sign="FT-04", status="available", current_lat=28.5950, current_lon=77.1700, base_lat=28.5950, base_lon=77.1700, speed_kmh=40.0)
    ]
    db.add_all(units)
    db.commit()

    print("Seeding initial incidents...")
    now = datetime.datetime.utcnow()
    
    incidents_data = [
        {
            "id": "INC-1042",
            "phone": "9876543210",
            "name": "Sunita Verma",
            "urgency": "P0",
            "threat": "Medical Emergency (Cardiac)",
            "loc": "Rajendra Nagar, Delhi",
            "lat": 28.6389,
            "lon": 77.1788,
            "status": "active",
            "text": "Hello... mere papa ko achanak se chest mein bahut dard ho raha hai, saans lene mein bhi takleef ho rahi hai... hum abhi ghar par hi hain... location Rajendra Nagar, Delhi... please jaldi help kijiye.",
            "routes": ["medical"],
            "minutes_ago": 12
        },
        {
            "id": "INC-1041",
            "phone": "8765432109",
            "name": "Pooja Devi",
            "urgency": "P1",
            "threat": "Domestic Violence",
            "loc": "Karol Bagh, Delhi",
            "lat": 28.6514,
            "lon": 77.1907,
            "status": "in_progress",
            "text": "bhaiya mera pati daru peeke maar raha hai, gali no 4 Karol Bagh, bacche ro rahe hain please police bhejo",
            "routes": ["police", "shelter"],
            "minutes_ago": 28
        },
        {
            "id": "INC-1040",
            "phone": "7654321098",
            "name": "Ramesh Kumar",
            "urgency": "P0",
            "threat": "Accident & Fire",
            "loc": "Shalimar Bagh, Delhi",
            "lat": 28.7164,
            "lon": 77.1584,
            "status": "resolved",
            "text": "gadi thuk gayi hai divider se, dhuwan nikal raha hai aur driver behosh hai Shalimar Bagh flyover par",
            "routes": ["medical", "police"],
            "minutes_ago": 75
        },
        {
            "id": "INC-1039",
            "phone": "6543210987",
            "name": "Anjali Sharma",
            "urgency": "P1",
            "threat": "Stalking & Harassment",
            "loc": "Patel Nagar, Delhi",
            "lat": 28.6538,
            "lon": 77.1644,
            "status": "resolved",
            "text": "wahi ladka phir se bike se peecha kar raha hai Patel Nagar metro ke paas, pichle hafte bhi call kiya tha maine",
            "routes": ["police", "legal"],
            "minutes_ago": 140
        },
        {
            "id": "INC-1038",
            "phone": "5432109876",
            "name": "Mohd Irfan",
            "urgency": "P3",
            "threat": "Legal Advisory Query",
            "loc": "Connaught Place, Delhi",
            "lat": 28.6315,
            "lon": 77.2167,
            "status": "resolved",
            "text": "talaq ke baad maintenance claim karne ka kya process hota hai, legal aid vakeel se baat karni hai",
            "routes": ["legal"],
            "minutes_ago": 320
        }
    ]

    for item in incidents_data:
        inc_dt = now - datetime.timedelta(minutes=item["minutes_ago"])
        inc = Incident(
            id=item["id"],
            caller_masked_phone=f"+91 98*** **{item['phone'][-4:]}",
            phone_hmac=hash_phone_hmac(item["phone"]),
            caller_name=item["name"],
            name_phonetic=get_phonetic_key(item["name"]),
            current_urgency=item["urgency"],
            original_urgency=item["urgency"],
            is_urgent_pinned=(item["urgency"] == "P0"),
            status=item["status"],
            primary_threat=item["threat"],
            location_text=item["loc"],
            latitude=item["lat"],
            longitude=item["lon"],
            location_confidence=0.92,
            location_source="transcript",
            location_type="locality",
            safe_contact_flag=True,
            requires_verification=(item["urgency"] == "P0"),
            verification_reasons=["P0_PRIORITY"] if item["urgency"] == "P0" else [],
            created_at=inc_dt,
            updated_at=inc_dt
        )
        db.add(inc)
        db.flush()

        # Transcript segment
        seg = TranscriptSegment(
            incident_id=inc.id,
            timestamp_offset="00:12",
            speaker="Caller",
            raw_text=item["text"],
            normalized_text=item["text"],
            lang_mix="Hinglish",
            asr_confidence=0.92,
            is_whisper=False,
            created_at=inc_dt
        )
        db.add(seg)

        # Triage Assessment
        assessment = TriageAssessment(
            incident_id=inc.id,
            call_id=inc.id,
            urgency=item["urgency"],
            confidence=0.88,
            rules_floor=item["urgency"],
            model_level=item["urgency"],
            flags=["VERIFY"] if item["urgency"] == "P0" else [],
            threat_types=[{"type": item["threat"], "p": 0.92}],
            details={"victim": item["name"], "ongoing": True},
            suggested_routes=item["routes"],
            confirmed_routes=item["routes"],
            evidence_spans=[{"field": "urgency", "span": item["text"][:30], "rule": "R_SEED", "reason": "Initial call text"}],
            missing_fields=[],
            suggested_follow_up="Aap safe jagah par ho?",
            model_version="sahaay-hybrid-v1.0",
            latency_ms=124.5,
            created_at=inc_dt
        )
        db.add(assessment)

    # Seed Lexicon entries from yaml
    covert_yaml = _load_yaml(CONFIG_DIR / "lexicon" / "covert_signals.yaml")
    for entry in covert_yaml.get("entries", []):
        lex = LexiconEntry(
            id=entry["id"],
            phrase=entry["phrase"],
            variants=entry.get("variants", []),
            canonical_meaning=entry["canonical_meaning"],
            threat_type=entry["threat_type"],
            risk_class=entry.get("risk_class", "P1"),
            region=entry.get("region", "Pan-India"),
            context_rules=entry.get("context_rules", []),
            suggested_safe_question=entry.get("suggested_safe_question"),
            suggested_safe_question_hi=entry.get("suggested_safe_question_hi"),
            status="approved",
            version="1.2.0",
            created_by="Linguist",
            approved_by="Dr. Ananya Sen",
            created_at=now,
            approved_at=now
        )
        db.add(lex)

    db.commit()
    print("Demo database successfully seeded!")
    db.close()

if __name__ == "__main__":
    seed_database()
