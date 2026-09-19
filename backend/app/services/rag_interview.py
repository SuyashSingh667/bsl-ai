"""
RAG-Powered Adaptive Safety Verification Interview Engine.
Dynamically synthesizes short, concise, high-urgency verification questions
grounded in plant SOP documents (rag_documents/) across 10 Indian languages + English.
Urdu is strictly excluded.
Clauses and document titles are omitted from spoken/text questions for rapid field comprehension.

V2: Answer-Adaptive Branching — follow-up questions are now selected based on
what the worker actually answered in previous turns, not just sequential order.
"""

from __future__ import annotations

import re
from typing import Any
from app.services import rag, answer_classifier
from app.services.rag_interview_flows import CATEGORY_INTERVIEW_FLOWS

# Equipment normalization dictionary across English and Indian languages
_EQUIPMENT_PATTERNS = {
    "valve": ["valve", "flange", "stopcock", "cock", "bypass valve", "v-", "valv", "bloomers", "वाल्व", "ভলভ", "வால்வு", "వాల్వ్", "झडप", "વાલ્વ", "ಕವಾಟ", "വാൽവ്", "ਵਾਲਵ", "ଭଲଭ୍"],
    "pipeline": ["pipe", "pipeline", "gas line", "conduit", "manifold", "steam line", "header", "पाइप", "पाइपलाइन", "পাইপ", "குழாய்", "పైప్‌లైన్", "पाईप", "પાઇપ", "ಪೈಪ್", "പൈപ്പ്", "ਪਾਈਪ", "ପାଇପ୍"],
    "storage_tank": ["tank", "vessel", "cylinder", "gasholder", "holder", "silo", "receiver", "टैंक", "टंकी", "ট্যাঙ্ক", "தொட்டி", "ట్యాంక్", "ટાંકી", "ಟ್ಯಾಂಕ್", "ടാങ്ക്", "ਟੈਂਕ", "ଟାଙ୍କି"],
    "furnace": ["furnace", "coke oven", "converter", "tundish", "runner", "tap hole", "ladle", "bosh", "tuyere", "ब्लास्ट फर्नेस", "भट्ठी", "ভাটি", "உலை", "కొలిమి", "भट्टी", "ધગધગતી ભઠ્ઠી", "ಕುಲುಮೆ", "ചൂള", "ਭੱਠੀ", "ଭାଟି"],
    "electrical_panel": ["panel", "switchgear", "breaker", "transformer", "cable", "switchboard", "busbar", "motor", "starter", "पैनल", "बिजली", "மின்சார", "విద్యుత్", "विद्युत", "વીજળી", "ವಿದ್ಯುತ್", "വൈദ്യുതി", "ਬਿਜਲੀ", "ବିଦ୍ୟୁତ୍"],
    "crane": ["crane", "hoist", "hook", "sling", "trolley", "winch", "wire rope", "boom", "क्रेन", "ক্রেন", "கிரேன்", "క్రేన్", "ક્રેન", "ಕ್ರೇನ್", "ക്രെയിൻ", "ਕ੍ਰੇਨ", "କ୍ରେନ୍"],
    "vehicle": ["forklift", "truck", "wagon", "locomotive", "dumper", "loader", "torpedo car", "गाड़ी", "डंपर"],
    "conveyor": ["conveyor", "belt", "roller", "pulley", "chute", "कन्वेयर", "கன்வேயர்", "కన్వేయర్", "કન્વેયર", "കൺവെയർ"],
    "chemical_container": ["drum", "carboy", "acid tank", "chemical tote", "ibc", "ड्रम", "एसिड"],
    "confined_space": ["tank interior", "pit", "manhole", "duct", "sewer", "tunnel", "sump", "गड्ढा", "मैनहोल"],
}

_LOCATION_PATTERNS = [
    "blast furnace 1", "blast furnace 2", "blast furnace", "coke oven battery", "coke oven",
    "gas holder station", "gas holder", "steel melting shop", "sms", "power plant",
    "rolling mill", "top platform", "cable basement", "pulpit", "control room",
    "substation", "pump house", "oxygen plant", "sinter plant", "refractory",
    "ब्लास्ट फर्नेस 1", "ब्लास्ट फर्नेस 2", "ब्लास्ट फर्नेस", "कोक ओवन", "गैस होल्डर",
    "bf1", "bf2", "cob", "ghs"
]


# ---------------------------------------------------------------------------
# Answer-Adaptive Context Classifier
# ---------------------------------------------------------------------------

def _classify_answer_context(answer_en: str) -> dict[str, bool]:
    """Classifies a worker's answer into contextual flags for adaptive branching."""
    lowered = answer_en.lower() if answer_en else ""
    return {
        "hazard_active": any(w in lowered for w in [
            "active", "spreading", "ongoing", "leaking", "escaping", "hissing",
            "still", "getting worse", "increasing", "cannot control", "not contained",
            "fire actively", "not stopped", "cannot reach", "too hot", "too dangerous",
        ]),
        "hazard_contained": any(w in lowered for w in [
            "contained", "controlled", "isolated", "shut off", "stopped", "secured",
            "suppressed", "extinguished", "loto", "locked out", "cut off", "closed",
            "safely", "under control",
        ]),
        "workers_injured": any(w in lowered for w in [
            "injured", "hurt", "burn", "dizzy", "unconscious", "fainted", "nausea",
            "breathing", "collapsed", "trapped", "blister", "fracture", "choking",
            "suffocating", "headache", "vomiting", "bleeding",
        ]),
        "workers_present": any(w in lowered for w in [
            "worker", "people", "person", "operator", "man", "men", "team",
            "crew", "staff", "2 ", "3 ", "5 ", "10 ", "many", "several", "few",
        ]),
        "area_evacuated": any(w in lowered for w in [
            "evacuated", "cleared", "empty", "no one", "nobody", "moved away",
            "cordoned", "safe distance", "left the area",
        ]),
        "equipment_identified": any(w in lowered for w in [
            "valve", "pipe", "tank", "panel", "breaker", "transformer", "crane",
            "cable", "motor", "furnace", "ladle", "conveyor", "hoist", "truck",
            "dumper", "compressor", "pump",
        ]),
        "uncertain": any(w in lowered for w in [
            "not sure", "don't know", "cannot see", "unclear", "maybe", "might",
            "hard to tell", "didn't see", "can't confirm",
        ]),
    }


# ---------------------------------------------------------------------------
# Adaptive question pools — organized by answer context
# These provide contextually relevant follow-ups based on what the worker said.
# ---------------------------------------------------------------------------

