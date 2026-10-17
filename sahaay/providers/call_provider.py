"""Call Session Provider Abstraction and Simulated Call Provider.
Reference: PRD Section 3 (Mandatory call-mode boundary) and Section 4.

CRITICAL SAFETY BOUNDARY:
- Simulation only.
- Never claims live audio or telephony connection.
- Defines future integration points for Exotel or other Indian telephony providers.
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Callable
import time
import datetime
import uuid

class TranscriptEvent:
    """Represents an incremental transcript segment event."""
    def __init__(
        self,
        segment_id: int,
        timestamp_offset: str,
        speaker: str,
        text: str,
        is_final: bool = True,
        asr_confidence: float = 0.92,
        is_whisper: bool = False,
        translation: Optional[str] = None
    ):
        self.segment_id = segment_id
        self.timestamp_offset = timestamp_offset
        self.speaker = speaker
        self.text = text
        self.is_final = is_final  # False = partial interim hypothesis, True = final committed text
        self.asr_confidence = asr_confidence
        self.is_whisper = is_whisper
        self.translation = translation

    def to_dict(self) -> Dict[str, Any]:
        return {
            "segment_id": self.segment_id,
            "timestamp_offset": self.timestamp_offset,
            "speaker": self.speaker,
            "text": self.text,
            "is_final": self.is_final,
            "asr_confidence": self.asr_confidence,
            "is_whisper": self.is_whisper,
            "translation": self.translation
        }

class CallSessionState:
    """Represents the state of an active or simulated call session."""
    RINGING = "RINGING"
    CONNECTED = "CONNECTED"
    PAUSED = "PAUSED"
    ENDED = "ENDED"
    REJECTED = "REJECTED"

class CallSessionProvider(ABC):
    """
    Abstract interface for telephony and call session ingestion.
    
    Future Integration Extension Points:
    - Inbound telephony webhook (e.g. Exotel, Twilio)
    - Secure WebSocket audio streaming
    - Streaming speech-to-text (STT) pipeline (IndicASR, Whisper, Conformer)
    - Partial and final transcript event hooks
    - Call lifecycle state hooks (ringing, answered, disconnected)
    - Signature verification & provider auth
    """

    @abstractmethod
    def start_call(self, scenario_id: Optional[str] = None) -> Dict[str, Any]:
        """Initiate or simulate an incoming call session."""
        pass

    @abstractmethod
    def answer_call(self, session_id: str) -> Dict[str, Any]:
        """Answer the ringing call."""
        pass

    @abstractmethod
    def reject_call(self, session_id: str) -> Dict[str, Any]:
        """Reject the incoming call."""
        pass

    @abstractmethod
    def pause_call(self, session_id: str) -> Dict[str, Any]:
        """Pause/hold the call."""
        pass

    @abstractmethod
    def resume_call(self, session_id: str) -> Dict[str, Any]:
        """Resume the paused call."""
        pass

    @abstractmethod
    def end_call(self, session_id: str) -> Dict[str, Any]:
        """Terminate the call."""
        pass

    @abstractmethod
    def get_next_transcript_event(self, session_id: str) -> Optional[TranscriptEvent]:
        """Retrieve the next streaming transcript chunk (partial or final)."""
        pass

    @abstractmethod
    def is_simulation(self) -> bool:
        """Returns True if running in simulation mode."""
        return True


# Predefined realistic Hinglish & Hindi Emergency Scenarios
PREDEFINED_SIMULATION_SCENARIOS = {
    "scen_domestic_violence": {
        "id": "scen_domestic_violence",
        "title": "1. Active Domestic Violence (Critical P0)",
        "caller_phone": "+91 98765 43210",
        "caller_name": "Sunita Verma",
        "language": "Hinglish (Code-Mixed)",
        "expected_urgency": "P0",
        "expected_threat": "Domestic Violence",
        "expected_location": "Sector 14 Rohini",
        "segments": [
            TranscriptEvent(1, "00:04", "Caller", "Hello... bhaiya jaldi aao...", is_final=False, asr_confidence=0.85, translation="Hello... please come quickly brother..."),
            TranscriptEvent(2, "00:07", "Caller", "Hello... bhaiya jaldi aao please, ghar me bahut jhagda ho raha hai.", is_final=True, asr_confidence=0.94, translation="Hello... please come quickly brother, a severe fight is happening at home."),
            TranscriptEvent(3, "00:12", "Caller", "pati maar raha hai bohot buri tarah se...", is_final=False, asr_confidence=0.88, translation="My husband is beating me very severely..."),
            TranscriptEvent(4, "00:15", "Caller", "pati chaku dikha kar maar raha hai, Sector 14 Rohini gali number 3, bacche ro rahe hain!", is_final=True, asr_confidence=0.96, translation="Husband is beating me while threatening with a knife, Sector 14 Rohini street number 3, children are crying!"),
            TranscriptEvent(5, "00:22", "Caller", "police bhej do jaldi se, darwaza band kar liya hai maine...", is_final=True, asr_confidence=0.92, translation="Please send police quickly, I have locked the door from inside...")
        ]
    },
    "scen_covert_pizza": {
        "id": "scen_covert_pizza",
        "title": "2. Covert Distress — Pizza Order Code (High P1 + VERIFY)",
        "caller_phone": "+91 98111 22334",
        "caller_name": "Anonymous Caller",
        "language": "Hinglish (Whispered Code)",
        "expected_urgency": "P1",
        "expected_threat": "Covert Distress / Domestic Threat",
        "expected_location": "Karol Bagh",
        "segments": [
            TranscriptEvent(1, "00:03", "Caller", "hello... wrong number lag gaya kya...", is_final=False, asr_confidence=0.79, is_whisper=True, translation="Hello... is this a wrong number..."),
            TranscriptEvent(2, "00:06", "Caller", "hello... aap pizza wali dukan ho kya? mujhe ek large pizza chahiye...", is_final=True, asr_confidence=0.88, is_whisper=True, translation="Hello... are you the pizza shop? I need to order a large pizza..."),
            TranscriptEvent(3, "00:12", "Caller", "nahi wo... mera bhai room ke bahar khada hai... (whisper, silence)", is_final=True, asr_confidence=0.84, is_whisper=True, translation="No actually... my brother is standing right outside the room... (whisper, silence)"),
            TranscriptEvent(4, "00:18", "Caller", "address note kar lo... Karol Bagh metro gate number 2 ke paas... jaldi delivery bhejna.", is_final=True, asr_confidence=0.91, is_whisper=True, translation="Take down the address... near Karol Bagh metro gate number 2... send delivery urgently.")
        ]
    },
    "scen_cardiac_medical": {
        "id": "scen_cardiac_medical",
        "title": "3. Acute Cardiac Emergency (Critical P0)",
        "caller_phone": "+91 98990 12345",
        "caller_name": "Rohan Mehra",
        "language": "Hindi / Hinglish",
        "expected_urgency": "P0",
        "expected_threat": "Medical Emergency (Cardiac)",
        "expected_location": "Rajendra Nagar",
        "segments": [
            TranscriptEvent(1, "00:04", "Caller", "emergency ambulance chahiye jaldi!", is_final=False, asr_confidence=0.89, translation="Emergency ambulance needed quickly!"),
            TranscriptEvent(2, "00:08", "Caller", "meri maa ko achanak se severe chest pain ho raha hai, saans nahi aa rahi!", is_final=True, asr_confidence=0.97, translation="My mother is suddenly having severe chest pain, she cannot breathe!"),
            TranscriptEvent(3, "00:14", "Caller", "hosh kho rahi hain wo, Rajendra Nagar Old Market house no 42...", is_final=True, asr_confidence=0.95, translation="She is losing consciousness, Rajendra Nagar Old Market house no 42..."),
            TranscriptEvent(4, "00:20", "Caller", "oxygen cylinder aur doctor team jaldi bhejiye please!", is_final=True, asr_confidence=0.94, translation="Please send an oxygen cylinder and doctor team immediately!")
        ]
    },
    "scen_stalking_repeat": {
        "id": "scen_stalking_repeat",
        "title": "4. Stalking & Repeat Caller (High P1)",
        "caller_phone": "+91 97123 45678",
        "caller_name": "Anjali Sharma",
        "language": "Hinglish",
        "expected_urgency": "P1",
        "expected_threat": "Stalking & Harassment",
        "expected_location": "Patel Nagar Metro",
        "segments": [
            TranscriptEvent(1, "00:05", "Caller", "hello helpline? wahi ladka phir se peecha kar raha hai mera...", is_final=True, asr_confidence=0.93, translation="Hello helpline? That same man is stalking me again..."),
            TranscriptEvent(2, "00:11", "Caller", "pichle hafte bhi maine Patel Nagar se call kiya tha complaint darj karwane...", is_final=True, asr_confidence=0.95, translation="Last week too I called from Patel Nagar to file a complaint..."),
            TranscriptEvent(3, "00:17", "Caller", "wo bike par mera peecha kar raha hai metro station gate number 3 tak, bohot dar lag raha hai.", is_final=True, asr_confidence=0.94, translation="He is tailing me on a motorbike up to metro station gate number 3, I am terrified.")
        ]
    },
    "scen_missing_location": {
        "id": "scen_missing_location",
        "title": "5. Emergency with Ambiguous/Missing Location (P1 + VERIFY)",
        "caller_phone": "+91 96500 88990",
        "caller_name": "Kavita",
        "language": "Hinglish",
        "expected_urgency": "P1",
        "expected_threat": "Intrusion / Threat",
        "expected_location": "Unknown (Near red water tank)",
        "segments": [
            TranscriptEvent(1, "00:05", "Caller", "koi darwaza todne ki koshish kar raha hai bahar se! please bachao!", is_final=True, asr_confidence=0.92),
            TranscriptEvent(2, "00:12", "Caller", "main yahan nayi shift hui hoon, exact sector nahi pata... lal paani ki tanki ke peeche...", is_final=True, asr_confidence=0.86),
            TranscriptEvent(3, "00:19", "Caller", "kisi ko bhejo jaldi, darwaza toot jayega!", is_final=True, asr_confidence=0.91)
        ]
    },
    "scen_legal_query": {
        "id": "scen_legal_query",
        "title": "6. Non-Emergency Legal Aid Query (Low P3)",
        "caller_phone": "+91 95400 11223",
        "caller_name": "Farida Bano",
        "language": "Hindi / Urdu",
        "expected_urgency": "P3",
        "expected_threat": "Legal Advisory",
        "expected_location": "Connaught Place",
        "segments": [
            TranscriptEvent(1, "00:05", "Caller", "namaste, mujhe kanooni salah chahiye thi...", is_final=True, asr_confidence=0.95),
            TranscriptEvent(2, "00:12", "Caller", "talaq ke baad mehr aur bacchon ke kharche ka kya niyam hota hai court mein?", is_final=True, asr_confidence=0.96),
            TranscriptEvent(3, "00:18", "Caller", "kya koi sarkari legal aid vakeel mil sakta hai?", is_final=True, asr_confidence=0.94)
        ]
    },
    "scen_fire_cylinder": {
        "id": "scen_fire_cylinder",
        "title": "7. Industrial Fire & Gas Cylinder Blast (Critical P0)",
        "caller_phone": "+91 98234 56789",
        "caller_name": "Sunil Kumar",
        "language": "Hindi / Hinglish",
        "expected_urgency": "P0",
        "expected_threat": "Fire & Explosion Hazard",
        "expected_location": "Okhla Phase 2",
        "segments": [
            TranscriptEvent(1, "00:04", "Caller", "Hello 112 control room?! Jaldi aag lag gayi hai!", is_final=False, asr_confidence=0.88, translation="Hello 112 control room?! A fire has broken out urgently!"),
            TranscriptEvent(2, "00:08", "Caller", "Okhla Phase 2 factory mein short circuit se aag lag gayi hai, commercial cylinder blast hone wala hai!", is_final=True, asr_confidence=0.96, translation="Fire broke out in Okhla Phase 2 factory from short circuit, commercial gas cylinder is about to explode!"),
            TranscriptEvent(3, "00:15", "Caller", "Kala dhuan bhar gaya hai andar teen mazdoor phase hue hain, fire brigade aur ambulance bhejo turant!", is_final=True, asr_confidence=0.95, translation="Black smoke has filled the area and three workers are trapped inside, send fire brigade and ambulance immediately!"),
            TranscriptEvent(4, "00:22", "Caller", "Hum log bahar nikal aaye hain lekin gate number 4 par log ro rahe hain, jaldi aao!", is_final=True, asr_confidence=0.93, translation="We escaped outside but people are crying at gate number 4, hurry please!")
        ]
    },
    "scen_road_accident": {
        "id": "scen_road_accident",
        "title": "8. Major Multi-Vehicle Crash & Trauma (Critical P0)",
        "caller_phone": "+91 99100 44556",
        "caller_name": "Amitabh Saxena",
        "language": "Hinglish",
        "expected_urgency": "P0",
        "expected_threat": "Road Accident & Critical Trauma",
        "expected_location": "Dhaula Kuan",
        "segments": [
            TranscriptEvent(1, "00:04", "Caller", "Dhaula Kuan flyover par bahut bada road accident ho gaya hai!", is_final=False, asr_confidence=0.89, translation="A major road accident just happened on Dhaula Kuan flyover!"),
            TranscriptEvent(2, "00:09", "Caller", "Speeding truck ne do cars ko thuk diya hai, car overturn ho gayi hai!", is_final=True, asr_confidence=0.97, translation="A speeding truck rammed into two cars, a car has overturned!"),
            TranscriptEvent(3, "00:16", "Caller", "Driver unconscious hai aur sir se bleeding ho rahi hai, khoon beh raha hai bohot zyada!", is_final=True, asr_confidence=0.96, translation="Driver is unconscious with heavy head trauma, severe bleeding!"),
            TranscriptEvent(4, "00:23", "Caller", "Traffic jam lag gaya hai, ALS ambulance aur police rescue van urgently chahiye Dhaula Kuan descent par!", is_final=True, asr_confidence=0.94, translation="Traffic is backed up, ALS ambulance and police rescue van urgently needed at Dhaula Kuan descent!")
        ]
    },
    "scen_tamil_distress": {
        "id": "scen_tamil_distress",
        "title": "9. Tamil (தமிழ்) — Acute Paralytic Stroke (Critical P0)",
        "caller_phone": "+91 94440 12345",
        "caller_name": "S. Sundaram",
        "language": "Tamil (தமிழ் / Tanglish)",
        "expected_urgency": "P0",
        "expected_threat": "Medical Emergency (Stroke / Paralysis)",
        "expected_location": "T Nagar",
        "segments": [
            TranscriptEvent(1, "00:04", "Caller", "En appa ku thideernu... udhavi thevai...", is_final=False, asr_confidence=0.88, translation="My father suddenly collapsed... urgent help needed..."),
            TranscriptEvent(2, "00:08", "Caller", "En appa ku thideernu oru pakkam kai kaal asaiyaama poiduchi, vaai saanjiduchi!", is_final=True, asr_confidence=0.96, translation="My father suddenly lost all movement on one side of his body, and his mouth has drooped!"),
            TranscriptEvent(3, "00:15", "Caller", "Moochu thinaral irukku, hosh illama aaguraaru, T Nagar 3rd street house no 12!", is_final=True, asr_confidence=0.95, translation="He is struggling to breathe and losing consciousness, T Nagar 3rd street house no 12!"),
            TranscriptEvent(4, "00:22", "Caller", "Paralysis stroke pola theriyudhu, ICU ambulance team udane anupunga please!", is_final=True, asr_confidence=0.93, translation="It looks like a paralytic stroke, please send an ICU ambulance team immediately!")
        ]
    },
    "scen_bengali_distress": {
        "id": "scen_bengali_distress",
        "title": "10. Bengali (বাংলা) — Building Fire & Smoke Trap (Critical P0)",
        "caller_phone": "+91 98300 76543",
        "caller_name": "Debolina Mukherjee",
        "language": "Bengali (বাংলা / Banglish)",
        "expected_urgency": "P0",
        "expected_threat": "Fire & Trapped Civilians",
        "expected_location": "CR Park",
        "segments": [
            TranscriptEvent(1, "00:04", "Caller", "Bachan please... aag legeche...", is_final=False, asr_confidence=0.87, translation="Please save us... fire has broken out..."),
            TranscriptEvent(2, "00:08", "Caller", "Aamader flat er ground floor electrical meter box theke bishal agun legeche!", is_final=True, asr_confidence=0.96, translation="A massive fire has erupted from the electrical meter box on our building's ground floor!"),
            TranscriptEvent(3, "00:15", "Caller", "Shob jaygay kaalo dhnowa, staircases bondho, CR Park Market 2 kache 3 te poribar aatke aache!", is_final=True, asr_confidence=0.95, translation="Black smoke everywhere, staircases are blocked, 3 families are trapped near CR Park Market 2!"),
            TranscriptEvent(4, "00:22", "Caller", "Shash kosto hocche shobar, fire brigade aar ambulance jaldi pathan!", is_final=True, asr_confidence=0.94, translation="Everyone is suffocating from smoke inhalation, send fire brigade and ambulance quickly!")
        ]
    },
    "scen_kannada_distress": {
        "id": "scen_kannada_distress",
        "title": "11. Kannada (ಕನ್ನಡ) — Highway Hit-and-Run Crash (Critical P0)",
        "caller_phone": "+91 98450 67890",
        "caller_name": "Lakshmi Gowda",
        "language": "Kannada (ಕನ್ನಡ / Kanglish)",
        "expected_urgency": "P0",
        "expected_threat": "Road Accident & Critical Trauma",
        "expected_location": "Rajendra Nagar",
        "segments": [
            TranscriptEvent(1, "00:04", "Caller", "Sahaya madi... flyover kelage...", is_final=False, asr_confidence=0.86, translation="Please help... under the flyover..."),
            TranscriptEvent(2, "00:08", "Caller", "Ondhu speeding lorry bike ge guddhittu nilladhe hodithu, rider biddu biddane!", is_final=True, asr_confidence=0.95, translation="A speeding truck rammed into a motorcycle and sped away without stopping, rider was thrown off!"),
            TranscriptEvent(3, "00:15", "Caller", "Rider taleyinda thumbe raktha harithide, prajna thappiddane, Rajendra Nagar flyover kelage!", is_final=True, asr_confidence=0.94, translation="The rider has massive head bleeding and is unconscious, right under Rajendra Nagar flyover!"),
            TranscriptEvent(4, "00:22", "Caller", "Usirata tondare ide, dayavittu police van mathu trauma ambulance kalsi!", is_final=True, asr_confidence=0.93, translation="His breathing is faint, please dispatch a police squad and trauma ambulance!")
        ]
    },
    "scen_kumaoni_distress": {
        "id": "scen_kumaoni_distress",
        "title": "12. Kumaoni (कुमाऊँनी) — Hill Landslide & Rollover (Critical P0)",
        "caller_phone": "+91 94120 54321",
        "caller_name": "Kamla Joshi",
        "language": "Kumaoni / Pahari (कुमाऊँनी)",
        "expected_urgency": "P0",
        "expected_threat": "Disaster Rescue & Rollover Trauma",
        "expected_location": "Rohini",
        "segments": [
            TranscriptEvent(1, "00:04", "Caller", "Arey koi madat kara... gaddi girige...", is_final=False, asr_confidence=0.87, translation="Oh someone please help... vehicle fell..."),
            TranscriptEvent(2, "00:08", "Caller", "Pahad bata dhoong pado aur passenger gaddi divider todi ber khayi ma ulti gayi!", is_final=True, asr_confidence=0.96, translation="Boulders rolled down the slope and the passenger vehicle crashed through the divider into the ditch!"),
            TranscriptEvent(3, "00:15", "Caller", "Andar aath yatri fasa cha, khoon bagan laago cha, Rohini sector 14 bypass ke paas!", is_final=True, asr_confidence=0.94, translation="Eight passengers are trapped inside with heavy bleeding, near Rohini sector 14 bypass!"),
            TranscriptEvent(4, "00:22", "Caller", "Gaddi ka darwaza toot ni ro, gas cutter aur rescue ambulance bhyola bheja!", is_final=True, asr_confidence=0.93, translation="Vehicle doors are crushed shut, please send gas cutters and rescue ambulances urgently!")
        ]
    }
}


class SimulatedCallProvider(CallSessionProvider):
    """
    Deterministic simulated operator call session provider.
    Maintains an active call session, segment queue, playback speed, and state transitions.
    """

    def __init__(self):
        self.active_session: Optional[Dict[str, Any]] = None

    def is_simulation(self) -> bool:
        return True

    def start_call(self, scenario_id: Optional[str] = None) -> Dict[str, Any]:
        """Start a new simulated incoming call."""
        if not scenario_id or scenario_id not in PREDEFINED_SIMULATION_SCENARIOS:
            scenario_id = "scen_domestic_violence"
            
        scen = PREDEFINED_SIMULATION_SCENARIOS[scenario_id]
        session_id = f"sim_call_{int(time.time())}_{uuid.uuid4().hex[:4]}"
        
        self.active_session = {
            "session_id": session_id,
            "scenario_id": scenario_id,
            "scenario_title": scen["title"],
            "caller_phone": scen["caller_phone"],
            "caller_name": scen["caller_name"],
            "language": scen["language"],
            "state": CallSessionState.RINGING,
            "segments_queue": list(scen["segments"]),
            "played_segments": [],
            "current_segment_idx": 0,
            "call_started_at": None,
            "call_duration_seconds": 0,
            "is_fast_forward": False,
            "is_simulation": True
        }
        return self.active_session

    def answer_call(self, session_id: str) -> Dict[str, Any]:
        """Operator answers the simulated phone."""
        if not self.active_session or self.active_session["session_id"] != session_id:
            raise ValueError("No matching active call session")
            
        self.active_session["state"] = CallSessionState.CONNECTED
        self.active_session["call_started_at"] = time.time()
        return self.active_session

    def reject_call(self, session_id: str) -> Dict[str, Any]:
        """Operator rejects the incoming call."""
        if not self.active_session or self.active_session["session_id"] != session_id:
            raise ValueError("No matching active call session")
            
        self.active_session["state"] = CallSessionState.REJECTED
        return self.active_session

    def pause_call(self, session_id: str) -> Dict[str, Any]:
        """Hold or pause the call."""
        if not self.active_session or self.active_session["session_id"] != session_id:
            raise ValueError("No matching active call session")
            
        self.active_session["state"] = CallSessionState.PAUSED
        return self.active_session

    def resume_call(self, session_id: str) -> Dict[str, Any]:
        """Resume call from hold."""
        if not self.active_session or self.active_session["session_id"] != session_id:
            raise ValueError("No matching active call session")
            
        self.active_session["state"] = CallSessionState.CONNECTED
        return self.active_session

    def end_call(self, session_id: str) -> Dict[str, Any]:
        """End the call."""
        if not self.active_session or self.active_session["session_id"] != session_id:
            raise ValueError("No matching active call session")
            
        self.active_session["state"] = CallSessionState.ENDED
        return self.active_session

    def get_next_transcript_event(self, session_id: str) -> Optional[TranscriptEvent]:
        """Pop and return the next transcript segment from the scenario queue."""
        if not self.active_session or self.active_session["session_id"] != session_id:
            return None
            
        queue = self.active_session["segments_queue"]
        idx = self.active_session["current_segment_idx"]
        
        if idx < len(queue):
            event = queue[idx]
            self.active_session["current_segment_idx"] += 1
            self.active_session["played_segments"].append(event)
            # Update simulated duration based on offset
            offset_parts = event.timestamp_offset.split(":")
            if len(offset_parts) == 2:
                mins, secs = int(offset_parts[0]), int(offset_parts[1])
                self.active_session["call_duration_seconds"] = mins * 60 + secs
            return event
        return None

    def get_accumulated_transcript(self, session_id: str) -> str:
        """Return the combined text of all played transcript segments."""
        if not self.active_session or self.active_session["session_id"] != session_id:
            return ""
        # Filter for final or latest text
        return " ".join([seg.text for seg in self.active_session["played_segments"] if seg.is_final])

# Global instance for simulation
simulated_call_provider = SimulatedCallProvider()
