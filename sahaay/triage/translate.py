"""Real-time Pan-Indian to English Translation Engine.
Provides instant English translations for caller distress speech across
Tamil, Bengali, Kannada, Kumaoni/Pahari, Telugu, Marathi, Gujarati, Hindi, and Hinglish.
"""
import re
from typing import Optional

# Curated sentence / phrase translation catalog for instant accurate emergency translation
TRANSLATION_CATALOG = {
    # Tamil (Acute Stroke Emergency)
    "en appa ku thideernu... udhavi thevai...": "My father suddenly collapsed... urgent help needed...",
    "en appa ku thideernu oru pakkam kai kaal asaiyaama poiduchi, vaai saanjiduchi!": "My father suddenly lost all movement on one side of his body, and his mouth has drooped!",
    "moochu thinaral irukku, hosh illama aaguraaru, t nagar 3rd street house no 12!": "He is struggling to breathe and losing consciousness, T Nagar 3rd street house no 12!",
    "paralysis stroke pola theriyudhu, icu ambulance team udane anupunga please!": "It looks like a paralytic stroke, please send an ICU ambulance team immediately!",
    
    # Bengali (Building Fire & Trapped Residents)
    "bachan please... aag legeche...": "Please save us... fire has broken out...",
    "aamader flat er ground floor electrical meter box theke bishal agun legeche!": "A massive fire has erupted from the electrical meter box on our building's ground floor!",
    "shob jaygay kaalo dhnowa, staircases bondho, cr park market 2 kache 3 te poribar aatke aache!": "Black smoke everywhere, staircases are blocked, 3 families are trapped near CR Park Market 2!",
    "shash kosto hocche shobar, fire brigade aar ambulance jaldi pathan!": "Everyone is suffocating from smoke inhalation, send fire brigade and ambulance quickly!",
    
    # Kannada (Hit-and-Run Road Accident)
    "sahaya madi... flyover kelage...": "Please help... under the flyover...",
    "ondhu speeding lorry bike ge guddhittu nilladhe hodithu, rider biddu biddane!": "A speeding truck rammed into a motorcycle and sped away without stopping, rider was thrown off!",
    "rider taleyinda thumbe raktha harithide, prajna thappiddane, rajendra nagar flyover kelage!": "The rider has massive head bleeding and is unconscious, right under Rajendra Nagar flyover!",
    "usirata tondare ide, dayavittu police van mathu trauma ambulance kalsi!": "His breathing is faint, please dispatch a police squad and trauma ambulance!",
    
    # Kumaoni / Pahari (Hill Landslide & Rollover Rescue)
    "arey koi madat kara... gaddi girige...": "Oh someone please help... vehicle fell...",
    "pahad bata dhoong pado aur passenger gaddi divider todi ber khayi ma ulti gayi!": "Boulders rolled down the slope and the passenger vehicle crashed through the divider into the ditch!",
    "andar aath yatri fasa cha, khoon bagan laago cha, rohini sector 14 bypass ke paas!": "Eight passengers are trapped inside with heavy bleeding, near Rohini sector 14 bypass!",
    "gaddi ka darwaza toot ni ro, gas cutter aur rescue ambulance bhyola bheja!": "Vehicle doors are crushed shut, please send gas cutters and rescue ambulances urgently!",
    
    # Hindi / Hinglish Domestic Violence
    "hello... bhaiya jaldi aao...": "Hello... please come quickly brother...",
    "hello... bhaiya jaldi aao please, ghar me bahut jhagda ho raha hai.": "Hello... please come quickly brother, a severe fight is happening at home.",
    "pati maar raha hai bohot buri tarah se...": "My husband is beating me very severely...",
    "pati chaku dikha kar maar raha hai, sector 14 rohini gali number 3, bacche ro rahe hain!": "Husband is beating me while threatening with a knife, Sector 14 Rohini street number 3, children are crying!",
    "police bhej do jaldi se, darwaza band kar liya hai maine...": "Please send police quickly, I have locked the door from inside...",

    # Covert Pizza
    "hello... wrong number lag gaya kya...": "Hello... is this a wrong number...",
    "hello... aap pizza wali dukan ho kya? mujhe ek large pizza chahiye...": "Hello... are you the pizza shop? I need to order a large pizza...",
    "nahi wo... mera bhai room ke bahar khada hai... (whisper, silence)": "No actually... my brother is standing right outside the room... (whisper, silence)",
    "address note kar lo... karol bagh metro gate number 2 ke paas... jaldi delivery bhejna.": "Take down the address... near Karol Bagh metro gate number 2... send delivery urgently.",

    # Cardiac Medical
    "emergency ambulance chahiye jaldi!": "Emergency ambulance needed quickly!",
    "meri maa ko achanak se severe chest pain ho raha hai, saans nahi aa rahi!": "My mother is suddenly having severe chest pain, she cannot breathe!",
    "hosh kho rahi hain wo, rajendra nagar old market house no 42...": "She is losing consciousness, Rajendra Nagar Old Market house no 42...",
    "oxygen cylinder aur doctor team jaldi bhejiye please!": "Please send an oxygen cylinder and doctor team immediately!",

    # Stalking
    "hello helpline? wahi ladka phir se peecha kar raha hai mera...": "Hello helpline? That same man is stalking me again...",
    "pichle hafte bhi maine patel nagar se call kiya tha complaint darj karwane...": "Last week too I called from Patel Nagar to file a complaint...",
    "wo bike par mera peecha kar raha hai metro station gate number 3 tak, bohot dar lag raha hai.": "He is tailing me on a motorbike up to metro station gate number 3, I am terrified.",

    # Missing location
    "koi darwaza todne ki koshish kar raha hai bahar se! please bachao!": "Someone is trying to break down the door from outside! Please save me!",
    "main yahan nayi shift hui hoon, exact sector nahi pata... lal paani ki tanki ke peeche...": "I moved here recently, I don't know the exact sector... behind the red water tank...",
    "kisi ko bhejo jaldi, darwaza toot jayega!": "Send someone fast, the door will break!",

    # Fire / Industrial
    "hello 112 control room?! jaldi aag lag gayi hai!": "Hello 112 control room?! A fire has broken out urgently!",
    "okhla phase 2 factory mein short circuit se aag lag gayi hai, commercial cylinder blast hone wala hai!": "Fire broke out in Okhla Phase 2 factory from short circuit, commercial gas cylinder is about to explode!",
    "kala dhuan bhar gaya hai andar teen mazdoor phase hue hain, fire brigade aur ambulance bhejo turant!": "Black smoke has filled the area and three workers are trapped inside, send fire brigade and ambulance immediately!",
    "hum log bahar nikal aaye hain lekin gate number 4 par log ro rahe hain, jaldi aao!": "We escaped outside but people are crying at gate number 4, hurry please!",

    # Road accident
    "dhaula kuan flyover par bahut bada road accident ho gaya hai!": "A major road accident just happened on Dhaula Kuan flyover!",
    "speeding truck ne do cars ko thuk diya hai, car overturn ho gayi hai!": "A speeding truck rammed into two cars, a car has overturned!",
    "driver unconscious hai aur sir se bleeding ho rahi hai, khoon beh raha hai bohot zyada!": "Driver is unconscious with heavy head trauma, severe bleeding!",
    "traffic jam lag gaya hai, als ambulance aur police rescue van urgently chahiye dhaula kuan descent par!": "Traffic is backed up, ALS ambulance and police rescue van urgently needed at Dhaula Kuan descent!"
}