_ADAPTIVE_QUESTIONS = {
    "active_hazard_followup": {
        "q_en": "Are workers still in the danger zone? Has evacuation been started?",
        "opts_en": [
            "Workers have been evacuated to safe assembly point",
            "Workers still in danger zone, evacuation in progress",
            "Workers trapped, cannot evacuate safely",
            "No workers were present in the area",
        ],
        "q_translations": {
            "hi": "क्या कर्मचारी अभी भी खतरे वाले क्षेत्र में हैं? क्या खाली कराना शुरू किया गया है?",
            "bn": "কর্মীরা কি এখনও বিপদ অঞ্চলে আছেন? সরিয়ে নেওয়া শুরু হয়েছে কি?",
            "ta": "தொழிலாளர்கள் இன்னும் ஆபத்து மண்டலத்தில் இருக்கிறார்களா? வெளியேற்றம் தொடங்கப்பட்டதா?",
            "te": "కార్మికులు ఇంకా ప్రమాద ప్రాంతంలో ఉన్నారా? తరలింపు ప్రారంభమైందా?",
            "mr": "कामगार अजून धोक्याच्या क्षेत्रात आहेत का? स्थलांतर सुरू केले आहे का?",
            "gu": "કામદારો હજુ પણ જોખમી વિસ્તારમાં છે? ખાલી કરાવવાનું શરૂ થયું છે?",
            "kn": "ಕೆಲಸಗಾರರು ಇನ್ನೂ ಅಪಾಯ ವಲಯದಲ್ಲಿದ್ದಾರೆಯೇ? ಸ್ಥಳಾಂತರ ಪ್ರಾರಂಭವಾಗಿದೆಯೇ?",
            "ml": "തൊഴിലാളികൾ ഇപ്പോഴും അപകട മേഖലയിലാണോ? ഒഴിപ്പിക്കൽ ആരംഭിച്ചോ?",
            "pa": "ਕਾਮੇ ਅਜੇ ਵੀ ਖ਼ਤਰੇ ਵਾਲੇ ਇਲਾਕੇ ਵਿੱਚ ਹਨ? ਖਾਲੀ ਕਰਾਉਣਾ ਸ਼ੁਰੂ ਹੋਇਆ?",
            "or": "ଶ୍ରମିକମାନେ ଏବେ ବି ବିପଦ ଅଞ୍ଚଳରେ ଅଛନ୍ତି କି? ସ୍ଥଳାନ୍ତର ଆରମ୍ଭ ହୋଇଛି କି?",
        },
        "opts_translations": {
            "hi": ["कर्मचारियों को सुरक्षित स्थान पर ले जाया गया है", "कर्मचारी अभी खतरे में हैं, खाली कराना जारी", "कर्मचारी फंसे हुए हैं, सुरक्षित निकासी संभव नहीं", "उस क्षेत्र में कोई कर्मचारी नहीं था"],
            "bn": ["কর্মীদের নিরাপদ স্থানে সরানো হয়েছে", "কর্মীরা এখনও বিপদে, সরিয়ে নেওয়া চলছে", "কর্মীরা আটকে আছে, নিরাপদে বের হওয়া সম্ভব নয়", "ওই এলাকায় কোনো কর্মী ছিল না"],
            "ta": ["தொழிலாளர்கள் பாதுகாப்பான இடத்திற்கு அழைத்துச் செல்லப்பட்டனர்", "தொழிலாளர்கள் இன்னும் ஆபத்தில், வெளியேற்றம் நடக்கிறது", "தொழிலாளர்கள் சிக்கியுள்ளனர், பாதுகாப்பாக வெளியேற முடியவில்லை", "அந்த பகுதியில் யாரும் இல்லை"],
            "te": ["కార్మికులను సురక్షిత ప్రాంతానికి తరలించారు", "కార్మికులు ఇంకా ప్రమాదంలో, తరలింపు కొనసాగుతోంది", "కార్మికులు చిక్కుకుపోయారు, సురక్షితంగా బయటకు రాలేరు", "ఆ ప్రాంతంలో ఎవరూ లేరు"],
            "mr": ["कामगारांना सुरक्षित ठिकाणी हलवले", "कामगार अजून धोक्यात, स्थलांतर सुरू", "कामगार अडकले, सुरक्षित बाहेर येणे शक्य नाही", "त्या क्षेत्रात कोणी नव्हते"],
            "gu": ["કામદારોને સુરક્ષિત સ્થાને ખસેડવામાં આવ્યા", "કામદારો હજુ જોખમમાં, ખાલી કરાવવું ચાલુ", "કામદારો ફસાયેલા છે, સુરક્ષિત રીતે બહાર નીકળી શકાતું નથી", "તે વિસ્તારમાં કોઈ ન હતું"],
            "kn": ["ಕೆಲಸಗಾರರನ್ನು ಸುರಕ್ಷಿತ ಸ್ಥಳಕ್ಕೆ ಸ್ಥಳಾಂತರಿಸಲಾಗಿದೆ", "ಕೆಲಸಗಾರರು ಇನ್ನೂ ಅಪಾಯದಲ್ಲಿ, ಸ್ಥಳಾಂತರ ನಡೆಯುತ್ತಿದೆ", "ಕೆಲಸಗಾರರು ಸಿಕ್ಕಿಹಾಕಿಕೊಂಡಿದ್ದಾರೆ", "ಆ ಪ್ರದೇಶದಲ್ಲಿ ಯಾರೂ ಇರಲಿಲ್ಲ"],
            "ml": ["തൊഴിലാളികളെ സുരക്ഷിത സ്ഥലത്തേക്ക് മാറ്റി", "തൊഴിലാളികൾ ഇപ്പോഴും അപകടത്തിൽ, ഒഴിപ്പിക്കൽ നടക്കുന്നു", "തൊഴിലാളികൾ കുടുങ്ങി, സുരക്ഷിതമായി പുറത്തിറങ്ങാൻ കഴിയില്ല", "ആ പ്രദേശത്ത് ആരും ഉണ്ടായിരുന്നില്ല"],
            "pa": ["ਕਾਮਿਆਂ ਨੂੰ ਸੁਰੱਖਿਅਤ ਥਾਂ ਤੇ ਲਿਜਾਇਆ ਗਿਆ", "ਕਾਮੇ ਅਜੇ ਖ਼ਤਰੇ ਵਿੱਚ, ਖਾਲੀ ਕਰਾਉਣਾ ਜਾਰੀ", "ਕਾਮੇ ਫਸੇ ਹੋਏ ਹਨ, ਸੁਰੱਖਿਅਤ ਬਾਹਰ ਨਿਕਲ ਨਹੀਂ ਸਕਦੇ", "ਉਸ ਇਲਾਕੇ ਵਿੱਚ ਕੋਈ ਨਹੀਂ ਸੀ"],
            "or": ["ଶ୍ରମିକମାନଙ୍କୁ ସୁରକ୍ଷିତ ସ୍ଥାନକୁ ସ୍ଥାନାନ୍ତର କରାଯାଇଛି", "ଶ୍ରମିକ ଏବେ ବି ବିପଦରେ, ସ୍ଥଳାନ୍ତର ଚାଲିଛି", "ଶ୍ରମିକ ଫସିଯାଇଛନ୍ତି, ସୁରକ୍ଷିତ ବାହାରକୁ ବାହାରି ପାରୁନାହାଁନ୍ତି", "ସେ ଅଞ୍ଚଳରେ କେହି ନଥିଲେ"],
        },
    },
    "injury_followup": {
        "q_en": "How many workers are injured? What type of injuries — burns, breathing difficulty, fractures, or unconscious?",
        "opts_en": [
            "Minor injuries only (cuts, bruises) — workers conscious",
            "Burns or chemical exposure — need medical treatment",
            "Breathing difficulty or toxic exposure — need oxygen/SCBA",
            "Workers unconscious or trapped — need rescue team",
        ],
        "q_translations": {
            "hi": "कितने कर्मचारी घायल हैं? किस प्रकार की चोटें — जलन, सांस की तकलीफ, फ्रैक्चर, या बेहोश?",
            "bn": "কতজন কর্মী আহত? কী ধরনের আঘাত — পোড়া, শ্বাসকষ্ট, ফ্র্যাকচার, নাকি অজ্ঞান?",
            "ta": "எத்தனை தொழிலாளர்கள் காயமடைந்துள்ளனர்? காயங்களின் வகை — தீக்காயம், சுவாசக் கஷ்டம், எலும்பு முறிவு அல்லது மயக்கம்?",
            "te": "ఎంత మంది కార్మికులు గాయపడ్డారు? ఏ రకమైన గాయాలు — కాలిన గాయాలు, శ్వాస ఇబ్బంది, ఎముక విరిగింది లేదా స్పృహ కోల్పోయారా?",
            "mr": "किती कामगार जखमी आहेत? कोणत्या प्रकारच्या दुखापती — भाजणे, श्वास घेण्यास त्रास, फ्रॅक्चर, की बेशुद्ध?",
            "gu": "કેટલા કામદારો ઘાયલ છે? કેવા પ્રકારની ઈજાઓ — દાઝવું, શ્વાસમાં તકલીફ, ફ્રેક્ચર કે બેભાન?",
            "kn": "ಎಷ್ಟು ಕೆಲಸಗಾರರು ಗಾಯಗೊಂಡಿದ್ದಾರೆ? ಯಾವ ರೀತಿಯ ಗಾಯಗಳು — ಸುಟ್ಟ ಗಾಯ, ಉಸಿರಾಟ ತೊಂದರೆ, ಮೂಳೆ ಮುರಿತ ಅಥವಾ ಪ್ರಜ್ಞೆ ಕಳೆದುಕೊಂಡಿದ್ದಾರೆ?",
            "ml": "എത്ര തൊഴിലാളികൾക്ക് പരിക്കേറ്റു? ഏത് തരം പരിക്കുകൾ — പൊള്ളൽ, ശ്വാസതടസ്സം, ഒടിവ്, അതോ ബോധം നഷ്ടപ്പെട്ടോ?",
            "pa": "ਕਿੰਨੇ ਕਾਮੇ ਜ਼ਖ਼ਮੀ ਹਨ? ਕਿਸ ਤਰ੍ਹਾਂ ਦੀਆਂ ਸੱਟਾਂ — ਸੜਨ, ਸਾਹ ਦੀ ਤਕਲੀਫ਼, ਹੱਡੀ ਟੁੱਟੀ ਜਾਂ ਬੇਹੋਸ਼?",
            "or": "କେତେ ଶ୍ରମିକ ଆହତ? କେଉଁ ପ୍ରକାର ଆଘାତ — ଜଳିବା, ଶ୍ବାସକଷ୍ଟ, ଭାଙ୍ଗିବା, କିମ୍ବା ଅଚେତ?",
        },
        "opts_translations": {
            "hi": ["केवल मामूली चोटें (कट, खरोंच) — कर्मचारी होश में", "जलन या केमिकल एक्सपोजर — चिकित्सा जरूरी", "सांस की तकलीफ या जहरीली गैस — ऑक्सीजन/SCBA जरूरी", "कर्मचारी बेहोश या फंसे — रेस्क्यू टीम जरूरी"],
            "bn": ["শুধু সামান্য আঘাত (কাটা, ঘষা) — কর্মীরা সচেতন", "পোড়া বা রাসায়নিক এক্সপোজার — চিকিৎসা প্রয়োজন", "শ্বাসকষ্ট বা বিষাক্ত এক্সপোজার — অক্সিজেন/SCBA প্রয়োজন", "কর্মীরা অজ্ঞান বা আটকে — উদ্ধার দল প্রয়োজন"],
            "ta": ["சிறு காயங்கள் மட்டும் (வெட்டு, சிராய்ப்பு) — தொழிலாளர்கள் நினைவில்", "தீக்காயம் அல்லது ரசாயன தாக்கம் — மருத்துவ சிகிச்சை தேவை", "சுவாசக் கஷ்டம் — ஆக்சிஜன்/SCBA தேவை", "தொழிலாளர்கள் மயக்கமடைந்தனர் — மீட்பு குழு தேவை"],
            "te": ["చిన్న గాయాలు మాత్రమే — కార్మికులు స్పృహలో", "కాలిన గాయాలు లేదా రసాయన బహిర్గతం — వైద్య చికిత్స అవసరం", "శ్వాస ఇబ్బంది — ఆక్సిజన్/SCBA అవసరం", "కార్మికులు స్పృహ కోల్పోయారు — రెస్క్యూ టీమ్ అవసరం"],
            "mr": ["फक्त किरकोळ जखमा — कामगार शुद्धीत", "भाजले किंवा रासायनिक — वैद्यकीय उपचार आवश्यक", "श्वासोच्छवासात अडचण — ऑक्सिजन आवश्यक", "कामगार बेशुद्ध किंवा अडकले — बचाव पथक आवश्यक"],
            "gu": ["માત્ર નાની ઈજાઓ — કામદારો ભાનમાં", "દાઝવું કે રાસાયણિક સંપર્ક — તબીબી સારવાર જરૂરી", "શ્વાસ લેવામાં મુશ્કેલી — ઓક્સિજન જરૂરી", "કામદારો બેભાન કે ફસાયેલા — રેસ્ક્યૂ ટીમ જરૂરી"],
            "kn": ["ಚಿಕ್ಕ ಗಾಯಗಳು ಮಾತ್ರ — ಕೆಲಸಗಾರರು ಪ್ರಜ್ಞೆಯಲ್ಲಿ", "ಸುಟ್ಟ ಗಾಯ ಅಥವಾ ರಾಸಾಯನಿಕ — ವೈದ್ಯಕೀಯ ಅಗತ್ಯ", "ಉಸಿರಾಟ ತೊಂದರೆ — ಆಮ್ಲಜನಕ ಅಗತ್ಯ", "ಕೆಲಸಗಾರರು ಪ್ರಜ್ಞೆ ಕಳೆದುಕೊಂಡಿದ್ದಾರೆ — ರಕ್ಷಣಾ ತಂಡ ಅಗತ್ಯ"],
            "ml": ["ചെറിയ പരിക്കുകൾ മാത്രം — തൊഴിലാളികൾ ബോധത്തിൽ", "പൊള്ളൽ അല്ലെങ്കിൽ രാസ — വൈദ്യ ചികിത്സ ആവശ്യം", "ശ്വാസ തടസ്സം — ഓക്സിജൻ ആവശ്യം", "തൊഴിലാളികൾ ബോധരഹിതം — രക്ഷാ സംഘം ആവശ്യം"],
            "pa": ["ਸਿਰਫ਼ ਮਾਮੂਲੀ ਸੱਟਾਂ — ਕਾਮੇ ਹੋਸ਼ ਵਿੱਚ", "ਸੜਨ ਜਾਂ ਕੈਮੀਕਲ — ਇਲਾਜ ਲੋੜੀਂਦਾ", "ਸਾਹ ਦੀ ਤਕਲੀਫ਼ — ਆਕਸੀਜਨ ਲੋੜੀਂਦੀ", "ਕਾਮੇ ਬੇਹੋਸ਼ ਜਾਂ ਫਸੇ — ਰੈਸਕਿਊ ਟੀਮ ਲੋੜੀਂਦੀ"],
            "or": ["ମାମୁଲି ଆଘାତ — ଶ୍ରମିକ ସଚେତନ", "ଜଳା ବା ରାସାୟନିକ — ଚିକିତ୍ସା ଆବଶ୍ୟକ", "ଶ୍ବାସ ସମସ୍ୟା — ଅମ୍ଳଜାନ ଆବଶ୍ୟକ", "ଶ୍ରମିକ ଅଚେତ — ଉଦ୍ଧାର ଦଳ ଆବଶ୍ୟକ"],
        },
    },
    "contained_followup": {
        "q_en": "When was the hazard isolated? Were any workers exposed or injured before containment?",
        "opts_en": [
            "Isolated immediately, no injuries reported",
            "Isolated after brief exposure — minor symptoms reported",
            "Isolated but some workers had significant exposure",
            "Isolation was done by emergency response, not by local team",
        ],
        "q_translations": {
            "hi": "खतरे को कब आइसोलेट किया गया? क्या बंद करने से पहले कोई कर्मचारी प्रभावित या घायल हुआ?",
            "bn": "কখন বিপদ বিচ্ছিন্ন করা হয়েছিল? বন্ধ করার আগে কোনো কর্মী আক্রান্ত বা আহত হয়েছিল?",
            "ta": "ஆபத்து எப்போது தனிமைப்படுத்தப்பட்டது? கட்டுப்படுத்துவதற்கு முன் தொழிலாளர்கள் பாதிக்கப்பட்டார்களா?",
            "te": "ప్రమాదం ఎప్పుడు ఐసోలేట్ చేశారు? నియంత్రించడానికి ముందు కార్మికులు గాయపడ్డారా?",
            "mr": "धोका कधी वेगळा केला? बंद करण्यापूर्वी कोणी जखमी झाला का?",
            "gu": "જોખમ ક્યારે અલગ કરવામાં આવ્યું? નિયંત્રણ પહેલાં કોઈ કામદાર ઘાયલ થયો?",
            "kn": "ಅಪಾಯವನ್ನು ಯಾವಾಗ ಪ್ರತ್ಯೇಕಿಸಲಾಯಿತು? ನಿಯಂತ್ರಣಕ್ಕೆ ಮುನ್ನ ಯಾರಾದರೂ ಗಾಯಗೊಂಡರೆ?",
            "ml": "അപകടം എപ്പോൾ ഒറ്റപ്പെടുത്തി? നിയന്ത്രണത്തിന് മുമ്പ് ആർക്കെങ്കിലും പരിക്കേറ്റോ?",
            "pa": "ਖ਼ਤਰਾ ਕਦੋਂ ਅਲੱਗ ਕੀਤਾ? ਬੰਦ ਕਰਨ ਤੋਂ ਪਹਿਲਾਂ ਕੋਈ ਕਾਮਾ ਜ਼ਖ਼ਮੀ ਹੋਇਆ?",
            "or": "ବିପଦ କେବେ ପୃଥକ କରାଗଲା? ନିୟନ୍ତ୍ରଣ ପୂର୍ବରୁ କେହି ଆହତ ହୋଇଥିଲେ?",
        },
        "opts_translations": {
            "hi": ["तुरंत बंद किया, कोई चोट नहीं", "थोड़े एक्सपोजर के बाद बंद — मामूली लक्षण", "बंद किया लेकिन कुछ कर्मचारी काफी प्रभावित", "आपातकालीन दल ने बंद किया, स्थानीय टीम ने नहीं"],
            "bn": ["তাৎক্ষণিক বন্ধ, কোনো আঘাত নেই", "সংক্ষিপ্ত এক্সপোজারের পরে বন্ধ — সামান্য লক্ষণ", "বন্ধ করা হয়েছে কিন্তু কিছু কর্মী উল্লেখযোগ্যভাবে আক্রান্ত", "জরুরি দল বন্ধ করেছে"],
            "ta": ["உடனடியாக நிறுத்தப்பட்டது, காயமில்லை", "சிறிது நேர தாக்கத்திற்குப் பிறகு — சிறிய அறிகுறிகள்", "நிறுத்தப்பட்டது ஆனால் சில தொழிலாளர்கள் பாதிக்கப்பட்டனர்", "அவசர குழு நிறுத்தியது"],
            "te": ["వెంటనే ఆపారు, గాయాలు లేవు", "కొద్దిసేపు బహిర్గతం తర్వాత — తేలికపాటి లక్షణాలు", "ఆపారు కానీ కొంతమంది కార్మికులు బాగా ప్రభావితమయ్యారు", "ఎమర్జెన్సీ టీమ్ ఆపింది"],
            "mr": ["त्वरित बंद, दुखापत नाही", "थोड्या एक्सपोजरनंतर बंद — किरकोळ लक्षणे", "बंद केले पण काही कामगार बऱ्यापैकी प्रभावित", "आणीबाणी पथकाने बंद केले"],
            "gu": ["તરત બંધ, કોઈ ઈજા નહીં", "ટૂંકા સંપર્ક પછી બંધ — સામાન્ય લક્ષણો", "બંધ કર્યું પણ કેટલાક કામદારો નોંધપાત્ર રીતે પ્રભાવિત", "ઈમરજન્સી ટીમે બંધ કર્યું"],
            "kn": ["ತಕ್ಷಣ ನಿಲ್ಲಿಸಲಾಯಿತು, ಗಾಯವಿಲ್ಲ", "ಸ್ವಲ್ಪ ಸಮಯದ ಸಂಪರ್ಕದ ನಂತರ — ಸಣ್ಣ ಲಕ್ಷಣಗಳು", "ನಿಲ್ಲಿಸಲಾಯಿತು ಆದರೆ ಕೆಲವರು ಗಮನಾರ್ಹವಾಗಿ ಪ್ರಭಾವಿತ", "ತುರ್ತು ತಂಡ ನಿಲ್ಲಿಸಿತು"],
            "ml": ["ഉടൻ നിർത്തി, പരിക്കില്ല", "ചെറിയ എക്സ്പോഷറിന് ശേഷം — ചെറിയ ലക്ഷണങ്ങൾ", "നിർത്തി പക്ഷേ ചിലർക്ക് കാര്യമായ എക്സ്പോഷർ", "എമർജൻസി ടീം നിർത്തി"],
            "pa": ["ਤੁਰੰਤ ਬੰਦ, ਕੋਈ ਸੱਟ ਨਹੀਂ", "ਥੋੜੇ ਐਕਸਪੋਜ਼ਰ ਤੋਂ ਬਾਅਦ ਬੰਦ — ਮਾਮੂਲੀ ਲੱਛਣ", "ਬੰਦ ਕੀਤਾ ਪਰ ਕੁਝ ਕਾਮੇ ਕਾਫ਼ੀ ਪ੍ਰਭਾਵਿਤ", "ਐਮਰਜੈਂਸੀ ਟੀਮ ਨੇ ਬੰਦ ਕੀਤਾ"],
            "or": ["ତୁରନ୍ତ ବନ୍ଦ, ଆଘାତ ନାହିଁ", "ସ୍ୱଳ୍ପ ସମ୍ପର୍କ ପରେ ବନ୍ଦ — ମାମୁଲି ଲକ୍ଷଣ", "ବନ୍ଦ ହେଲା କିନ୍ତୁ କେତେକ ଶ୍ରମିକ ଗୁରୁତର ଭାବେ ପ୍ରଭାବିତ", "ଜରୁରୀକାଳୀନ ଦଳ ବନ୍ଦ କଲା"],
        },
    },
    "personnel_count_followup": {
        "q_en": "How many workers are currently in the affected zone? Has Control Room been notified?",
        "opts_en": [
            "1-2 workers only, Control Room notified",
            "3-5 workers, Control Room notified",
            "More than 5 workers, Control Room NOT yet notified",
            "Area is empty now, Control Room was notified",
        ],
        "q_translations": {
            "hi": "प्रभावित क्षेत्र में अभी कितने कर्मचारी हैं? क्या कंट्रोल रूम को सूचित किया गया?",
            "bn": "আক্রান্ত এলাকায় এখন কতজন কর্মী আছেন? কন্ট্রোল রুমকে জানানো হয়েছে?",
            "ta": "பாதிக்கப்பட்ட பகுதியில் இப்போது எத்தனை தொழிலாளர்கள்? கண்ட்ரோல் ரூமுக்கு தகவல் அளிக்கப்பட்டதா?",
            "te": "ప్రభావిత ప్రాంతంలో ప్రస్తుతం ఎంతమంది? కంట్రోల్ రూమ్‌కు తెలియజేశారా?",
            "mr": "प्रभावित क्षेत्रात सध्या किती कामगार? कंट्रोल रूमला कळवले आहे का?",
            "gu": "અસરગ્રસ્ત વિસ્તારમાં હાલ કેટલા કામદારો? કંટ્રોલ રૂમને જાણ કરી?",
            "kn": "ಪ್ರಭಾವಿತ ಪ್ರದೇಶದಲ್ಲಿ ಈಗ ಎಷ್ಟು ಕೆಲಸಗಾರರು? ಕಂಟ್ರೋಲ್ ರೂಮ್‌ಗೆ ತಿಳಿಸಲಾಗಿದೆಯೇ?",
            "ml": "ബാധിത പ്രദേശത്ത് ഇപ്പോൾ എത്ര തൊഴിലാളികൾ? കൺട്രോൾ റൂമിൽ അറിയിച്ചോ?",
            "pa": "ਪ੍ਰਭਾਵਿਤ ਖੇਤਰ ਵਿੱਚ ਹੁਣ ਕਿੰਨੇ ਕਾਮੇ? ਕੰਟਰੋਲ ਰੂਮ ਨੂੰ ਦੱਸਿਆ?",
            "or": "ପ୍ରଭାବିତ ଅଞ୍ଚଳରେ ଏବେ କେତେ ଶ୍ରମିକ? କଣ୍ଟ୍ରୋଲ ରୁମ୍‌କୁ ଜଣାଇଛନ୍ତି?",
        },
        "opts_translations": {
            "hi": ["1-2 कर्मचारी, कंट्रोल रूम को सूचित किया", "3-5 कर्मचारी, कंट्रोल रूम को सूचित किया", "5 से अधिक कर्मचारी, कंट्रोल रूम को अभी सूचित नहीं किया", "क्षेत्र अब खाली है, कंट्रोल रूम को सूचित किया गया"],
            "bn": ["1-2 কর্মী, কন্ট্রোল রুম জানানো হয়েছে", "3-5 কর্মী, কন্ট্রোল রুম জানানো হয়েছে", "5 এর বেশি কর্মী, কন্ট্রোল রুম এখনও জানানো হয়নি", "এলাকা এখন খালি, কন্ট্রোল রুম জানানো হয়েছে"],
            "ta": ["1-2 தொழிலாளர்கள், கண்ட்ரோல் ரூம் தகவல்", "3-5 தொழிலாளர்கள், கண்ட்ரோல் ரூம் தகவல்", "5க்கு மேல், கண்ட்ரோல் ரூம் தகவல் இல்லை", "பகுதி காலியாக உள்ளது, கண்ட்ரோல் ரூம் தகவல்"],
            "te": ["1-2 కార్మికులు, కంట్రోల్ రూమ్‌కు తెలియజేశారు", "3-5 కార్మికులు, కంట్రోల్ రూమ్‌కు తెలియజేశారు", "5 కంటే ఎక్కువ, కంట్రోల్ రూమ్‌కు ఇంకా తెలియజేయలేదు", "ప్రాంతం ఖాళీగా ఉంది"],
            "mr": ["1-2 कामगार, कंट्रोल रूमला कळवले", "3-5 कामगार, कंट्रोल रूमला कळवले", "5 पेक्षा जास्त, कंट्रोल रूमला अजून कळवले नाही", "क्षेत्र रिकामे, कंट्रोल रूमला कळवले"],
            "gu": ["1-2 કામદાર, કંટ્રોલ રૂમને જાણ કરી", "3-5 કામદાર, કંટ્રોલ રૂમને જાણ કરી", "5થી વધુ, કંટ્રોલ રૂમને હજુ જાણ નથી કરી", "વિસ્તાર ખાલી, કંટ્રોલ રૂમને જાણ કરી"],
            "kn": ["1-2 ಕೆಲಸಗಾರರು, ಕಂಟ್ರೋಲ್ ರೂಮ್ ತಿಳಿಸಲಾಗಿದೆ", "3-5 ಕೆಲಸಗಾರರು, ಕಂಟ್ರೋಲ್ ರೂಮ್ ತಿಳಿಸಲಾಗಿದೆ", "5ಕ್ಕಿಂತ ಹೆಚ್ಚು, ಕಂಟ್ರೋಲ್ ರೂಮ್ ಇನ್ನೂ ತಿಳಿಸಿಲ್ಲ", "ಪ್ರದೇಶ ಖಾಲಿ, ಕಂಟ್ರೋಲ್ ರೂಮ್ ತಿಳಿಸಲಾಗಿದೆ"],
            "ml": ["1-2 തൊഴിലാളികൾ, കൺട്രോൾ റൂമിന് അറിയിച്ചു", "3-5 തൊഴിലാളികൾ, കൺട്രോൾ റൂമിന് അറിയിച്ചു", "5-ൽ കൂടുതൽ, കൺട്രോൾ റൂമിന് ഇതുവരെ അറിയിച്ചിട്ടില്ല", "പ്രദേശം ഒഴിഞ്ഞിരിക്കുന്നു"],
            "pa": ["1-2 ਕਾਮੇ, ਕੰਟਰੋਲ ਰੂਮ ਨੂੰ ਦੱਸਿਆ", "3-5 ਕਾਮੇ, ਕੰਟਰੋਲ ਰੂਮ ਨੂੰ ਦੱਸਿਆ", "5 ਤੋਂ ਵੱਧ, ਕੰਟਰੋਲ ਰੂਮ ਨੂੰ ਅਜੇ ਨਹੀਂ ਦੱਸਿਆ", "ਇਲਾਕਾ ਖਾਲੀ, ਕੰਟਰੋਲ ਰੂਮ ਨੂੰ ਦੱਸਿਆ"],
            "or": ["1-2 ଶ୍ରମିକ, କଣ୍ଟ୍ରୋଲ ରୁମ୍‌କୁ ଜଣାଇଛନ୍ତି", "3-5 ଶ୍ରମିକ, କଣ୍ଟ୍ରୋଲ ରୁମ୍‌କୁ ଜଣାଇଛନ୍ତି", "5ରୁ ଅଧିକ, କଣ୍ଟ୍ରୋଲ ରୁମ୍‌କୁ ଏପର୍ଯ୍ୟନ୍ତ ଜଣାଇ ନାହାଁନ୍ତି", "ଅଞ୍ଚଳ ଖାଲି, କଣ୍ଟ୍ରୋଲ ରୁମ୍‌କୁ ଜଣାଇଛନ୍ତି"],
        },
    },
}


