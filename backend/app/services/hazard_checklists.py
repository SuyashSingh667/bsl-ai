"""
Hazard Information Needs Registry.
Structured question-oriented knowledge layer for heavy industry emergency response.
Defines what emergency responders and safety officers MUST know within the first
60-90 seconds across all 10 industrial hazard categories.

Marked: DRAFT — FOR SAFETY OFFICER REVIEW
"""

from typing import Any

INFORMATION_NEEDS_REGISTRY: dict[str, list[dict[str, Any]]] = {
    "gas_leak": [
        {
            "slot": "isolation_status",
            "priority": 1,
            "description": "Whether the gas supply is isolated or valve accessible",
            "clinical_intent": "Determines whether acute spread continues or source is cut off",
            "default_q": {
                "en": "Has the gas supply or isolation valve been safely closed?",
                "hi": "क्या गैस सप्लाई या आइसोलेशन वाल्व सुरक्षित रूप से बंद कर दिया गया है?"
            },
            "options": {
                "en": ["Safely isolated / valve closed", "Cannot reach valve due to gas", "Gas actively leaking", "Status unconfirmed"],
                "hi": ["सुरक्षित रूप से बंद / वाल्व आइसोलेट", "गैस के कारण वाल्व तक पहुंच असंभव", "गैस लगातार लीक हो रही है", "पुष्टि नहीं"]
            }
        },
        {
            "slot": "victims_condition",
            "priority": 1,
            "description": "Presence of symptomatic, unconscious, or trapped personnel",
            "clinical_intent": "Immediately trips ambulance and emergency rescue with SCBA",
            "default_q": {
                "en": "Are any workers unconscious, experiencing dizziness, or trapped near the leak?",
                "hi": "क्या कोई कर्मचारी बेहोश है, चक्कर आ रहे हैं, या रिसाव के पास फंसा है?"
            },
            "options": {
                "en": ["Worker unconscious or overcome", "Workers dizzy / nauseous", "All workers conscious and safe", "No personnel present"],
                "hi": ["कर्मचारी बेहोश है", "कर्मचारियों को चक्कर / उल्टी", "सभी कर्मचारी सुरक्षित", "कोई उपस्थित नहीं था"]
            }
        },
        {
            "slot": "evacuation_status",
            "priority": 2,
            "description": "Whether personnel are moving upwind to designated assembly points",
            "clinical_intent": "Prevents toxic exposure progression and establishes perimeter",
            "default_q": {
                "en": "Have personnel evacuated upwind away from the gas cloud?",
                "hi": "क्या सभी कर्मचारी हवा की विपरीत दिशा (upwind) में सुरक्षित हट गए हैं?"
            },
            "options": {
                "en": ["Evacuated upwind to safe point", "Evacuation in progress", "Workers cannot move upwind", "Evacuation not started"],
                "hi": ["हवा की विपरीत सुरक्षित पहुंचे", "निकासी जारी है", "कर्मचारी हट नहीं पा रहे", "निकासी शुरू नहीं"]
            }
        },
        {
            "slot": "ignition_source",
            "priority": 2,
            "description": "Presence of flames, hot work, or vehicle running in flammable gas zone",
            "clinical_intent": "Prevents secondary catastrophic explosion",
            "default_q": {
                "en": "Are there any hot work, open flames, or vehicle engines running near the leak?",
                "hi": "क्या रिसाव के पास कोई वेल्डिंग, खुली आग या गाड़ी का इंजन चालू है?"
            },
            "options": {
                "en": ["Open flames or hot work active", "Vehicle engine running nearby", "All ignition sources isolated", "None visible"],
                "hi": ["खुली आग या वेल्डिंग चालू", "पास में गाड़ी चालू है", "सभी चिंगारी स्रोत बंद", "कोई स्रोत नहीं"]
            }
        }
    ],

    "fire": [
        {
            "slot": "material_involved",
            "priority": 1,
            "description": "Fuel source involved (electrical cables, transformer oil, flammable gas, conveyor belt)",
            "clinical_intent": "Dictates correct extinguishing agent (never use water on live electrical or molten metal)",
            "default_q": {
                "en": "What material is burning: electrical cables, transformer oil, gas line, or conveyor belt?",
                "hi": "आग किसमें लगी है: बिजली केबल, ट्रांसफार्मर तेल, गैस लाइन, या कन्वेयर बेल्ट?"
            },
            "options": {
                "en": ["Electrical cables or panel", "Transformer oil / fuel", "Gas line / flammable vapor", "Conveyor rubber / coal"],
                "hi": ["बिजली केबल या पैनल", "ट्रांसफार्मर तेल / ईंधन", "गैस लाइन / वाष्प", "कन्वेयर रबर या कोयला"]
            }
        },
        {
            "slot": "electrical_power_cut",
            "priority": 1,
            "description": "Whether electrical power supply to the fire area has been tripped",
            "clinical_intent": "Eliminates electrocution hazard for firefighters",
            "default_q": {
                "en": "Has electrical power to the burning area or equipment been de-energized?",
                "hi": "क्या जलते हुए उपकरण या क्षेत्र की बिजली मेन ब्रेकर से काट दी गई है?"
            },
            "options": {
                "en": ["Power tripped and de-energized", "Power still live / cannot isolate", "Breaker status unknown", "Not electrical related"],
                "hi": ["बिजली बंद कर दी गई है", "बिजली अभी भी चालू है", "ब्रेकर स्थिति की पुष्टि नहीं", "बिजली से संबंधित नहीं"]
            }
        },
        {
            "slot": "victims_condition",
            "priority": 1,
            "description": "Burn injuries or workers trapped in smoke / overhead cabins",
            "clinical_intent": "Dispatches burn trauma team and hydraulic snorkel ladders",
            "default_q": {
                "en": "Are any workers trapped by smoke, or have anyone suffered burn injuries?",
                "hi": "क्या कोई कर्मचारी धुएं में फंसा है या किसी को जलने की चोट आई है?"
            },
            "options": {
                "en": ["Workers trapped in cabin/smoke", "Workers have burn injuries", "Smoke inhalation symptoms", "All personnel accounted for"],
                "hi": ["कर्मचारी केबिन/धुएं में फंसे हैं", "जलने की चोटें आई हैं", "धुआं सांस में जाने के लक्षण", "सभी कर्मचारी सुरक्षित"]
            }
        },
        {
            "slot": "spread_barrier_isolation",
            "priority": 2,
            "description": "Proximity of fire to critical adjacent assets, gas pipes, or oil tanks",
            "clinical_intent": "Focuses defensive boundary cooling to prevent tier-escalation",
            "default_q": {
                "en": "Is the fire threatening adjacent gas lines, oil reservoirs, or populated pulpits?",
                "hi": "क्या आग पास की गैस लाइनों, तेल टैंकों या कंट्रोल पल्पिट की ओर बढ़ रही है?"
            },
            "options": {
                "en": ["Threatening gas lines / oil tanks", "Spreading to cable tunnels", "Contained in local enclosure", "No critical assets adjacent"],
                "hi": ["गैस लाइन / तेल टैंक की ओर बढ़ रही", "केबल टनल में फैल रही", "स्थानीय स्थान में सीमित", "आसपास कोई खतरा नहीं"]
            }
        }
    ],

    "electrical_hazard": [
        {
            "slot": "shock_casualty_pulse",
            "priority": 1,
            "description": "Immediate vital status of shock victim and CPR readiness",
            "clinical_intent": "Instant dispatch of AED defibrillator and cardiac first aid",
            "default_q": {
                "en": "Did any worker suffer electric shock, and is the casualty conscious and breathing?",
                "hi": "क्या किसी कर्मचारी को करंट लगा है, और क्या वह होश में और सांस ले रहा है?"
            },
            "options": {
                "en": ["Victim unconscious / no pulse", "Shocked but conscious", "Arc flash burn injury", "No physical shock sustained"],
                "hi": ["कर्मचारी बेहोश / सांस नहीं", "करंट लगा लेकिन होश में", "आर्क फ्लैश जलने की चोट", "किसी को करंट नहीं लगा"]
            }
        },
        {
            "slot": "circuit_deenergized_loto",
            "priority": 1,
            "description": "Isolation and lockout status of the affected circuit",
            "clinical_intent": "Prevents second victim or rescuer electrocution",
            "default_q": {
                "en": "Has the electrical breaker or feeder been locked out (LOTO) and confirmed dead?",
                "hi": "क्या मेन सर्किट ब्रेकर या फीडर को बंद (LOTO) करके पावर शून्य सुनिश्चित की गई है?"
            },
            "options": {
                "en": ["Confirmed isolated and locked out", "Circuit still energized", "Breaker tripped automatically", "Isolation not confirmed"],
                "hi": ["पावर बंद और लॉक (LOTO)", "सर्किट अभी भी चालू है", "ब्रेकर अपने आप ट्रिप हुआ", "आइसोलेशन की पुष्टि नहीं"]
            }
        },
        {
            "slot": "step_potential_cordon",
            "priority": 2,
            "description": "Establishment of minimum safe clearance perimeter around fallen lines",
            "clinical_intent": "Prevents ground gradient electrocution (especially high voltage)",
            "default_q": {
                "en": "Is a safe perimeter of at least 15 meters barricaded around the live equipment or cable?",
                "hi": "क्या चालू तार या उपकरण के चारों ओर कम से कम 15 मीटर का सुरक्षित घेरा बनाया गया है?"
            },
            "options": {
                "en": ["15-meter cordon established", "Personnel still near equipment", "Area blocked at main doors", "No barricade placed"],
                "hi": ["15 मीटर का घेरा बना दिया", "कर्मचारी अभी भी पास हैं", "मुख्य द्वार बंद किया", "कोई घेरा नहीं लगाया"]
            }
        }
    ],

    "molten_metal_spill": [
        {
            "slot": "water_exclusion_status",
            "priority": 1,
            "description": "Strict exclusion of any water contact with molten slag or liquid iron",
            "clinical_intent": "Absolute prevention of catastrophic steam explosions",
            "default_q": {
                "en": "Is the spill area completely dry, with all water sprays and water lines shut off?",
                "hi": "क्या पिघली धातु का क्षेत्र सूखा है, और सभी पानी के छिड़काव/पाइप तुरंत बंद हैं?"
            },
            "options": {
                "en": ["Area dry, water lines shut", "Water pooling or leaking near spill", "Water spray accidentally running", "Cannot verify ground wetness"],
                "hi": ["क्षेत्र सूखा है, पानी बंद है", "पिघली धातु पास पानी जमा है", "पानी का छिड़काव चल रहा है", "जमीन की पुष्टि नहीं"]
            }
        },
        {
            "slot": "personnel_clear_path",
            "priority": 1,
            "description": "Immediate clearance of personnel from ground-level liquid steel runoff path",
            "clinical_intent": "Protects workers from radiant heat and molten wave engulfment",
            "default_q": {
                "en": "Have all ground personnel evacuated clear of the molten metal flow path and pits?",
                "hi": "क्या सभी कर्मचारी पिघली धातु के बहाव के रास्ते और गड्ढों से सुरक्षित दूर हट गए हैं?"
            },
            "options": {
                "en": ["All personnel cleared to upper deck", "Workers near runoff path", "Workers trapped by radiant heat", "Area was unmanned"],
                "hi": ["सभी ऊपरी डेक पर सुरक्षित", "कर्मचारी बहाव रास्ते के पास", "रेडिएंट गर्मी से फंसे हैं", "क्षेत्र में कोई नहीं था"]
            }
        },
        {
            "slot": "cable_hydraulic_protection",
            "priority": 2,
            "description": "Separation of molten metal from high-pressure hydraulic lines and crane cables",
            "clinical_intent": "Prevents hydraulic fires and secondary structural collapse",
            "default_q": {
                "en": "Is molten metal in contact with hydraulic pipes, oil cellars, or crane cables?",
                "hi": "क्या पिघली धातु हाइड्रोलिक पाइपों, तेल सेलरों या क्रेन केबलों के संपर्क में है?"
            },
            "options": {
                "en": ["In contact with hydraulic/oil lines", "Threatening crane hoist cables", "Confined safely in catch pit", "No flammable lines near"],
                "hi": ["हाइड्रोलिक/तेल लाइनों के संपर्क में", "क्रेन केबल को खतरा", "कैच पिट में सुरक्षित सीमित", "पास कोई तेल लाइन नहीं"]
            }
        }
    ],

    "chemical_spill": [
        {
            "slot": "chemical_identity_hazmat",
            "priority": 1,
            "description": "Exact chemical identity (acid, caustic soda, chlorine, solvent)",
            "clinical_intent": "Selects appropriate PPE suit, neutralizer (lime vs acid), and medical wash",
            "default_q": {
                "en": "What chemical has spilled: hydrochloric acid, sulfuric acid, caustic soda, or solvent?",
                "hi": "कौन सा केमिकल गिरा है: हाइड्रोक्लोरिक एसिड, सल्फ्यूरिक एसिड, कास्टिक सोडा, या सॉल्वेंट?"
            },
            "options": {
                "en": ["Hydrochloric acid (HCl)", "Sulfuric acid (H2SO4)", "Caustic soda (NaOH)", "Solvent / organic liquid"],
                "hi": ["हाइड्रोक्लोरिक एसिड (HCl)", "सल्फ्यूरिक एसिड (H2SO4)", "कास्टिक सोडा (NaOH)", "सॉल्वेंट / कार्बनिक रसायन"]
            }
        },
        {
            "slot": "eyewash_shower_use",
            "priority": 1,
            "description": "Immediate and continuous decontamination flushing for chemical splashes",
            "clinical_intent": "Minimizes permanent chemical burn trauma to eyes and skin",
            "default_q": {
                "en": "Has any worker had skin or eye contact, and is emergency shower flushing underway?",
                "hi": "क्या किसी कर्मचारी पर केमिकल पड़ा है, और क्या इमरजेंसी शावर/आईवाश में धुलाई शुरू हो गई है?"
            },
            "options": {
                "en": ["Eye/skin contact — flushing underway", "Chemical contact — shower not yet used", "No worker had physical contact", "Worker already moved to clinic"],
                "hi": ["त्वचा/आंख पर गिरा — धुलाई जारी", "संपर्क हुआ — शावर नहीं पहुंचा", "किसी पर नहीं पड़ा", "कर्मचारी डिस्पेंसरी भेजा"]
            }
        },
        {
            "slot": "bund_drain_isolation",
            "priority": 2,
            "description": "Containment of liquid inside bund and prevention of entry into stormwater drains",
            "clinical_intent": "Prevents environmental contamination and plant-wide drain reactions",
            "default_q": {
                "en": "Is the spill contained inside the bund wall, or entering stormwater drains?",
                "hi": "क्या केमिकल बंड वाल के अंदर रुका है, या नाले/ड्रेन में बह रहा है?"
            },
            "options": {
                "en": ["Contained within bund wall", "Entering floor drains / open ditch", "Spill spreading across road", "Absorbent booms placed"],
                "hi": ["बंड वाल के अंदर रुका है", "नाले या ड्रेन में बह रहा है", "सड़क पर फैल रहा है", "अब्जॉर्बेंट बूम लगा दिए हैं"]
            }
        }
    ],

    "mechanical_failure": [
        {
            "slot": "equipment_e_stop_loto",
            "priority": 1,
            "description": "Activation of emergency stop, pull cord, and main breaker isolation",
            "clinical_intent": "Prevents machine restart while workers inspect or are entangled",
            "default_q": {
                "en": "Has the emergency pull cord or E-stop button been tripped and locked out?",
                "hi": "क्या इमरजेंसी पुल कॉर्ड या स्टॉप बटन दबाकर मशीन को लॉक (LOTO) कर दिया गया है?"
            },
            "options": {
                "en": ["E-stop tripped and power locked", "Machine still freewheeling / rotating", "E-stop pressed but power live", "Cannot reach E-stop safely"],
                "hi": ["इमरजेंसी स्टॉप और पावर बंद", "मशीन अभी भी घूम रही है", "स्टॉप दबाया पर पावर चालू है", "स्टॉप तक पहुंचना असंभव"]
            }
        },
        {
            "slot": "entrapment_crush_status",
            "priority": 1,
            "description": "Whether any worker is entangled, crushed, or caught in moving parts",
            "clinical_intent": "Directs heavy extrication rescue tools rather than routine maintenance",
            "default_q": {
                "en": "Is any worker trapped, entangled, or pinned in the machinery or conveyor nip point?",
                "hi": "क्या कोई कर्मचारी मशीनरी या कन्वेयर बेल्ट में फंसा या दबा हुआ है?"
            },
            "options": {
                "en": ["Worker trapped in moving parts", "Worker struck by flying debris", "No worker entangled or injured", "Cannot verify machine interior"],
                "hi": ["कर्मचारी मशीन में फंसा हुआ है", "टुकड़े लगने से घायल", "कोई फंसा या घायल नहीं", "अंदर की पुष्टि नहीं"]
            }
        },
        {
            "slot": "structural_overload_collapse",
            "priority": 2,
            "description": "Secondary collapse hazard of galleries, counterweights, or conveyor frames",
            "clinical_intent": "Prevents secondary collapse onto rescue personnel",
            "default_q": {
                "en": "Is the conveyor gallery or machine support frame sagging or threatening to collapse?",
                "hi": "क्या कन्वेयर गैलरी या मशीन का ढांचा झुक रहा है या गिरने का खतरा है?"
            },
            "options": {
                "en": ["Structure sagging / cracking", "Heavy material load piled up", "Structure intact and stable", "Area beneath evacuated"],
                "hi": ["ढांचा झुक रहा है / दरारें", "भारी माल जमा हो गया है", "ढांचा स्थिर और सुरक्षित", "नीचे का क्षेत्र खाली कराया"]
            }
        }
    ],

    "confined_space_emergency": [
        {
            "slot": "rescue_entry_prohibition",
            "priority": 1,
            "description": "Strict prohibition of unequipped rescuers entering hazardous atmosphere",
            "clinical_intent": "Prevents multiple secondary rescuer fatalities (the #1 killer in confined spaces)",
            "default_q": {
                "en": "Confirm that NO workers enter the space without SCBA and airline apparatus?",
                "hi": "पुष्टि करें कि कोई भी बिना SCBA (सांस लेने का उपकरण) पहने अंदर जाने की कोशिश नहीं कर रहा?"
            },
            "options": {
                "en": ["Strictly barred — no entry without SCBA", "Worker attempted entry — stopped", "Rescuer entered with lifeline", "Hatch closed and guarded"],
                "hi": ["सख्त रोक — बिना SCBA प्रवेश नहीं", "प्रयास किया था — रोक दिया", "लाइफलाइन के साथ प्रवेश", "ढक्कन बंद और गार्ड तैनात"]
            }
        },
        {
            "slot": "victim_responsiveness_radio",
            "priority": 1,
            "description": "Communication status and responsiveness of personnel inside space",
            "clinical_intent": "Determines atmospheric toxicity speed and life support timeline",
            "default_q": {
                "en": "Are workers inside the space responding to radio or vocal calls?",
                "hi": "क्या अंदर मौजूद कर्मचारी रेडियो या आवाज का कोई उत्तर दे रहे हैं?"
            },
            "options": {
                "en": ["No response / unresponsive", "Faint vocal / tapping heard", "Workers conscious and communicating", "Visible on safety camera"],
                "hi": ["कोई जवाब नहीं / बेहोश", "धीमी आवाज या खटखटाहट", "होश में हैं और बात कर रहे", "कैमरे पर दिखाई दे रहे हैं"]
            }
        },
        {
            "slot": "forced_ventilation_status",
            "priority": 2,
            "description": "Operation of positive pressure fresh air blower into the manhole",
            "clinical_intent": "Purges toxic gases and restores oxygen levels for victims",
            "default_q": {
                "en": "Has the explosion-proof forced fresh-air blower been started into the manhole?",
                "hi": "क्या मैनहोल में ताजी हवा फेंकने वाला ब्लोअर तुरंत चालू कर दिया गया है?"
            },
            "options": {
                "en": ["Fresh air blower operating", "Blower being mobilized", "No blower available", "Natural ventilation only"],
                "hi": ["ताजी हवा का ब्लोअर चालू है", "ब्लोअर लाया जा रहा है", "ब्लोअर उपलब्ध नहीं है", "केवल प्राकृतिक हवा"]
            }
        }
    ],

    "crane_lifting_failure": [
        {
            "slot": "load_drop_zone_clearance",
            "priority": 1,
            "description": "Complete evacuation of personnel from under suspended or slipped load",
            "clinical_intent": "Zero fatalities if suspended load drops completely",
            "default_q": {
                "en": "Is the entire drop zone beneath and around the suspended load cleared of personnel?",
                "hi": "क्या लटके हुए भार के नीचे और आसपास का पूरा क्षेत्र कर्मचारियों से खाली करा लिया गया है?"
            },
            "options": {
                "en": ["Drop zone fully barricaded and empty", "Personnel still in vicinity", "Load landed safely on ground", "Cannot clear area"],
                "hi": ["नीचे का क्षेत्र खाली और बंद", "कर्मचारी अभी भी पास हैं", "भार जमीन पर रख दिया गया", "खाली कराना संभव नहीं"]
            }
        },
        {
            "slot": "crane_hoist_brake_status",
            "priority": 1,
            "description": "Mechanical engagement of emergency brakes and motor power cut",
            "clinical_intent": "Prevents catastrophic drum freewheeling or cable unspooling",
            "default_q": {
                "en": "Has crane power been cut and mechanical emergency hoist brake applied?",
                "hi": "क्या क्रेन की पावर काट दी गई है और मैकेनिकल इमरजेंसी ब्रेक लगा दिया गया है?"
            },
            "options": {
                "en": ["Emergency brake holding load", "Brake slipping slowly", "Power isolated at main switch", "Operator holding on control"],
                "hi": ["इमरजेंसी ब्रेक भार को रोके है", "ब्रेक धीरे-धीरे फिसल रहा है", "मेन स्विच से पावर काटी", "ऑपरेटर कंट्रोल पकड़े हुए है"]
            }
        },
        {
            "slot": "rigging_wire_integrity",
            "priority": 2,
            "description": "Physical condition of wire rope, slings, or crane hook latch",
            "clinical_intent": "Assesses imminent total severance risk",
            "default_q": {
                "en": "Is the wire rope snapped, unstranded, or is the hook latch broken?",
                "hi": "क्या वायर रोप टूट गई है, तार खुल रहे हैं, या हुक का लैच टूटा है?"
            },
            "options": {
                "en": ["Wire rope strands snapped / frayed", "Hook latch broken / sling slipped", "Complete cable failure occurred", "Rope appears intact on drum"],
                "hi": ["तार टूट रहे हैं / छिल गए", "हुक लैच टूटा / स्लिंग फिसला", "पूरी केबल टूट चुकी है", "ड्रम पर तार ठीक दिख रहा"]
            }
        }
    ],

    "vehicle_traffic_incident": [
        {
            "slot": "vehicle_occupant_entrapment",
            "priority": 1,
            "description": "Entrapment of drivers inside cabins or under roll-over protection cages",
            "clinical_intent": "Dispatches heavy hydraulic spreaders and cutters",
            "default_q": {
                "en": "Is any driver or worker trapped inside the vehicle cabin or under the wheels?",
                "hi": "क्या कोई ड्राइवर या कर्मचारी केबिन के अंदर या पहियों के नीचे दबा हुआ है?"
            },
            "options": {
                "en": ["Driver pinned / trapped in cabin", "Casualty under vehicle wheel", "All occupants exited safely", "Driver conscious and uninjured"],
                "hi": ["ड्राइवर केबिन में दबा/फंसा है", "पहिए के नीचे दबा है", "सभी सुरक्षित बाहर निकल आए", "ड्राइवर होश में और सुरक्षित"]
            }
        },
        {
            "slot": "hazardous_cargo_fuel_leak",
            "priority": 1,
            "description": "Puncture of fuel tanks or collision involving molten metal / chemical tankers",
            "clinical_intent": "Prevents explosive fires or toxic secondary disasters at road junctions",
            "default_q": {
                "en": "Is there a fuel leak, or was a hot metal or chemical vehicle involved in the crash?",
                "hi": "क्या गाड़ी से डीजल/ईंधन बह रहा है, या पिघली धातु/केमिकल की गाड़ी टकराई है?"
            },
            "options": {
                "en": ["Diesel fuel leaking heavily", "Molten metal / slag carrier involved", "Chemical tanker involved", "No leaks detected"],
                "hi": ["डीजल तेजी से बह रहा है", "पिघली धातु/स्लैग की गाड़ी है", "केमिकल टैंकर टकराया है", "कोई रिसाव नहीं दिख रहा"]
            }
        },
        {
            "slot": "traffic_route_blockage",
            "priority": 2,
            "description": "Blockage of arterial plant roads and emergency gates",
            "clinical_intent": "Reroutes responding ambulances and fire tenders",
            "default_q": {
                "en": "Is the roadway completely blocked, preventing emergency ambulance access?",
                "hi": "क्या रास्ता पूरी तरह बंद है जिससे एम्बुलेंस आने में रुकावट होगी?"
            },
            "options": {
                "en": ["Main road completely blocked", "One lane open for traffic", "Emergency detour available", "Road cleared to shoulder"],
                "hi": ["रास्ता पूरी तरह बंद है", "एक लेन खुली है", "दूसरा रास्ता उपलब्ध है", "गाड़ी किनारे कर दी गई"]
            }
        }
    ],

    "slip_fall": [
        {
            "slot": "spine_head_trauma_triage",
            "priority": 1,
            "description": "Consciousness, head impact, and cervical spine immobilization status",
            "clinical_intent": "Strict directive DO NOT MOVE casualty without spine board to avoid paralysis",
            "default_q": {
                "en": "Is the fallen worker conscious, and is the worker being kept STILL without moving the neck?",
                "hi": "क्या गिरा हुआ कर्मचारी होश में है, और क्या उसे बिना गर्दन हिलाए स्थिर रखा गया है?"
            },
            "options": {
                "en": ["Worker conscious — kept completely still", "Worker unconscious / unresponsive", "Head bleeding or vomiting", "Worker standing / walking"],
                "hi": ["होश में है — स्थिर रखा गया", "बेहोश है / कोई जवाब नहीं", "सिर से खून / उल्टी", "कर्मचारी खड़ा हो गया है"]
            }
        },
        {
            "slot": "fall_height_mechanism",
            "priority": 1,
            "description": "Height of fall and landing surface (scaffolding, ladder, grating, floor)",
            "clinical_intent": "Calculates trauma score to prepare ICU/orthopedic surgical team",
            "default_q": {
                "en": "From what height did the worker fall: ground level, ladder, or scaffolding above 2 meters?",
                "hi": "कर्मचारी कितनी ऊंचाई से गिरा: जमीन से, सीढ़ी से, या 2 मीटर से ऊंची मचान से?"
            },
            "options": {
                "en": ["Fell from scaffold > 2 meters", "Fell from ladder (1-2 meters)", "Fell into pit / grating opening", "Same-level slip on oil/water"],
                "hi": ["मचान से गिरा (> 2 मीटर)", "सीढ़ी से गिरा (1-2 मीटर)", "गड्ढे या नाले में गिरा", "जमीन पर तेल/पानी से फिसला"]
            }
        },
        {
            "slot": "fall_hazard_isolation",
            "priority": 2,
            "description": "Barricading open holes, missing grating, or slippery oil slicks",
            "clinical_intent": "Prevents immediate secondary falls by first responders",
            "default_q": {
                "en": "Has the open pit, missing floor grating, or oil slick been barricaded with warning tape?",
                "hi": "क्या खुले गड्ढे, हटी हुई जाली (grating), या तेल के बहाव पर चेतावनी घेरा लगा दिया गया है?"
            },
            "options": {
                "en": ["Hazard barricaded with tape", "Still open and hazardous", "Barricade being erected", "Area locked from access"],
                "hi": ["खतरे पर घेरा लगा दिया गया", "अभी भी खुला और खतरनाक है", "घेरा लगाया जा रहा है", "रास्ता ताला लगाकर बंद"]
            }
        }
    ]
}
