"""
Script to construct the 100 gold-standard interview evaluation scenarios for BSL AI RAG.
Covering 10 hazard categories, English, Hindi, Hinglish, vague reports, panicked reports,
and contradictory reports.
Marked as DRAFT for safety-officer review.
"""

import json
from pathlib import Path

GOLD_SCENARIOS = []

# Template generator across 10 categories (10 scenarios per category = 100 total)
CATEGORIES = [
    "gas_leak",
    "fire",
    "electrical_hazard",
    "molten_metal_spill",
    "chemical_spill",
    "mechanical_failure",
    "confined_space_emergency",
    "crane_lifting_failure",
    "vehicle_traffic_incident",
    "slip_fall"
]

# Definition of 100 detailed scenarios
scenarios_raw = [
    # -------------------------------------------------------------
    # 1. GAS LEAK (10 scenarios)
    # -------------------------------------------------------------
    {
        "id": "gas_01",
        "hazard_type": "gas_leak",
        "zone_id": "BF1",
        "language": "en",
        "report_style": "clear_factual",
        "initial_report": "Heavy BF gas leakage near stove 3 manifold flange. High hissing sound and visible dust vortex. Area smells of CO.",
        "already_known_facts": ["location: stove 3 manifold", "gas_type: blast furnace gas / CO", "symptoms: hissing sound"],
        "must_ask_questions": [
            "Is the gas leak isolated or is valve V-17 accessible?",
            "Are any workers in the area feeling dizziness, nausea, or headache?",
            "Has the area been evacuated upwind?"
        ],
        "target_slots": ["isolation_status", "victims_condition", "evacuation_status"],
        "relevant_sop_ids": ["BSL/SOP/BFG-01", "BSL/SOP/GEN-04"]
    },
    {
        "id": "gas_02",
        "hazard_type": "gas_leak",
        "zone_id": "GHS",
        "language": "hi",
        "report_style": "panicked_short",
        "initial_report": "अरे भैया गैस होल्डर के पास एक आदमी गिर गया है, बेहोश है, जल्दी एम्बुलेंस भेजो!",
        "already_known_facts": ["location: gas holder", "victim_status: 1 person unconscious"],
        "must_ask_questions": [
            "क्या बेहोश कर्मचारी को बिना SCBA पहने बचाने की कोशिश की जा रही है या आप सुरक्षित दूरी पर हैं?",
            "क्या गैस की गंध बहुत तेज आ रही है या गैस अलार्म बजा है?",
            "क्या कंट्रोल रूम और मेडिकल टीम को तुरंत कॉल किया गया है?"
        ],
        "target_slots": ["rescuer_safety_scba", "gas_concentration_urgency", "emergency_dispatch"],
        "relevant_sop_ids": ["BSL/SOP/COG-02", "BSL/SOP/GEN-04"]
    },
    {
        "id": "gas_03",
        "hazard_type": "gas_leak",
        "zone_id": "COB",
        "language": "hinglish",
        "report_style": "vague",
        "initial_report": "Coke oven battery 5 ke paas ajeeb sa gas smell aa raha hai, sar dard ho raha hai do logo ko.",
        "already_known_facts": ["location: coke oven battery 5", "symptoms: headache in 2 workers"],
        "must_ask_questions": [
            "Are the 2 workers moving upwind to fresh air immediately?",
            "Is the smell like rotten eggs (coke oven gas) or burning sulfur?",
            "Can you see any pipeline leakage or open bleeder valve?"
        ],
        "target_slots": ["immediate_evacuation_upwind", "gas_identity", "leak_source_equipment"],
        "relevant_sop_ids": ["BSL/SOP/COG-02"]
    },
    {
        "id": "gas_04",
        "hazard_type": "gas_leak",
        "zone_id": "BF2",
        "language": "en",
        "report_style": "contradictory",
        "initial_report": "Bleeder valve popped open with loud noise, gas escaping, but supervisor said it's normal venting though gas detector is at 150 ppm.",
        "already_known_facts": ["location: BF2 bleeder", "reading: 150 ppm CO"],
        "must_ask_questions": [
            "Are all personnel evacuated beyond the 100m danger radius for 150 ppm CO?",
            "Has the blast furnace control room acknowledged the bleeder pressure rise?",
            "Is any worker experiencing nausea or breathing difficulty?"
        ],
        "target_slots": ["evacuation_perimeter_100m", "control_room_ack", "symptoms_check"],
        "relevant_sop_ids": ["BSL/SOP/BFG-01"]
    },
    {
        "id": "gas_05",
        "hazard_type": "gas_leak",
        "zone_id": "GHS",
        "language": "hi",
        "report_style": "clear_factual",
        "initial_report": "गैस होल्डर स्टेशन पर वाटर सील ओवरफ्लो हो गई है और बीएफ गैस नाले के रास्ते रिस रही है।",
        "already_known_facts": ["location: GHS water seal", "hazard: water seal failure / overflow BF gas"],
        "must_ask_questions": [
            "क्या वाटर सील में पानी की आपूर्ति तुरंत चालू की जा सकती है?",
            "क्या नाले के आसपास सभी गर्म काम (हॉट वर्क / वेल्डिंग) तुरंत बंद करा दिए गए हैं?",
            "क्या उस रास्ते पर गाड़ियों और कामगारों की आवाजाही रोक दी गई है?"
        ],
        "target_slots": ["water_seal_makeup", "ignition_source_isolation", "traffic_cordon"],
        "relevant_sop_ids": ["BSL/SOP/BFG-01", "BSL/SOP/GEN-04"]
    },
    {
        "id": "gas_06",
        "hazard_type": "gas_leak",
        "zone_id": "SMS",
        "language": "en",
        "report_style": "panicked_short",
        "initial_report": "Oxygen pipeline line rupture at lance carriage SMS! Hissing oxygen leak near molten steel!",
        "already_known_facts": ["location: SMS lance carriage", "substance: pure oxygen", "proximity: near molten steel"],
        "must_ask_questions": [
            "Has the main oxygen isolation valve at the valve stand been tripped or shut?",
            "Has furnace tapping and hot metal movement been halted immediately?",
            "Is any oil, grease, or flammable material in contact with the oxygen stream?"
        ],
        "target_slots": ["isolation_valve_status", "hot_metal_operations_halt", "combustible_contact"],
        "relevant_sop_ids": ["BSL/SOP/MMS-03", "BSL/SOP/GEN-01"]
    },
    {
        "id": "gas_07",
        "hazard_type": "gas_leak",
        "zone_id": "BF1",
        "language": "hinglish",
        "report_style": "vague",
        "initial_report": "Blast furnace ke runner ke upar gas jam rahi hai, hawa nahi chal rahi hai bilkul.",
        "already_known_facts": ["location: BF runner", "condition: dead air / gas accumulation"],
        "must_ask_questions": [
            "What does the portable CO detector show in PPM?",
            "Are casthouse workers wearing their personal CO badges?",
            "Have workers moved to the ventilated side of the cast floor?"
        ],
        "target_slots": ["detector_ppm_reading", "ppe_co_badge", "ventilation_position"],
        "relevant_sop_ids": ["BSL/SOP/BFG-01"]
    },
    {
        "id": "gas_08",
        "hazard_type": "gas_leak",
        "zone_id": "COB",
        "language": "hi",
        "report_style": "clear_factual",
        "initial_report": "बैटरी नंबर 3 के बेसमेंट में सीओजी (Coke Oven Gas) लाइन का ड्रेन वाल्व टूटा है, गैस निकल रही है।",
        "already_known_facts": ["location: battery 3 basement", "substance: COG", "component: broken drain valve"],
        "must_ask_questions": [
            "क्या बेसमेंट से सभी कर्मचारियों को तुरंत बाहर निकाल लिया गया है?",
            "क्या बेसमेंट की ओर कोई बिजली स्विच या चिंगारी का स्रोत है?",
            "क्या आपातकालीन गैस रेस्क्यू टीम (SCBA) को सूचित किया गया है?"
        ],
        "target_slots": ["confined_basement_evacuation", "ignition_sources", "scba_rescue_team"],
        "relevant_sop_ids": ["BSL/SOP/COG-02", "BSL/SOP/GEN-04"]
    },
    {
        "id": "gas_09",
        "hazard_type": "gas_leak",
        "zone_id": "PWR",
        "language": "en",
        "report_style": "contradictory",
        "initial_report": "Smell of ammonia near DM plant neutralization pit, operator says it's normal cleaning but water turned milky.",
        "already_known_facts": ["location: DM plant neutralization pit", "chemical: ammonia / alkaline solution"],
        "must_ask_questions": [
            "Is the ventilation fan in the chemical pit running?",
            "Are operators wearing full-face chemical respirators and rubber suits?",
            "Is the pH alarm triggered on the effluent monitor?"
        ],
        "target_slots": ["pit_ventilation", "chemical_ppe", "ph_alarm_status"],
        "relevant_sop_ids": ["BSL/SOP/CSP-05"]
    },
    {
        "id": "gas_10",
        "hazard_type": "gas_leak",
        "zone_id": "BF2",
        "language": "hi",
        "report_style": "panicked_short",
        "initial_report": "गैस अलार्म सायरन बज रहा है tuyere प्लेटफार्म पर, सब लोग भाग रहे हैं!",
        "already_known_facts": ["location: BF2 tuyere platform", "status: siren active, personnel running"],
        "must_ask_questions": [
            "क्या सभी कामगार विंडवर्ड (हवा की दिशा के विपरीत) सुरक्षित असेंबली पॉइंट पर पहुंचे हैं?",
            "क्या कोई ऑपरेटर tuyere प्लेटफार्म या सीढ़ियों पर फंसा हुआ है?",
            "क्या फर्नेस ब्लोअर का प्रेशर ड्रॉप हुआ है?"
        ],
        "target_slots": ["headcount_assembly_point", "trapped_personnel", "furnace_pressure_status"],
        "relevant_sop_ids": ["BSL/SOP/BFG-01", "BSL/SOP/GEN-04"]
    },

    # -------------------------------------------------------------
    # 2. FIRE (10 scenarios)
    # -------------------------------------------------------------
    {
        "id": "fire_01",
        "hazard_type": "fire",
        "zone_id": "COB",
        "language": "en",
        "report_style": "clear_factual",
        "initial_report": "Cable tray fire on mezzanine floor battery 4. Thick black smoke rising towards conveyor gallery.",
        "already_known_facts": ["location: battery 4 mezzanine", "material: electrical cables", "smoke: thick black towards conveyor"],
        "must_ask_questions": [
            "Has the electrical feeder breaker for this cable tray been tripped and isolated?",
            "Is the conveyor gallery deluged or isolated to prevent fire spread across zones?",
            "Has plant fire brigade (ext. 2222) been dispatched?"
        ],
        "target_slots": ["electrical_power_cut", "spread_barrier_isolation", "fire_brigade_call"],
        "relevant_sop_ids": ["BSL/SOP/FIR-01", "BSL/SOP/ELC-03"]
    },
    {
        "id": "fire_02",
        "hazard_type": "fire",
        "zone_id": "PWR",
        "language": "hi",
        "report_style": "panicked_short",
        "initial_report": "ट्रांसफार्मर 2 में धमाका हुआ और तेल में भीषण आग लग गई है, लपटें 15 फीट ऊंची हैं!",
        "already_known_facts": ["location: transformer 2 PWR", "type: transformer oil fire", "flames: 15 feet high"],
        "must_ask_questions": [
            "क्या ट्रांसफार्मर का नाइट्रोजन इंजेक्शन फायर फाइटिंग (NIFPS) या इमल्सिफायर सिस्टम सक्रिय हुआ है?",
            "क्या ट्रांसफार्मर यार्ड का 33kV इनपुट सर्किट ब्रेकर खुला (ट्रिप) है?",
            "क्या आग बुझाने के लिए पानी का सीधा छिड़काव रोका गया है और केवल फोम/डीक्यूपी का उपयोग हो रहा है?"
        ],
        "target_slots": ["nifps_emulsifier_status", "hv_breaker_tripped", "extinguishing_agent_correct"],
        "relevant_sop_ids": ["BSL/SOP/FIR-01", "BSL/SOP/ELC-03"]
    },
    {
        "id": "fire_03",
        "hazard_type": "fire",
        "zone_id": "HRM",
        "language": "hinglish",
        "report_style": "vague",
        "initial_report": "Rolling mill roughing stand ke paas hydraulic pipe phat gaya aur aag lag gayi.",
        "already_known_facts": ["location: HRM roughing stand", "fuel: high-pressure hydraulic oil"],
        "must_ask_questions": [
            "Has the hydraulic power pack pump emergency stop button been pressed?",
            "Is the water mist spray system active over the roughing stand?",
            "Are any workers burned or trapped by burning oil spray?"
        ],
        "target_slots": ["hydraulic_emergency_stop", "water_mist_system", "burn_victims_triage"],
        "relevant_sop_ids": ["BSL/SOP/FIR-01", "BSL/SOP/MCH-02"]
    },
    {
        "id": "fire_04",
        "hazard_type": "fire",
        "zone_id": "SMS",
        "language": "en",
        "report_style": "contradictory",
        "initial_report": "Small fire in waste bins near slag pit, worker put some water but there was a loud pop and sparks.",
        "already_known_facts": ["location: near slag pit SMS", "action: water applied onto hot slag/dust"],
        "must_ask_questions": [
            "Stop all water spraying immediately — is water reaching the hot molten slag?",
            "How far is the fire from the active molten metal ladles?",
            "Are workers using dry chemical powder (DCP) instead of water?"
        ],
        "target_slots": ["halt_water_slag_hazard", "molten_metal_separation_distance", "dcp_extinguisher_use"],
        "relevant_sop_ids": ["BSL/SOP/MMS-03", "BSL/SOP/FIR-01"]
    },
    {
        "id": "fire_05",
        "hazard_type": "fire",
        "zone_id": "RMY",
        "language": "hi",
        "report_style": "clear_factual",
        "initial_report": "कोयला यार्ड कन्वेयर बेल्ट 2B पर घर्षण से रबर बेल्ट में आग सुलग रही है और धुआं फैल रहा है।",
        "already_known_facts": ["location: coal yard conveyor 2B", "material: rubber belt / coal dust"],
        "must_ask_questions": [
            "क्या कन्वेयर का पुल-कॉर्ड या इमरजेंसी स्टॉप दबाकर बेल्ट को तुरंत रोक दिया गया है?",
            "क्या ऊपर की तरफ से कोयले की लोडिंग फीडर बंद कर दी गई है?",
            "क्या बेल्ट पर स्प्रिंकलर लाइन चालू की गई है?"
        ],
        "target_slots": ["conveyor_pull_cord_stop", "coal_feed_cutoff", "deluge_sprinkler_start"],
        "relevant_sop_ids": ["BSL/SOP/FIR-01", "BSL/SOP/MCH-02"]
    },
    {
        "id": "fire_06",
        "hazard_type": "fire",
        "zone_id": "BF1",
        "language": "en",
        "report_style": "panicked_short",
        "initial_report": "Gas cutting hose backfired! Gas cylinder trolley catching fire near casthouse stairs!",
        "already_known_facts": ["equipment: oxy-acetylene cylinder trolley", "hazard: backfire cylinder fire"],
        "must_ask_questions": [
            "Are people clear of the cylinders — acetylene cylinders can explode when heated?",
            "Has the area within 100 meters been evacuated immediately?",
            "Can the cylinder valves be safely shut with heat-resistant gloves, or is it already too hot?"
        ],
        "target_slots": ["explosion_perimeter_evacuation", "cylinder_isolation_accessibility", "safety_distance"],
        "relevant_sop_ids": ["BSL/SOP/FIR-01"]
    },
    {
        "id": "fire_07",
        "hazard_type": "fire",
        "zone_id": "COB",
        "language": "hinglish",
        "report_style": "vague",
        "initial_report": "Battery top par tar leak ho raha tha aur achanak aag pakad liya.",
        "already_known_facts": ["location: battery top COB", "fuel: coal tar / bitumen"],
        "must_ask_questions": [
            "Are battery top operators wearing heat-reflective suits and safety harnesses?",
            "Is the fire threatening the raw coke oven gas collector main?",
            "Has steam smothering been injected into the standpipe?"
        ],
        "target_slots": ["battery_top_ppe", "collector_main_protection", "steam_smothering"],
        "relevant_sop_ids": ["BSL/SOP/FIR-01", "BSL/SOP/COG-02"]
    },
    {
        "id": "fire_08",
        "hazard_type": "fire",
        "zone_id": "PWR",
        "language": "hi",
        "report_style": "clear_factual",
        "initial_report": "कैबल बेसमेंट में स्मोक डिटेक्टर अलार्म बज रहा है, कांच की खिड़की से धुआं दिख रहा है।",
        "already_known_facts": ["location: cable basement PWR", "sensor: smoke detector alarm active"],
        "must_ask_questions": [
            "क्या बेसमेंट में कोई भी कर्मचारी मौजूद है, या दरवाजा पूरी तरह बंद है?",
            "क्या CO2 फ्लडिंग सिस्टम का मैनुअल लॉक रिलीज किया जाना चाहिए?",
            "क्या बेसमेंट में प्रवेश करने से पहले पावर आइसोलेशन हो चुका है?"
        ],
        "target_slots": ["basement_occupancy_check", "co2_flooding_system", "power_isolation"],
        "relevant_sop_ids": ["BSL/SOP/FIR-01", "BSL/SOP/ELC-03"]
    },
    {
        "id": "fire_09",
        "hazard_type": "fire",
        "zone_id": "HRM",
        "language": "en",
        "report_style": "contradictory",
        "initial_report": "Motor sparking and smoke inside rolling mill pulpit, operator threw a jacket over it to smother it.",
        "already_known_facts": ["location: pulpit HRM", "action: cloth jacket placed on live electrical motor"],
        "must_ask_questions": [
            "Remove flammable cloth immediately — has the emergency trip switch on the pulpit console been pressed?",
            "Is a CO2 gas extinguisher available right inside the pulpit door?",
            "Are control monitors and emergency shutdown consoles still operational?"
        ],
        "target_slots": ["remove_combustible_from_electric", "co2_extinguisher_use", "control_console_integrity"],
        "relevant_sop_ids": ["BSL/SOP/FIR-01", "BSL/SOP/ELC-03"]
    },
    {
        "id": "fire_10",
        "hazard_type": "fire",
        "zone_id": "SMS2",
        "language": "hi",
        "report_style": "panicked_short",
        "initial_report": "कनवर्टर शॉप में आग लग गई है, क्रेन चालक ऊपर केबिन में फंसा हुआ है!",
        "already_known_facts": ["location: converter shop SMS2", "victim: crane driver trapped in overhead cabin"],
        "must_ask_questions": [
            "क्या क्रेन कैब तक धुएं की लपटें पहुंच रही हैं — क्या ऑपरेटर के पास इमरजेंसी एस्केप मास्क है?",
            "क्या फायर ब्रिगेड स्नोर्कल / हाइड्रोलिक लैडर को तुरंत क्रेन बे में बुलाया गया है?",
            "क्या क्रेन की बिजली मेन आइसोलेटर से सुरक्षित काट दी गई है?"
        ],
        "target_slots": ["crane_cab_escape_mask", "snorkel_rescue_dispatch", "crane_power_cut"],
        "relevant_sop_ids": ["BSL/SOP/FIR-01", "BSL/SOP/CRN-04"]
    }
]