def extract_incident_context(
    description_en: str,
    prior_questions: list[str],
    prior_answers_en: list[str],
    zone_id: str | None = None,
    raw_description: str = "",
) -> dict[str, Any]:
    full_text = f"{raw_description} {description_en} {' '.join(prior_answers_en)}".lower()

    detected_equipment = None
    for eq_type, keywords in _EQUIPMENT_PATTERNS.items():
        for kw in keywords:
            if kw in full_text:
                detected_equipment = eq_type
                break
        if detected_equipment:
            break

    detected_location = zone_id or None
    for loc in _LOCATION_PATTERNS:
        if loc in full_text:
            detected_location = loc.title()
            break

    saw_evidence = any(w in full_text for w in ["saw", "see", "visible", "looked", "flame", "fire", "smoke", "leaking", "burst", "sparks"])
    smelled_evidence = any(w in full_text for w in ["smell", "smelled", "odor", "fumes", "stench"])
    is_isolated = any(w in full_text for w in ["isolated", "shut", "closed", "loto", "locked", "tripped", "cut off", "secured"])
    cannot_isolate = any(w in full_text for w in ["cannot reach", "inaccessible", "too hot", "too thick", "hissing", "live", "dangerous to approach", "spreading"])
    personnel_mentioned = any(w in full_text for w in ["people", "worker", "operator", "dizzy", "burn", "unconscious", "nobody", "no one", "trapped", "injured"])

    return {
        "equipment": detected_equipment,
        "location": detected_location,
        "saw_evidence": saw_evidence,
        "smelled_evidence": smelled_evidence,
        "is_isolated": is_isolated,
        "cannot_isolate": cannot_isolate,
        "personnel_mentioned": personnel_mentioned,
    }