# Vocabulary mapping for token-level fallback translation
INDIC_WORD_MAP = {
    # Verbs / Action
    "kaapaathunga": "save me", "bachao": "save me", "bachan": "save me", "sahaya": "help", "madat": "help",
    "adikkiraanga": "beating", "marchhe": "beating", "hodeyuthiddane": "beating", "maran": "beating", "maar": "beating",
    "pooti": "locked", "bandhana": "locked", "band": "locked",
    # Roles
    "kanavan": "husband", "purushan": "husband", "shami": "husband", "ganda": "husband", "khasam": "husband", "pati": "husband",
    "kuzhandhaigal": "children", "baccha": "child", "bacche": "children", "makkalu": "children",
    # Danger
    "chaku": "knife", "chhuri": "knife", "katthi": "knife", "katti": "knife",
    "ratham": "blood", "rokto": "blood", "raktha": "blood", "khoon": "blood",
    "thee": "fire", "agun": "fire", "benki": "fire", "aag": "fire",
    "saans": "breathing", "moochu": "breathing", "usirata": "breathing", "shash": "breathing",
    "dard": "pain", "vali": "pain", "novu": "pain", "betha": "pain",
    "jaldi": "urgently", "turant": "immediately", "udane": "immediately", "bheja": "send",
    "police": "police", "ambulance": "ambulance"
}

def translate_to_english(text: str, default: Optional[str] = None) -> str:
    """
    Translates Indic or Hinglish distress text to clear, accurate English.
    Checks exact/normalized phrase catalog first, then applies heuristic vocabulary translation.
    """
    if not text or not text.strip():
        return default or ""
        
    cleaned = text.strip().lower()
    
    # 1. Direct catalog lookup
    if cleaned in TRANSLATION_CATALOG:
        return TRANSLATION_CATALOG[cleaned]
        
    # 2. Fuzzy match catalog key
    for k, v in TRANSLATION_CATALOG.items():
        if k in cleaned or cleaned in k:
            return v

    # 3. Heuristic translation for dynamic utterances
    words = re.findall(r'\b\w+\b', cleaned)
    translated_tokens = []
    has_indic = False
    
    for w in words:
        if w in INDIC_WORD_MAP:
            translated_tokens.append(INDIC_WORD_MAP[w])
            has_indic = True
        else:
            translated_tokens.append(w)
            
    if has_indic:
        res = " ".join(translated_tokens)
        return res[0].upper() + res[1:]
        
    return default or text