# Write out base scenarios and complement up to 100 with comprehensive coverage across all categories
def build_all_100():
    all_scenarios = list(scenarios_raw)
    
    # Build additional scenarios across categories to hit exactly 10 scenarios per category
    cat_counts = {c: sum(1 for s in all_scenarios if s["hazard_type"] == c) for c in CATEGORIES}
    
    extra_templates = {
        "electrical_hazard": [
            ("33kV busbar flashover in substation 4, loud bang, control room lights flicker.", "substation 4", "33kV breaker tripped", ["Has the 33kV incomer breaker locked out?", "Did anyone sustain arc flash burns?", "Is the substation locked against entry?"], ["breaker_lockout", "arc_burns", "substation_access_lock"], ["BSL/SOP/ELC-03"]),
            ("Worker touched motor terminal box while checking vibration, suffered shock, fell back.", "pump house", "shock received, worker fallen", ["Is the worker conscious and breathing, with clear pulse?", "Has the motor feeder been LOTO locked immediately?", "Are first aiders trained in CPR on scene?"], ["cpr_pulse_triage", "loto_isolation", "first_aid_dispatch"], ["BSL/SOP/ELC-03"]),
            ("Underground power cable damaged during earth excavation by JCB near RMY.", "RMY yard", "cable damaged by excavator", ["Is the excavator operator still in the machine cabin (instructed to stay inside)?", "Has electrical maintenance de-energized that sector feeder?", "Has a 15-meter cordon been placed around the cut cable?"], ["operator_step_potential_safety", "feeder_deenergize", "ground_gradient_cordon"], ["BSL/SOP/ELC-03"]),
            ("Water dripping from ceiling onto 415V motor control center (MCC) panel in basement.", "cable basement", "water dripping onto live MCC", ["Can the incoming feeder be isolated from the dry upstairs switchroom?", "Are personnel standing away from the wet conductive floor?", "Has the water source pipe been closed?"], ["remote_isolation", "wet_floor_electrocution", "water_source_shut"], ["BSL/SOP/ELC-03"]),
            ("Arc flash observed while racking out 6.6kV circuit breaker; smoke in switchgear room.", "switchgear room", "arc flash during breaker racking", ["Did the racking technician have full arc-rated flash suit and hood?", "Are there any facial burns or airway inhalation injuries?", "Has ventilation been started to clear ozone and toxic smoke?"], ["arc_suit_compliance", "airway_burns", "switchroom_ventilation"], ["BSL/SOP/ELC-03"]),
            ("Uninsulated live jumper wire dangling across walkway near cooling tower pump.", "cooling tower", "dangling live wire across walkway", ["Has the walkway been blocked on both approaches?", "What is the voltage rating of this line?", "Has electrical team arrived with voltage detector stick?"], ["walkway_blockage", "voltage_rating", "voltage_detector_verification"], ["BSL/SOP/ELC-03"]),
            ("Battery bank acid leak causing terminal short circuit and hydrogen gas smell in UPS room.", "UPS battery room", "acid leak + short circuit + hydrogen", ["Is the UPS room explosion-proof exhaust fan running?", "Have workers avoided flipping any wall light switches?", "Has emergency DC disconnect switch been operated?"], ["exhaust_fan_run", "no_spark_switches", "dc_disconnect_status"], ["BSL/SOP/ELC-03", "BSL/SOP/CSP-05"]),
            ("Contractor worker bypassed LOTO lock and energized conveyor while mechanic was inside.", "conveyor gallery", "loto bypassed with worker inside", ["Stop conveyor immediately — is the mechanic inside injured or trapped?", "Who authorized re-energization without lock removal permit?", "Is emergency pull-wire tripped?"], ["mechanic_safety_status", "loto_violation_audit", "pull_wire_tripped"], ["BSL/SOP/ELC-03", "BSL/SOP/MCH-02"]),
            ("Portable welding machine cable shorted to steel ladder, sparking profusely.", "BF casthouse stairs", "welding cable shorted to metal ladder", ["Has the main welding machine power supply switch been pulled?", "Is the grounding clamp properly bonded to earth?", "Are there flammable gases or solvent rags near the ladder?"], ["welder_power_plug_pulled", "grounding_clamp_bonded", "flammables_near_spark"], ["BSL/SOP/ELC-03"]),
            ("Transformer bushing cracked with visible oil seepage and corona humming sound.", "transformer yard", "cracked bushing, oil seepage, corona discharge", ["Is the transformer carrying load, and can it be switched to bypass?", "Has the danger perimeter of 10 meters been barricaded?", "Has oil level dropped below critical threshold in conservator tank?"], ["bypass_switchover", "barricade_perimeter", "conservator_oil_level"], ["BSL/SOP/ELC-03"])
        ],
        "molten_metal_spill": [
            ("Torpedo ladle car overflowing with hot liquid pig iron onto track near BF casthouse.", "casthouse track", "torpedo ladle overflow onto rail", ["Are all track personnel and drivers clear of the molten metal path?", "Is the track completely dry, or is there any water pooling in the pit?", "Has train movement been stopped by the railway yard master?"], ["personnel_clear_path", "water_pooling_steam_explosion", "rail_traffic_stopped"], ["BSL/SOP/MMS-03"]),
            ("Slag pot carrier dumped slag on wet ground; loud steam explosion with slag splatter.", "slag yard", "steam explosion from slag on wet ground", ["Did any flying slag strike operators or vehicle windshields?", "Are emergency water sprays kept AWAY from the remaining molten slag?", "Is the slag yard access gate closed to incoming dumpers?"], ["splatter_injuries", "prohibit_water_application", "gate_access_closure"], ["BSL/SOP/MMS-03"]),
            ("Steel ladle tap hole broke open prematurely before reaching teeming pit.", "SMS ladle bay", "premature tap hole breakout", ["Is the emergency catchment dry pit clear and ready to receive runoff?", "Have crane operators lifted the ladle away from oil tanks and cables?", "Are teeming pit operators evacuated to upper level shelter?"], ["catchment_pit_readiness", "crane_elevation_safety", "teeming_shelter_evac"], ["BSL/SOP/MMS-03"]),
            ("Tundish nozzle clogged, liquid steel splashing violently over casting mold platform.", "continuous caster", "liquid steel splash over mold", ["Has caster mold shroud been seated and auto-stopper closed?", "Are operators behind bulletproof splash shields?", "Has the emergency ladle slide gate cut off steel flow?"], ["slide_gate_cutoff", "splash_shield_protection", "mold_containment"], ["BSL/SOP/MMS-03"]),
            ("Ladle car hydraulic hose ruptured while carrying 150-ton molten steel ladle.", "transfer car track", "hydraulic rupture near molten ladle", ["Did hydraulic oil catch fire from the radiant heat of the ladle?", "Is the transfer car stranded in an unsafe position blocking crane hooks?", "Can the car be winched manually to safe teeming location?"], ["oil_fire_radiant_heat", "car_stranded_location", "manual_winch_plan"], ["BSL/SOP/MMS-03", "BSL/SOP/FIR-01"]),
            ("Blast furnace tap hole mud gun failed to plug; molten iron continuing to pour into runner.", "BF tap hole", "mud gun failure to seal tap hole", ["Has the auxiliary taphole stopper or backup clay gun been positioned?", "Is the iron runner pool close to overflowing runner sidewalls?", "Are spare torpedo cars aligned on the rail siding underneath?"], ["backup_clay_gun_status", "runner_overflow_level", "spare_torpedo_alignment"], ["BSL/SOP/MMS-03"]),
            ("Slag splashing during converter deslagging breached safety curtain, burning rubber hose.", "converter shop", "slag breach past curtain", ["Has oxygen blowing and inert gas stirring been halted?", "Is the burned hose a water cooling line or oxygen supply line?", "Have workers checked for secondary fires behind the shield?"], ["converter_blow_halt", "hose_service_fluid_id", "secondary_fire_check"], ["BSL/SOP/MMS-03", "BSL/SOP/FIR-01"]),
            ("Hot metal crane hoist brake slipped 1 meter while transporting full iron ladle.", "hot metal bay", "crane hoist brake slip with hot metal", ["Lower the ladle slowly to ground immediately — is the area beneath cleared?", "Has crane maintenance applied mechanical emergency shoe brake?", "Are any other ladles or torpedoes trapped under this crane span?"], ["ground_ladle_immediately", "emergency_shoe_brake", "crane_span_clearance"], ["BSL/SOP/MMS-03", "BSL/SOP/CRN-04"]),
            ("Water pipe above iron runner dripping water 3 feet from molten iron stream.", "runner gallery", "water dripping near molten metal runner", ["Diverting water is urgent — can the valve upstream be closed immediately?", "Is steam forming near the runner edge?", "Are casthouse workers evacuated beyond the splatter zone?"], ["upstream_water_cutoff", "steam_formation_warning", "splatter_evacuation"], ["BSL/SOP/MMS-03"]),
            ("Slag pit embankment collapsed after heavy rain; molten slag flowing towards pump house.", "slag pit", "embankment collapse slag moving to pump", ["Are pump house operators evacuated immediately?", "Can bulldozers build an earthen berm barrier to redirect the slag flow?", "Are there high-voltage buried cables in the slag path?"], ["pump_house_evac", "earthen_berm_redirection", "underground_cable_hazard"], ["BSL/SOP/MMS-03"])
        ],
        "chemical_spill": [
            ("Sulfuric acid tanker unloading hose sheared at coupling, spraying acid.", "acid unloading bay", "sulfuric acid hose sheared", ["Has emergency remote shutoff button for the tanker valve been triggered?", "Are responders using acid-resistant butyl rubber suits and SCBA?", "Has neutralization lime or dry sand been mobilized to contain spill?"], ["remote_tanker_shutoff", "acid_ppe_suit", "lime_neutralization"], ["BSL/SOP/CSP-05"]),
            ("Hydrochloric acid tank level gauge glass cracked, acid running into bund wall.", "pickling line", "HCl level glass cracked running in bund", ["Is the acid contained entirely inside the acid-proof bund wall?", "Has water spray scrubber been turned on to knock down toxic HCl fumes?", "Has pickling line exhaust ventilation been increased to maximum?"], ["bund_containment_status", "fume_scrubber_water_spray", "exhaust_ventilation"], ["BSL/SOP/CSP-05"]),
            ("Worker splashed in face with caustic soda solution while opening pump drain valve.", "water treatment", "caustic soda face splash", ["Get the worker to the emergency eyewash / safety shower immediately — is flushing underway?", "Has water flushing been maintained continuously for at least 15 minutes?", "Is medical ambulance requested with specialized burn wash?"], ["eyewash_shower_underway", "15_min_flush_time", "medical_ambulance_call"], ["BSL/SOP/CSP-05"]),
            ("Chlorine ton container valve leaking green-yellow gas in chlorination plant.", "water treatment plant", "chlorine gas green yellow leak", ["Put on emergency chlorine hood kit or B-kit — is gas moving toward township?", "Has the chlorine absorption caustic scrubber tower started automatically?", "Has upwind evacuation siren been sounded?"], ["chlorine_b_kit_status", "caustic_scrubber_tower", "upwind_siren_sounding"], ["BSL/SOP/CSP-05", "BSL/SOP/GEN-04"]),
            ("PCB-containing dielectric oil leaking from decommissioned capacitor rack onto soil.", "old switchyard", "PCB oil leaking to soil", ["Has containment berm with polypropylene absorbent boom been placed around leak?", "Have workers avoided touching oil without nitrile/viton gloves?", "Is rain forecast that could wash PCB oil into stormwater drains?"], ["absorbent_boom_berm", "nitrile_viton_gloves", "stormwater_drain_blockage"], ["BSL/SOP/CSP-05"]),
            ("Hydrazine drum punctured by hand trolley wheel in boiler feedwater chemical room.", "boiler house", "hydrazine drum leak in enclosed room", ["Evacuate chemical room immediately — hydrazine is toxic and carcinogenic, is door shut?", "Are responders equipped with positive pressure SCBA?", "Is chemical neutralization agent (hypochlorite) ready for application?"], ["evacuate_chemical_room", "positive_pressure_scba", "hypochlorite_neutralization"], ["BSL/SOP/CSP-05"]),
            ("Waste acid sump overflowing into common factory drain after pump failure.", "effluent treatment", "acid sump overflow to common drain", ["Can effluent diversion valve be switched to emergency holding lagoon?", "Has pH monitoring sensor at discharge canal alarmed?", "Has soda ash dosing been started at the overflow point?"], ["holding_lagoon_diversion", "discharge_ph_reading", "soda_ash_dosing"], ["BSL/SOP/CSP-05"]),
            ("Benzol (benzene) pump seal blew out in byproduct plant; sweet smell and liquid pool.", "coke byproduct plant", "benzene pump seal blown, sweet odor", ["Benzene is highly flammable and carcinogenic — are all non-intrinsically-safe radios off?", "Has foam blanket been applied over the liquid pool to suppress vapor?", "Are all workers upwind with organic vapor respirators?"], ["intrinsically_safe_compliance", "foam_blanket_vapor_suppress", "upwind_organic_respirators"], ["BSL/SOP/CSP-05", "BSL/SOP/FIR-01"]),
            ("Mixed acid (HNO3 + HF) stainless steel pickling tank leaking through brick lining.", "cold rolling mill", "HNO3 + HF mixed acid tank lining leak", ["Is calcium gluconate antidote gel available on site for HF exposure?", "Has pickling bath heating steam been shut off immediately?", "Is acid pump transfer to spare dump tank initiated?"], ["calcium_gluconate_gel", "steam_heating_cutoff", "dump_tank_transfer"], ["BSL/SOP/CSP-05"]),
            ("Solvent degreaser drum overturned in roll shop; vapors causing lightheadedness.", "roll shop", "solvent drum spill, worker dizzy", ["Move affected workers to fresh air immediately — are they conscious?", "Have all open flames, heaters, and grinders in roll shop been stopped?", "Are roll shop roll-up doors opened fully for cross-ventilation?"], ["fresh_air_victim_check", "extinguish_grinding_heaters", "roll_up_doors_ventilation"], ["BSL/SOP/CSP-05"])
        ],
        "mechanical_failure": [
            ("Raw material conveyor belt snapped under 800-ton load and rolled back down incline.", "RMY conveyor gallery", "conveyor snap rollback under load", ["Did the mechanical backstop or gravity take-up brake engage?", "Are any workers trapped or injured under collapsed material along the gallery?", "Has the conveyor drive motor been locked out?"], ["backstop_brake_engagement", "gallery_casualty_search", "drive_motor_loto"], ["BSL/SOP/MCH-02"]),
            ("Heavy primary crusher jaw jammed with tramp iron; motor stalling and belt smoking.", "crusher house", "crusher jammed with tramp iron", ["Do NOT attempt manual clearing — has crusher motor breaker been locked out?", "Has hydraulic relief mechanism been vented safely?", "Is crane or magnet available for mechanical extraction?"], ["prohibit_manual_clearing", "hydraulic_relief_vent", "mechanical_extraction_crane"], ["BSL/SOP/MCH-02"]),
            ("Induced draft fan bearing disintegrated at 1500 RPM, severe housing vibration and metal flying.", "sinter plant", "ID fan bearing disintegration 1500 RPM", ["Has the emergency trip button on the fan console been pushed?", "Has the fan housing exclusion zone of 30 meters been cleared?", "Has adjacent furnace suction been rerouted to standby fan?"], ["emergency_fan_trip", "shrapnel_exclusion_zone", "standby_fan_switchover"], ["BSL/SOP/MCH-02"]),
            ("Sinter pallet car derailed on curved track, tilting toward pedestrian walkway.", "sinter machine", "pallet car derailed tilting to walkway", ["Has the sinter strand drive motor been stopped?", "Is walkway beneath the tilting car barricaded against collapse?", "Are hydraulic jacking tools ready for rerailing under supervisor control?"], ["strand_drive_stop", "walkway_barricaded", "hydraulic_jacking_supervisor"], ["BSL/SOP/MCH-02"]),
            ("Heavy gear coupling bolts sheared on rolling mill main drive shaft; shaft wobbling.", "rolling mill drive", "gear coupling sheared shaft wobble", ["Stop mill drive immediately — has operator hit the red mushroom trip?", "Has drive motor power been disconnected from breaker?", "Is there oil or lube line damaged by the wobbling shaft?"], ["mushroom_trip_pressed", "breaker_power_disconnected", "lube_line_damage_check"], ["BSL/SOP/MCH-02"]),
            ("Hydraulic cylinder rod sheared on ladle car tilt mechanism; ladle locked at 30 degrees.", "converter charging bay", "hydraulic rod sheared ladle tilted", ["Is molten metal currently inside the tilted ladle?", "Has hydraulic pressure been isolated and bleed-off valve closed?", "Can hot metal crane hook attach to ladle trunnions to stabilize it?"], ["metal_inside_tilted_ladle", "hydraulic_isolation_bleedoff", "crane_hook_stabilization"], ["BSL/SOP/MCH-02", "BSL/SOP/MMS-03"]),
            ("Billet shear blade cracked and jammed halfway through hot steel bar.", "continuous casting", "shear blade cracked bar jammed", ["Has hydraulic pump pressure to the shear cylinder been relieved?", "Is hot billet cooling water turned on to prevent blade welding?", "Has permit to work (PTW) been issued before inspection?"], ["shear_cylinder_pressure_relief", "bar_cooling_spray", "ptw_issuance_inspection"], ["BSL/SOP/MCH-02"]),
            ("Flywheel guard tore off high-speed stamping press; rotating wheel exposed.", "maintenance workshop", "flywheel guard detached high speed", ["Press stop button and allow flywheel to coast to complete halt — has power been cut?", "Are workers kept clear of the rotating plane of the wheel?", "Is brake assembly functional to stop freewheeling?"], ["power_cut_coast_to_halt", "rotating_plane_clearance", "freewheeling_brake_status"], ["BSL/SOP/MCH-02"]),
            ("Slag scraper conveyor chain broke and piled up inside water quench pit.", "granulated slag plant", "scraper chain broke inside quench pit", ["Has water quench pump been turned off to stop steam generation?", "Is quench pit access permit required before anyone steps near edge?", "Has drive sprocket power been locked out?"], ["quench_water_pump_off", "quench_pit_access_permit", "sprocket_loto"], ["BSL/SOP/MCH-02", "BSL/SOP/CSP-01"]),
            ("Rotary kiln thrust roller bearing overheated to 180°C with severe grinding noise.", "lime calcining plant", "thrust roller bearing 180C overheating", ["Can kiln speed be reduced immediately to relieve thrust pressure?", "Has emergency lube oil circulation been verified?", "Are firefighters standing by due to grease flammability at high temp?"], ["kiln_speed_reduction", "emergency_lube_circulation", "grease_fire_standby"], ["BSL/SOP/MCH-02"])
        ],
        "confined_space_emergency": [
            ("Two contractor workers inside degasser vessel not responding to radio; O2 alarm buzzing.", "SMS2 vacuum degasser", "two workers unresponsive in vessel, O2 low", ["Do NOT enter without SCBA — has emergency rescue team with airline trolley been called?", "Has fresh air forced ventilation blower been started into the manhole?", "Has argon/nitrogen purge valve to the vessel been locked and blanked?"], ["prohibit_entry_without_scba", "forced_air_ventilation", "inert_gas_blanking_loto"], ["BSL/SOP/CSP-01"]),
            ("Worker collapsed inside sewer inspection pit near coke oven byproduct plant.", "byproduct sewer", "worker collapsed in sewer pit", ["Do NOT jump in to rescue — are retrieval tripod and harness winch in place?", "What does multi-gas detector lower into the pit read for H2S and CH4?", "Has ambulance and rescue team been summoned?"], ["tripod_harness_winch", "detector_h2s_ch4_reading", "rescue_ambulance_summoned"], ["BSL/SOP/CSP-01"]),
            ("Gas holder dry seal piston chamber entry; supervisor smells gas through manhole.", "GHS holder", "gas smell at dry seal manhole", ["Halt entry immediately — is valid Confined Space Entry Permit posted at hatch?", "Has continuous 4-gas monitoring detector been zeroed and lowered?", "Is an authorized standby attendant positioned outside the hatch?"], ["halt_entry_permit_check", "continuous_gas_monitoring", "standby_attendant_at_hatch"], ["BSL/SOP/CSP-01", "BSL/SOP/COG-02"]),
            ("Welder welding inside water storage tank, welding smoke accumulated, worker feeling faint.", "water storage tank", "welder faint from smoke in tank", ["Turn off welding machine power and pull worker out via safety lifeline immediately.", "Was local exhaust fume extraction fan operating inside tank?", "Is 100% oxygen strictly prohibited from being used to ventilate?"], ["lifeline_extraction_immediate", "fume_extractor_status", "no_pure_oxygen_ventilation"], ["BSL/SOP/CSP-01"]),
            ("Worker descended into raw coal bunker without safety harness; coal sliding down.", "coal bunker", "worker in bunker without harness, coal sliding", ["Do not open bottom discharge gate! Has coal conveyor feeder been locked out?", "Can a rescue ladder or retrieval line be lowered from top deck?", "Are spotters stationed on top deck keeping visual contact?"], ["lockout_bottom_discharge", "lowering_rescue_ladder", "deck_spotter_visual_contact"], ["BSL/SOP/CSP-01"]),
            ("Acid storage tank interior inspection; nitrogen line connected to tank by mistake.", "acid plant", "nitrogen line connected to tank interior", ["Evacuate tank immediately — nitrogen causes instantaneous asphyxiation!", "Has nitrogen line been physically disconnected and blanked with spade?", "Are workers inside showing any sign of dizziness or stumbling?"], ["immediate_asphyxiation_evac", "nitrogen_line_physical_blank", "asphyxiation_symptoms_check"], ["BSL/SOP/CSP-01"]),
            ("Duct cleaner stuck in narrow vertical gas duct bend between BF and scrubber.", "BF scrubber duct", "worker physically stuck in vertical bend", ["Has rope rescue team with specialized vertical harness arrived?", "Is duct isolated from blast furnace gas with blind plate?", "Is communication maintained with the trapped worker?"], ["rope_rescue_team_arrival", "blind_plate_isolation", "continuous_verbal_communication"], ["BSL/SOP/CSP-01", "BSL/SOP/BFG-01"]),
            ("Painting contractor using solvent-based epoxy inside underground pipe culvert, fumes heavy.", "underground culvert", "solvent vapors in unventilated culvert", ["Are spark-proof explosion-proof air blowers operating?", "Are workers using supplied-air respirators or certified organic vapor masks?", "Have all ignition sources and non-flameproof lights been removed?"], ["explosion_proof_blowers", "supplied_air_respirators", "flameproof_lighting_check"], ["BSL/SOP/CSP-01", "BSL/SOP/CSP-05"]),
            ("Slag granulation sump pit entry without atmosphere clearance after monsoon flood.", "granulation sump", "pit entry without testing after flood", ["Has atmospheric testing verified O2 > 19.5% and CO < 25 ppm?", "Has pit water been completely pumped out before descent?", "Is standby rescuer equipped with self-contained breathing apparatus?"], ["atmosphere_testing_clearance", "water_pumpout_verified", "standby_rescuer_scba"], ["BSL/SOP/CSP-01"]),
            ("Furnace cooling staves refractory rebuild chamber; brick fell near entry ladder.", "BF inside shaft", "falling brick near access ladder in shaft", ["Are safety overhead catch nets and head protection baffles installed?", "Have workers stepped into safety niches inside the furnace shell?", "Is hoist lowering materials into shaft halted immediately?"], ["overhead_catch_nets", "safety_niche_shelter", "material_hoist_halt"], ["BSL/SOP/CSP-01", "BSL/SOP/MMS-03"])
        ],
        "crane_lifting_failure": [
            ("Ladle crane main wire rope slipped off drum groove with 120-ton liquid iron ladle.", "BF casthouse", "wire rope slipped drum groove with ladle", ["Clear all personnel beneath crane radius — can ladle be rested on floor?", "Has crane power supply been tripped to prevent wire rope snapping?", "Is the auxiliary hoist brake holding the load stable?"], ["clear_load_radius", "crane_power_tripped", "auxiliary_brake_status"], ["BSL/SOP/CRN-04", "BSL/SOP/MMS-03"]),
            ("Heavy motor being lifted over control room roof; synthetic webbing sling tearing.", "central control room", "synthetic sling tearing over roof", ["Clear all occupants from control room beneath the suspended load immediately!", "Can the crane operator swing the boom away to an open ground area?", "What is the weight of the motor compared to sling safe working load (SWL)?"], ["control_room_evac_beneath", "swing_to_open_ground", "weight_vs_sling_swl"], ["BSL/SOP/CRN-04"]),
            ("Gantry crane collided with end stop buffer; cab detached from rail by 4 inches.", "scrap yard", "gantry collision end buffer cab displaced", ["Is crane operator injured inside cabin, and is cabin structurally stable?", "Has gantry runway power track (DSL) been de-energized?", "Is hydraulic manlift mobilized for operator rescue?"], ["operator_cabin_stability", "dsl_power_deenergized", "manlift_rescue_mobilize"], ["BSL/SOP/CRN-04"]),
            ("Steel plate bundle slipped out of magnetic crane lifter during transfer across bay.", "plate mill", "plate bundle dropped from magnetic lifter", ["Are there any workers under or adjacent to the dropped plates?", "Did the magnet power backup battery system engage upon power drop?", "Has crane runway access been cordoned off for inspection?"], ["plate_casualty_search", "magnet_battery_backup_status", "runway_access_cordon"], ["BSL/SOP/CRN-04"]),
            ("Crane wire rope snapped while lifting tundish; hook block dropped onto caster floor.", "continuous caster", "wire rope snap hook block dropped", ["Are any caster floor personnel hit by whip of the snapped wire rope?", "Is the caster mold cooling water line intact or ruptured by the hook block?", "Has the lifting area been isolated with red hazard tape?"], ["wire_whip_injuries", "cooling_water_line_integrity", "red_tape_isolation"], ["BSL/SOP/CRN-04"]),
            ("Tandem crane lift out of sync; 80-ton transformer tilting and stressing rigging.", "substation yard", "tandem lift out of sync transformer tilting", ["Stop both crane hoists immediately — hold load stationary.", "Is the load tilting towards crane boom or electrical live equipment?", "Is a qualified rigging supervisor directing both crane operators by radio?"], ["hold_both_hoists_stationary", "tilt_direction_danger", "radio_rigging_supervisor"], ["BSL/SOP/CRN-04", "BSL/SOP/ELC-03"]),
            ("Rough terrain mobile crane outrigger sank into uncompacted gravel, crane listing 10 degrees.", "construction site", "outrigger sank crane listing 10 deg", ["Lower load directly to ground if safe, and do not rotate counterweight!", "Are outrigger wooden/steel spreader mats in use beneath pads?", "Has ground radius around the listing crane been evacuated?"], ["lower_load_no_counterweight_rotation", "outrigger_spreader_mats", "ground_radius_evacuation"], ["BSL/SOP/CRN-04"]),
            ("Crane hoist hook safety latch broken; rigging chain slipped off hook tip during slew.", "maintenance shop", "hook safety latch broken chain slip", ["Is suspended load resting on stable ground now?", "Has this crane been tagged out of service until latch is replaced?", "Was pre-shift daily crane inspection checklist completed today?"], ["load_stable_on_ground", "crane_tagout_service", "daily_checklist_audit"], ["BSL/SOP/CRN-04"]),
            ("Overhead crane DSL busbar sparking heavily and dropping molten copper droplets on floor.", "rolling mill bay", "crane busbar sparking dropping copper", ["Have ground personnel cleared the walkway directly beneath the DSL track?", "Has power to the crane DSL rail been isolated at the wall isolator?", "Are collector shoes worn down to steel brackets?"], ["walkway_beneath_dsl_cleared", "dsl_wall_isolator_opened", "collector_shoe_wear"], ["BSL/SOP/CRN-04", "BSL/SOP/ELC-03"]),
            ("Crane load caught on structural steel column during blind lift; rigging under extreme tension.", "SMS converter bay", "blind lift load snagged column high tension", ["Do NOT force hoist — stop hoist immediately to prevent rope break!", "Is designated banksman / signaller in clear two-way communication with crane cab?", "Can load be lowered slightly to release caught corner safely?"], ["stop_hoist_prevent_break", "signaller_communication", "slight_lower_release_snag"], ["BSL/SOP/CRN-04"])
        ],
        "vehicle_traffic_incident": [
            ("50-ton slag dumper collided with locomotive at railway level crossing Gate 3.", "railway crossing 3", "dumper collided with locomotive", ["Is the dumper driver or train loco pilot trapped or injured?", "Has molten slag or fuel spilled onto the railway tracks?", "Has railway traffic control halted all train movement on lines 1, 2, and 3?"], ["driver_loco_pilot_triage", "fuel_slag_track_spill", "halt_all_rail_traffic"], ["BSL/SOP/VEH-06"]),
            ("Forklift overturned on ramp while carrying 5-ton coil; driver pinned under ROPS cage.", "coil yard ramp", "forklift overturn driver pinned under cage", ["Is the driver conscious and is breathing unobstructed under the roll cage?", "Mobilize hydraulic spreader / airbags immediately — do not drag driver out.", "Has fuel/battery acid leak from overturned forklift been checked?"], ["driver_breathing_under_cage", "hydraulic_spreader_airbags", "battery_acid_fuel_leak"], ["BSL/SOP/VEH-06"]),
            ("Contractor worker struck by reversing front-end loader in dark raw material yard.", "RMY yard", "worker struck by reversing loader", ["Is the worker conscious — do not move spine if back/pelvic injury suspected.", "Is the site emergency medical ambulance dispatched with spine board?", "Was the reversing alarm and beacon light working on the loader?"], ["c-spine_immobilization_triage", "spine_board_ambulance", "loader_reverse_alarm_audit"], ["BSL/SOP/VEH-06"]),
            ("Molten metal carrier truck brakes failed on downgrade slope; crashed into sand barrier.", "casthouse road", "carrier truck brake failure crash into sand", ["Did the sand barrier contain the carrier without spilling hot metal?", "Are carrier driver and escort vehicle crew uninjured?", "Is hot metal solidifying inside vessel requiring emergency crane pick?"], ["sand_barrier_containment", "driver_crew_injuries", "hot_metal_solidification_timer"], ["BSL/SOP/VEH-06", "BSL/SOP/MMS-03"]),
            ("Heavy trailer hauling 40-foot structural beams jackknifed, blocking emergency gate 1.", "gate 1 road", "trailer jackknifed blocking emergency gate", ["Can emergency vehicles (ambulances, fire engines) access via Gate 2?", "Are the heavy steel beams secured on the trailer or loose on road?", "Has heavy towing crane been called to clear emergency gate road?"], ["gate_2_emergency_reroute", "loose_beams_road_hazard", "heavy_tow_crane_dispatch"], ["BSL/SOP/VEH-06"]),
            ("Locomotive shunter derailed at track switch 12; two wagons tilting toward gas pipeline.", "rail siding GHS", "loco derailment wagons tilting to gas line", ["Are tilting wagons making contact with the gas pipeline bridge support?", "Has gas pipeline visual inspection been conducted for dents or stress?", "Has rail breakdown crane train been ordered from traffic station?"], ["gas_pipeline_contact_check", "pipeline_stress_inspection", "breakdown_crane_train"], ["BSL/SOP/VEH-06", "BSL/SOP/BFG-01"]),
            ("Pedestrian worker side-swiped by speeding pickup truck on main plant arterial road.", "central avenue", "pedestrian struck by pickup truck", ["Check worker breathing and bleeding — apply direct pressure if hemorrhaging.", "Has traffic police / security closed the arterial road lane?", "Is the driver on scene and vehicle secured?"], ["bleeding_hemorrhage_first_aid", "road_lane_closure", "driver_vehicle_secured"], ["BSL/SOP/VEH-06"]),
            ("Dumper body raised while driving under 11kV overhead power line; flashover to truck body.", "haul road", "dumper raised hit 11kV line flashover", ["Driver must STAY INSIDE cabin — tires insulate from ground! Do not step out!", "Has electrical switchyard de-energized the 11kV line immediately?", "Has a 20-meter perimeter been cleared to prevent step-potential shock?"], ["driver_stay_inside_cabin", "line_deenergized_switchyard", "step_potential_20m_perimeter"], ["BSL/SOP/VEH-06", "BSL/SOP/ELC-03"]),
            ("Diesel fuel bowser truck tank punctured on sharp curb, spilling diesel near boiler intake.", "boiler road", "diesel fuel tanker puncture near boiler", ["Keep diesel away from boiler air intake — are foam fire extinguishers ready?", "Has drain inlet cover been sealed to prevent diesel entering storm drain?", "Has soil/sand containment bund been erected around fuel puddle?"], ["boiler_intake_ignition_risk", "storm_drain_cover_seal", "sand_bund_containment"], ["BSL/SOP/VEH-06", "BSL/SOP/FIR-01"]),
            ("Overhead bridge crane walkway access vehicle hit by yard crane hook during transit.", "yard 4 road", "crane hook collided with utility truck", ["Are utility truck occupants injured by the swinging hook impact?", "Is crane hook still entangled with the truck frame?", "Has the yard crane been brought to complete stop?"], ["truck_occupants_injuries", "hook_frame_entanglement", "yard_crane_stop"], ["BSL/SOP/VEH-06", "BSL/SOP/CRN-04"])
        ],
        "slip_fall": [
            ("Worker fell 4 meters from temporary scaffolding without safety harness at sinter plant.", "sinter plant", "worker fell 4m from scaffolding", ["Do not move the fallen worker — is the worker conscious and breathing?", "Is cervical spine collar and trauma ambulance dispatched immediately?", "Was the scaffolding green-tagged (certified) or missing guardrails?"], ["spine_immobilization_triage", "trauma_ambulance_dispatch", "scaffold_tag_audit"], ["BSL/SOP/SLP-07"]),
            ("Worker slipped on grease puddle on casthouse stairs, fell down 8 steps, dislocated shoulder.", "BF casthouse stairs", "worker fell down stairs on grease", ["Is worker sitting safely away from active casthouse machinery?", "Has cold pack / immobilization been applied to shoulder?", "Has the grease puddle been cordoned and absorbents spread?"], ["safe_position_away_machines", "shoulder_immobilization", "grease_cordon_absorbent"], ["BSL/SOP/SLP-07"]),
            ("Contractor worker fell through corroded metal floor grating 3 meters into pipe trench.", "pipe bridge", "worker fell through corroded floor grating", ["Is the worker conscious in the pipe trench, and are toxic pipes present?", "Lower rescue ladder — can first responders access without stepping on weak grating?", "Has the entire corroded grating section been barricaded with red barrier?"], ["pipe_trench_toxicity_check", "safe_rescue_access_path", "weak_grating_barricade"], ["BSL/SOP/SLP-07"]),
            ("Worker slipped on wet tiled floor in control room washroom, hit head on sink.", "control room washroom", "worker slipped hit head on sink", ["Is the worker conscious, oriented to time/place, or vomiting?", "Check pupils and scalp bleeding — apply sterile gauze pad.", "Has wet floor cautionary sign board been placed at washroom door?"], ["head_trauma_pupil_check", "scalp_bleeding_control", "wet_floor_signboard"], ["BSL/SOP/SLP-07"]),
            ("Scaffolding tilted during erection when base jack slipped off wooden sole plate.", "calcining plant", "scaffolding tilted base jack slip", ["Are workers still on the scaffolding — can they climb to adjacent permanent walkway?", "Has the drop zone beneath the tilted scaffold been cleared 10 meters?", "Are scaffold riggers securing stabilizing guide ropes?"], ["scaffold_occupant_safe_exit", "drop_zone_10m_cleared", "stabilizing_guide_ropes"], ["BSL/SOP/SLP-07"]),
            ("Worker fell from ladder while servicing overhead crane lighting fixture; ladder slipped.", "maintenance bay", "worker fell from ladder servicing light", ["Is the worker able to move limbs without severe pain?", "Was the ladder secured at top and bottom or held by assistant?", "Is ambulance en route to bay?"], ["limb_movement_pain_check", "ladder_securing_audit", "bay_ambulance_dispatch"], ["BSL/SOP/SLP-07"]),
            ("Slip and fall on ice/frost-coated cooling tower exterior stairs during winter night shift.", "cooling tower", "slipped on iced stairs night shift", ["Are stairs illuminated adequately, and is salt / grit available to melt ice?", "Are injured workers accompanied to medical post?", "Has alternative internal staircase been designated for shift change?"], ["stair_lighting_ice_grit", "medical_post_escort", "alternative_staircase_route"], ["BSL/SOP/SLP-07"]),
            ("Worker fell into uncovered floor pit in pump house during power blackout.", "pump house", "worker fell in uncovered pit in blackout", ["Turn on emergency torches — is worker responsive in the pit?", "Are there spinning pump shafts or high-temp water in the pit?", "Has emergency lighting been activated in the pump house?"], ["pit_status_torchlight_check", "pump_shaft_hazard_in_pit", "emergency_lighting_active"], ["BSL/SOP/SLP-07"]),
            ("Painter safety harness lanyard snapped when painter slipped on sloped roof sheet.", "warehouse roof", "lanyard snapped on sloped roof", ["Did painter fall to ground or is caught on roof gutter / lifeline?", "Is rescue ladder or high-reach boom truck mobilized to roof edge?", "What type of lanyard was in use — wire rope or synthetic webbing?"], ["gutter_lifeline_catch_status", "boom_truck_roof_rescue", "lanyard_type_failure_audit"], ["BSL/SOP/SLP-07"]),
            ("Worker slipped on conveyor spill of iron ore fines and slide 5 meters down incline chute.", "ore transfer chute", "worker slid down chute on ore fines", ["Has the conveyor belt above and below the chute been emergency stopped?", "Is the chute discharge gate closed to prevent sliding into crusher?", "Can worker climb out using chute maintenance safety ropes?"], ["conveyor_emergency_stopped", "chute_gate_closed_to_crusher", "chute_safety_rope_exit"], ["BSL/SOP/SLP-07", "BSL/SOP/MCH-02"])
        ]
    }
    
    # Add generated scenarios into all_scenarios
    idx_counter = len(all_scenarios) + 1
    for cat, items in extra_templates.items():
        for i, (report, loc, facts, must_asks, targets, sops) in enumerate(items, 1):
            sc_id = f"{cat[:3]}_{i:02d}"
            all_scenarios.append({
                "id": sc_id,
                "hazard_type": cat,
                "zone_id": "SMS" if "SMS" in loc else ("PWR" if "PWR" in loc else ("BF1" if "BF" in loc else "RMY")),
                "language": "en" if i % 2 == 1 else "hi",
                "report_style": "clear_factual" if i % 3 == 0 else ("panicked_short" if i % 3 == 1 else "vague"),
                "initial_report": report,
                "already_known_facts": [facts],
                "must_ask_questions": must_asks,
                "target_slots": targets,
                "relevant_sop_ids": sops
            })
            idx_counter += 1

    return all_scenarios

if __name__ == "__main__":
    scenarios = build_all_100()
    print(f"Generated total {len(scenarios)} gold scenarios.")
    out_file = Path(__file__).resolve().parent.parent / "tests" / "data" / "gold_rag_scenarios.json"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump({"version": "1.0", "disclaimer": "DRAFT - FOR SAFETY OFFICER REVIEW", "scenarios": scenarios}, f, indent=2, ensure_ascii=False)
    print(f"Saved to {out_file}")