def _get_equipment_display(eq: str | None) -> dict[str, str]:
    displays = {
        "valve": {
            "en": "valve", "hi": "वाल्व", "bn": "ভালভ",
            "ta": "வால்வு", "te": "వాల్వ్", "mr": "वाल्व",
            "gu": "વાલ્વ", "kn": "ವಾಲ್ವ್", "ml": "വാൽവ്",
            "pa": "ਵਾਲਵ", "or": "ଭାଲ୍ଭ"
        },
        "pipeline": {
            "en": "pipeline", "hi": "पाइपलाइन", "bn": "পাইপলাইন",
            "ta": "குழாய்", "te": "పైప్‌లైన్", "mr": "पाईपलाईन",
            "gu": "પાઇપલાઇન", "kn": "ಪೈಪ್‌ಲೈನ್", "ml": "പൈപ്പ്‌ലൈൻ",
            "pa": "ਪਾਈਪਲਾਈਨ", "or": "ପାଇପଲାଇନ"
        },
        "storage_tank": {
            "en": "tank", "hi": "टैंक", "bn": "ট্যাঙ্ক",
            "ta": "தொட்டி", "te": "ట్యాంక్", "mr": "टाकी",
            "gu": "ટાંકી", "kn": "ತೊಟ್ಟಿ", "ml": "ടാങ്ക്",
            "pa": "ਟੈਂਕ", "or": "ଟାଙ୍କି"
        },
        "electrical_panel": {
            "en": "electrical panel", "hi": "इलेक्ट्रिकल पैनल", "bn": "বৈদ্যুতিক প্যানেল",
            "ta": "மின் குழு", "te": "ఎలక్ట్రికల్ ప్యానెల్", "mr": "विद्युत पॅनेल",
            "gu": "ઇલેક્ટ્રિકલ પેનલ", "kn": "ವಿದ್ಯುತ್ ಪ್ಯಾನೆಲ್", "ml": "ഇലക്ട്രിക്കൽ പാനൽ",
            "pa": "ਇਲੈਕਟ੍ਰੀਕਲ ਪੈਨਲ", "or": "ବିଦ୍ୟୁତ ପ୍ୟାନେଲ"
        },
        "furnace": {
            "en": "furnace", "hi": "भट्टी", "bn": "চুল্লি",
            "ta": "உலை", "te": "కొలిమి", "mr": "भट्टी",
            "gu": "ભઠ્ઠી", "kn": "ಕುಲುಮೆ", "ml": "ചൂള",
            "pa": "ਭੱਠੀ", "or": "ଚୁଲି"
        },
        "crane": {
            "en": "crane", "hi": "क्रेन", "bn": "ক্রেন",
            "ta": "கிரேன்", "te": "క్రేన్", "mr": "क्रेन",
            "gu": "ક્રેન", "kn": "ಕ್ರೇನ್", "ml": "ക്രെയിൻ",
            "pa": "ਕ੍ਰੇਨ", "or": "କ୍ରେନ୍"
        },
    }
    default = {
        "en": "equipment", "hi": "उपकरण", "bn": "সরঞ্জাম",
        "ta": "உபகரணம்", "te": "పరికరాలు", "mr": "उपकरण",
        "gu": "સાધન", "kn": "ಉಪಕರಣ", "ml": "ഉപകരണം",
        "pa": "ਉਪਕਰਨ", "or": "ଉପକରଣ"
    }
    return displays.get(eq or "", default)


def _select_adaptive_question(
    answered_count: int,
    prior_answers_en: list[str],
    already_asked_keys: set[str],
    lang: str,
) -> tuple[str, list[str], str] | None:
    """
    Select the most contextually relevant follow-up question based on
    what the worker answered in previous turns.

    Returns (question_text, options, adaptive_key) or None.
    """
    if not prior_answers_en:
        return None

    # Classify the most recent answer for adaptive branching
    last_answer = prior_answers_en[-1]
    ctx = _classify_answer_context(last_answer)

    # Also check cumulative context across all answers
    all_answers_text = " ".join(prior_answers_en).lower()
    cumulative_ctx = _classify_answer_context(all_answers_text)

    # Priority ordering: what's most urgent to ask next?
    priority_order = []

    if ctx["hazard_active"] and "active_hazard_followup" not in already_asked_keys:
        priority_order.append("active_hazard_followup")

    if ctx["workers_injured"] and "injury_followup" not in already_asked_keys:
        priority_order.append("injury_followup")

    if ctx["hazard_contained"] and "contained_followup" not in already_asked_keys:
        priority_order.append("contained_followup")

    # If we haven't asked about personnel count and workers are mentioned
    if (ctx["workers_present"] or cumulative_ctx["workers_present"]) and "personnel_count_followup" not in already_asked_keys:
        priority_order.append("personnel_count_followup")

    # Fallback: if hazard is active and we haven't asked evacuation
    if cumulative_ctx["hazard_active"] and "active_hazard_followup" not in already_asked_keys:
        if "active_hazard_followup" not in priority_order:
            priority_order.append("active_hazard_followup")

    # If nothing matched, try injury followup if not asked
    if not priority_order:
        for key in ["injury_followup", "personnel_count_followup", "contained_followup", "active_hazard_followup"]:
            if key not in already_asked_keys:
                priority_order.append(key)
                break

    if not priority_order:
        return None

    selected_key = priority_order[0]
    q_pool = _ADAPTIVE_QUESTIONS.get(selected_key)
    if not q_pool:
        return None

    q_text = q_pool["q_translations"].get(lang, q_pool["q_en"])
    opts = q_pool["opts_translations"].get(lang, q_pool["opts_en"])

    return q_text, opts, selected_key


def generate_rag_question(
    category: str,
    incident_description_en: str,
    prior_questions: list[str],
    prior_answers_en: list[str],
    zone_id: str | None = None,
    language: str = "en",
    raw_description: str = "",
) -> tuple[str, list[str], str, bool] | None:
    answered_count = len(prior_answers_en)
    if answered_count >= 4:
        return None

    lang = (language or "en").lower()
    ctx = extract_incident_context(
        incident_description_en,
        prior_questions,
        prior_answers_en,
        zone_id,
        raw_description=raw_description,
    )

    # 1. RAG retrieval for grounding citation metadata (UI badge)
    search_query = f"{category} {incident_description_en} {' '.join(prior_answers_en[-1:])}"
    chunks = rag.retrieve(search_query, incident_type=category, top_k=2)
    top_chunk = chunks[0] if chunks else None
    sop_title = top_chunk["doc_title"] if top_chunk else "Plant Safety Operating Procedure"

    # 2. Select category interview flow
    flow = CATEGORY_INTERVIEW_FLOWS.get(category) or CATEGORY_INTERVIEW_FLOWS.get("default")
    if not flow:
        return None

    eq_disp = _get_equipment_display(ctx["equipment"])
    eq_name = eq_disp.get(lang, eq_disp["en"])

    # 3. Dynamic equipment personalization on Turn 0 for gas leak, fire, or default
    if answered_count == 0 and ctx["equipment"]:
        if category == "gas_leak":
            q_en = f"Is the {eq_disp['en']} gas leak actively spreading, or safely shut off under isolation?"
            opts_en = [
                f"{eq_disp['en'].title()} safely shut off and isolated",
                f"Cannot access {eq_disp['en']} due to hazard",
                "Hazard actively ongoing / spreading",
                "Not sure of isolation status"
            ]
            q_translations = {
                "hi": f"क्या {eq_name} से गैस रिसाव अभी भी फैल रहा है, या सुरक्षित रूप से बंद/आइसोलेट कर दिया है?",
                "bn": f"{eq_name} থেকে গ্যাস লিক কি এখনও ছড়াচ্ছে, নাকি নিরাপদে বিচ্ছিন্ন/বন্ধ করা হয়েছে?",
                "ta": f"{eq_name}-ல் எரிவாயு கசிவு இன்னும் பரவுகிறதா, அல்லது பாதுகாப்பாக துண்டிக்கப்பட்டதா?",
                "te": f"{eq_name} నుండి గ్యాస్ లీక్ ఇంకా వ్యాపిస్తోందా, లేదా సురక్షితంగా ఐసోలేట్ చేశారా?",
                "mr": f"{eq_name} मधून गॅस गळती अजून पसरत आहे की सुरक्षितपणे बंद/वेगळी केली आहे?",
                "gu": f"શું {eq_name} માંથી ગેસ ગળતર હજી ફેલાઈ રહ્યું છે, કે સુરક્ષિત રીતે બંધ/અલગ કરી દીધું છે?",
                "kn": f"{eq_name} ನಿಂದ ಅನಿಲ ಸೋರಿಕೆ ಇನ್ನೂ ಹರಡುತ್ತಿದೆಯೇ, ಅಥವಾ ಸುರಕ್ಷಿತವಾಗಿ ಪ್ರತ್ಯೇಕಿಸಲಾಗಿದೆಯೇ?",
                "ml": f"{eq_name}-ൽ നിന്ന് വാതക ചോർച്ച ഇപ്പോഴും പടരുകയാണോ, അതോ സുരക്ഷിതമായി നിർത്തിയോ?",
                "pa": f"ਕੀ {eq_name} ਤੋਂ ਗੈਸ ਲੀਕ ਅਜੇ ਵੀ ਫੈਲ ਰਿਹਾ ਹੈ, ਜਾਂ ਸੁਰੱਖਿਅਤ ਢੰਗ ਨਾਲ ਬੰਦ ਕਰ ਦਿੱਤਾ ਹੈ?",
                "or": f"କ'ଣ {eq_name} ରୁ ଗ୍ୟାସ ଲିକ୍ ଏବେ ବି ବ୍ୟାପୁଛି, ନା ସୁରକ୍ଷିତ ଭାବେ ବନ୍ଦ କରାଯାଇଛି?",
            }
            opts_translations = {
                "hi": [f"{eq_name} सुरक्षित रूप से अलग/बंद कर दिया", f"खतरे के कारण {eq_name} तक पहुंच असंभव", "खतरा लगातार फैल रहा है", "स्थिति की पुष्टि नहीं"],
                "bn": [f"{eq_name} নিরাপদে বিচ্ছিন্ন/বন্ধ করা হয়েছে", f"বিপদের কারণে {eq_name} নাগালের বাইরে", "বিপদ ক্রমাগত ছড়িয়ে পড়ছে", "অবস্থা নিশ্চিত নয়"],
                "ta": [f"{eq_name} பாதுகாப்பாக தனிமைப்படுத்தப்பட்டது", f"ஆபத்து காரணமாக {eq_name}-ஐ அணுக முடியவில்லை", "ஆபத்து தொடர்ந்து பரவுகிறது", "நிலைமை உறுதியாக தெரியவில்லை"],
                "te": [f"{eq_name} సురక్షితంగా ఐసోలేట్ చేశారు", f"ప్రమాదం వల్ల {eq_name} వద్దకు వెళ్లలేము", "ప్రమాదం ఇంకా వ్యాపిస్తోంది", "పరిస్థితి ఖచ్చితంగా తెలియదు"],
                "mr": [f"{eq_name} सुरक्षितपणे वेगळे/बंद केले", f"धोक्यामुळे {eq_name} जवळ जाता येत नाही", "धोका सतत पसरत आहे", "खात्री नाही"],
                "gu": [f"{eq_name} સુરક્ષિત રીતે અલગ/બંધ કર્યું", f"જોખમને કારણે {eq_name} સુધી પહોંચી શકાતું નથી", "જોખમ સતત ફેલાઈ રહ્યું છે", "સ્થિતિની ખાતરી નથી"],
                "kn": [f"{eq_name} ಸುರಕ್ಷಿತವಾಗಿ ಪ್ರತ್ಯೇಕಿಸಲಾಗಿದೆ", f"ಅಪಾಯದಿಂದಾಗಿ {eq_name} ತಲುಪಲು ಸಾಧ್ಯವಿಲ್ಲ", "ಅಪಾಯವು ಮುಂದುವರಿಯುತ್ತಿದೆ", "ಖಚಿತವಿಲ್ಲ"],
                "ml": [f"{eq_name} സുരക്ഷിതമായി ഒറ്റപ്പെടുത്തി", f"അപകടം കാരണം {eq_name} സമീപിക്കാൻ കഴിയില്ല", "അപകടം തുടരുന്നു", "ഉറപ്പില്ല"],
                "pa": [f"{eq_name} ਸੁਰੱਖਿਅਤ ਢੰਗ ਨਾਲ ਅਲੱਗ/ਬੰਦ ਕੀਤਾ", f"ਖ਼ਤਰੇ ਕਾਰਨ {eq_name} ਤੱਕ ਨਹੀਂ ਪਹੁੰਚਿਆ ਜਾ ਸਕਦਾ", "ਖ਼ਤਰਾ ਲਗਾਤਾਰ ਜਾਰੀ ਹੈ", "ਪੱਕਾ ਪਤਾ ਨਹੀਂ"],
                "or": [f"{eq_name} ସୁରକ୍ଷିତ ଭାବେ ପୃଥକ କରାଯାଇଛି", f"ବିପଦ ହେତୁ {eq_name} ପାଖକୁ ଯାଇହେଉନାହିଁ", "ବିପଦ ଲଗାତାର ବ୍ୟାପୁଛି", "ନିଶ୍ଚିତ ନୁହେଁ"],
            }
            return (
                q_translations.get(lang, q_en),
                opts_translations.get(lang, opts_en),
                sop_title,
                True,
            )
        elif category == "fire":
            q_en = f"Is the {eq_disp['en']} fire actively spreading, or safely contained?"
            opts_en = [
                f"{eq_disp['en'].title()} fire contained / suppressed",
                f"Cannot access {eq_disp['en']} due to flames/smoke",
                "Fire actively spreading to surroundings",
                "Fire status unconfirmed"
            ]
            q_translations = {
                "hi": f"क्या {eq_name} की आग फैल रही है, या सुरक्षित रूप से नियंत्रित कर ली गई है?",
                "bn": f"{eq_name}-এর আগুন কি ছড়াচ্ছে, নাকি নিরাপদে নিয়ন্ত্রণে আনা হয়েছে?",
                "ta": f"{eq_name}-ல் தீ பரவுகிறதா, அல்லது பாதுகாப்பாக கட்டுப்படுத்தப்பட்டதா?",
                "te": f"{eq_name} వద్ద మంటలు వ్యాపిస్తున్నాయా, లేదా అదుపులోకి వచ్చాయా?",
                "mr": f"{eq_name} ची आग पसरत आहे की सुरक्षितपणे आटोक्यात आणली आहे?",
                "gu": f"શું {eq_name} ની આગ ફેલાઈ રહી છે, કે સુરક્ષિત રીતે નિયંત્રિત કરી લીધી છે?",
                "kn": f"{eq_name} ಬೆಂಕಿ ಹರಡುತ್ತಿದೆಯೇ, ಅಥವಾ ಸುರಕ್ಷಿತವಾಗಿ ನಿಯಂತ್ರಿಸಲಾಗಿದೆಯೇ?",
                "ml": f"{eq_name}-ലെ തീ പടരുകയാണോ, അതോ നിയന്ത്രണവിധേയമാക്കിയോ?",
                "pa": f"ਕੀ {eq_name} ਦੀ ਅੱਗ ਫੈਲ ਰਹੀ ਹੈ, ਜਾਂ ਸੁਰੱਖਿਅਤ ਢੰਗ ਨਾਲ ਕਾਬੂ ਕਰ ਲਈ ਹੈ?",
                "or": f"କ'ଣ {eq_name} ର ନିଆଁ ବ୍ୟାପୁଛି, ନା ସୁରକ୍ଷିତ ଭାବେ ନିୟନ୍ତ୍ରଣ କରାଯାଇଛି?",
            }
            opts_translations = {
                "hi": [f"{eq_name} की आग नियंत्रित / बुझा दी गई", f"लपटों/धुएं के कारण {eq_name} तक पहुंच असंभव", "आग आसपास के क्षेत्र में तेजी से फैल रही है", "आग की स्थिति की पुष्टि नहीं"],
                "bn": [f"{eq_name}-এর আগুন নিয়ন্ত্রণে / নিভিয়ে ফেলা হয়েছে", f"আগুন/ধোঁয়ার কারণে {eq_name} নাগালের বাইরে", "আগুন দ্রুত চারপাশে ছড়িয়ে পড়ছে", "আগুনের অবস্থা নিশ্চিত নয়"],
                "ta": [f"{eq_name} தீ கட்டுப்படுத்தப்பட்டது / அணைக்கப்பட்டது", f"புகை/தீ காரணமாக {eq_name}-ஐ அணுக முடியவில்லை", "தீ சுற்றியுள்ள பகுதிக்கு வேகமாக பரவுகிறது", "நிலைமை உறுதியாக தெரியவில்லை"],
                "te": [f"{eq_name} మంటలు అదుపులోకి వచ్చాయి / ఆర్పేశారు", f"మంటలు/పొగ వల్ల {eq_name} వద్దకు వెళ్లలేము", "మంటలు చుట్టుపక్కలకు వేగంగా వ్యాపిస్తున్నాయి", "పరిస్థితి ఖచ్చితంగా తెలియదు"],
                "mr": [f"{eq_name} ची आग आटोक्यात / विझवली", f"ज्वाळा/धुरामुळे {eq_name} जवळ जाता येत नाही", "आग आजूबाजूला वेगाने पसरत आहे", "खात्री नाही"],
                "gu": [f"{eq_name} ની આગ નિયંત્રિત / બુઝાવી દીધી", f"જ્વાળાઓ/ધુમાડાને કારણે {eq_name} સુધી પહોંચી શકાતું નથી", "આગ આસપાસમાં ઝડપથી ફેલાઈ રહી છે", "સ્થિતિની ખાતરી નથી"],
                "kn": [f"{eq_name} ಬೆಂಕಿ ನಿಯಂತ್ರಣದಲ್ಲಿದೆ / ನಂದಿಸಲಾಗಿದೆ", f"ಜ್ವಾಲೆಗಳಿಂದ {eq_name} ತಲುಪಲು ಸಾಧ್ಯವಿಲ್ಲ", "ಬೆಂಕಿ ಸುತ್ತಮುತ್ತ ವೇಗವಾಗಿ ಹರಡುತ್ತಿದೆ", "ಖಚಿತವಿಲ್ಲ"],
                "ml": [f"{eq_name}-ലെ തീ നിയന്ത്രണവിധേയമാക്കി / അണച്ചു", f"തീ കാരണം {eq_name} സമീപിക്കാൻ കഴിയില്ല", "തീ ചുറ്റുപാടും പടരുന്നു", "ഉറപ്പില്ല"],
                "pa": [f"{eq_name} ਦੀ ਅੱਗ ਕਾਬੂ ਹੇਠ / ਬੁਝਾ ਦਿੱਤੀ ਗਈ", f"ਲਪਟਾਂ ਕਾਰਨ {eq_name} ਤੱਕ ਪਹੁੰਚਣਾ ਅਸੰਭਵ", "ਅੱਗ ਆਲੇ-ਦੁਆਲੇ ਤੇਜ਼ੀ ਨਾਲ ਫੈਲ ਰਹੀ ਹੈ", "ਪੱਕਾ ਪਤਾ ਨਹੀਂ"],
                "or": [f"{eq_name} ନିଆଁ ନିୟନ୍ତ୍ରିତ / ଲିଭାଯାଇଛି", f"ଅଗ୍ନି ହେତୁ {eq_name} ପାଖକୁ ଯାଇହେଉନାହିଁ", "ନିଆଁ ଚାରିଆଡ଼େ ବ୍ୟାପୁଛି", "ନିଶ୍ଚିତ ନୁହେଁ"],
            }
            return (
                q_translations.get(lang, q_en),
                opts_translations.get(lang, opts_en),
                sop_title,
                True,
            )

    # 4. Answer-adaptive branching for turns 1-3
    if answered_count >= 1 and prior_answers_en:
        # Track which adaptive questions have already been asked
        already_asked_keys: set[str] = set()
        # We can infer what adaptive keys were used by checking question text patterns
        for pq in prior_questions:
            pq_low = pq.lower() if pq else ""
            if "evacuat" in pq_low or "danger zone" in pq_low or "खतरे वाले" in pq_low:
                already_asked_keys.add("active_hazard_followup")
            if "injur" in pq_low or "burn" in pq_low or "fracture" in pq_low or "घायल" in pq_low:
                already_asked_keys.add("injury_followup")
            if "when was" in pq_low or "isolat" in pq_low or "before containment" in pq_low or "कब आइसोलेट" in pq_low:
                already_asked_keys.add("contained_followup")
            if "how many" in pq_low or "control room" in pq_low or "कितने कर्मचारी" in pq_low:
                already_asked_keys.add("personnel_count_followup")

        adaptive = _select_adaptive_question(
            answered_count=answered_count,
            prior_answers_en=prior_answers_en,
            already_asked_keys=already_asked_keys,
            lang=lang,
        )
        if adaptive:
            q_text, opts, _ = adaptive
            return (q_text, opts, sop_title, True)

    # 5. Standard category flow question and options (fallback)
    if answered_count >= len(flow):
        return None

    turn = flow[answered_count]
    q_text = turn["q_translations"].get(lang, turn["q_en"])
    opts = turn["opts_translations"].get(lang, turn["opts_en"])

    return (q_text, opts, sop_title, True)
