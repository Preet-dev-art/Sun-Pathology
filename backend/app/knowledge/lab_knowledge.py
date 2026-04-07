"""
lab_knowledge.py
Sun Pathology Laboratory & Research Institute
Production-Grade Knowledge Base

Changes from v1:
  1. Added Gujarati keywords to category_keywords (was Hindi/English only)
  2. Added BOOKING category (was missing — home collection queries need their own category)
  3. Added CORPORATE category (was missing)
  4. Added language detection helper (detect_language)
  5. classify_query() now returns priority-ordered category (avoids ambiguous overlap)
  6. get_nearest_branch() helper for location queries
  7. get_faq_answer() for direct FAQ lookups before hitting Gemini
  8. Sattadhar directions typo fixed
"""

from typing import Optional

# ─────────────────────────────────────────────────────────────────────────────
# MAIN LAB INFO DICT (unchanged from v1, single source of truth)
# ─────────────────────────────────────────────────────────────────────────────

lab_info = {
    "name": "सन पैथोलॉजी लैब और रिसर्च इंस्टीट्यूट",
    "nameEnglish": "Sun Pathology Laboratory and Research Institute",
    "established": 1998,
    "experienceYears": 27,
    "tagline": "A Complete Guide to Diagnostic Excellence",

    "organization": {
        "headquarters": "Ahmedabad, Gujarat",
        "branches": ["Science City", "Thaltej", "Satellite", "Akhbarnagar", "Maninagar", "Bopal", "Gota", "Vastral", "Shahibaug", "Sattadhar"],
        "certifications": ["ISO 9000:2015", "NABL Accreditation", "Six Sigma Performance (126 parameters)", "US FDA-Approved Diagnostic Instruments"],
        "equipment": ["Vitros 5600 and 7600 Integrated Dry Chemistry Analyzers", "Sysmex Hematology and Coagulation Analyzers", "Ortho Workstation Blood Group Analyzer", "Total Lab Automation"],
        "features": ["Less Pain Needle Technology (ideal for kids/elderly)", "AI-Based WhatsApp Services (079 6700 6700)"],
        "pathologists": ["Dr. Arpita Shah", "Dr. Harsha Pandya", "Dr. Anand Parikh"]
    },

    "achievements": {
        "milestones": "1.9 Million+ Health Check-Ups, 30 Million+ Tests Conducted, 35+ Corporate Collaborations",
        "awards": ["Best Pathology Lab of Ahmedabad", "Pride of Nation Award", "Legend of Gujarat Award", "Emerging Gujarat Award"]
    },

    "workingHours": {
        "sampleCollection": {
            "start": "6:00 AM",
            "note": "Home collection and walk-in sample collection starts from 6 AM"
        },
        "weekdays": {
            "open": "7:00 AM",
            "close": "8:00 PM",
            "hindi": "सैंपल 6 बजे से, लैब सुबह 7 बजे से रात 8 बजे तक (सोमवार से शनिवार)"
        },
        "sunday": {
            "open": "7:00 AM",
            "close": "8:00 PM",
            "note": "FULLY OPEN. Sample collection from 6 AM.",
            "hindi": "सैंपल 6 बजे से, लैब 7 बजे से रात 8 बजे तक (रविवार सहित)"
        },
        "holidays": {
            "open": "7:00 AM",
            "close": "8:00 PM",
            "note": "Open on most public holidays. Call 079-67006700 to confirm.",
            "hindi": "सैंपल 6 बजे से, लैब 7 बजे से रात 8 बजे तक"
        }
    },

    "location": {
        "primaryHeadquarters": "Ahmedabad, Gujarat",
        "mainLabAddress": "1st Floor, Saptak Corporate House, Near Shukan Mall, Opposite SBI Bank, Science City Main Road, Ahmedabad",
        "allBranches": [
            {
                "name": "Science City",
                "address": "Science City Road, Sola",
                "landmark": "CIMS Hospital के सामने / Opposite CIMS Hospital",
                "directions": "सोला ब्रिज से साइंस सिटी की तरफ जाते हुए बायीं तरफ (Left side coming from Sola Bridge).",
                "areas_served": ["Science City", "Sola", "Ghatlodiya", "Chandkheda"]
            },
            {
                "name": "Thaltej",
                "address": "S.G. Highway, Thaltej",
                "landmark": "Acropolis Mall के पास / Near Acropolis Mall",
                "directions": "SG हाईवे सर्विस रोड पर, PVR Acropolis के ठीक आगे (On service road just past PVR).",
                "areas_served": ["Thaltej", "Bodakdev", "Prahlad Nagar", "SG Highway"]
            },
            {
                "name": "Satellite",
                "address": "132 Ring Road, Satellite",
                "landmark": "Shivranjani Crossroads के पास / Near Shivranjani",
                "directions": "शिवरंजनी से नेहरूनगर की तरफ 200 मीटर आगे दायीं तरफ.",
                "areas_served": ["Satellite", "Shivranjani", "Nehrunagar", "Jodhpur"]
            },
            {
                "name": "Akhbarnagar",
                "address": "Akhbarnagar Circle, Nava Vadaj",
                "landmark": "Akhbarnagar BRTS Stop के पास / Near BRTS",
                "directions": "अखबारनगर अंडरपास सर्कल के बिल्कुल पास.",
                "areas_served": ["Akhbarnagar", "Nava Vadaj", "Sabarmati", "New Vadaj"]
            },
            {
                "name": "Maninagar",
                "address": "Kankaria Road, Maninagar",
                "landmark": "Kankaria Lake Gate 1 के सामने / Opp Kankaria Gate 1",
                "directions": "कांकरिया लेक के मुख्य टिकट काउंटर के ठीक सामने.",
                "areas_served": ["Maninagar", "Kankaria", "Gomtipur", "Bapunagar"]
            },
            {
                "name": "Bopal",
                "address": "Bopal-Ambli Road, Bopal",
                "landmark": "Bopal TRP Mall के पास / Near TRP Mall",
                "directions": "इस्कॉन से आते समय TRP मॉल से आधा किलोमीटर पहले.",
                "areas_served": ["Bopal", "Ambli", "South Bopal", "Shilaj"]
            },
            {
                "name": "Gota",
                "address": "Gota Crossroads, SG Highway",
                "landmark": "Vande Mataram City के पास / Near Vande Mataram",
                "directions": "गोटा में वन्दे मातरम बिल्डिंग के पास.",
                "areas_served": ["Gota", "New Ranip", "Tragad", "Motera"]
            },
            {
                "name": "Vastral",
                "address": "Vastral Ring Road",
                "landmark": "Nirant Cross Road Metro Station के पास / Near Metro",
                "directions": "निरंत क्रॉस रोड मेट्रो स्टेशन से वॉकिंग डिस्टेंस पर.",
                "areas_served": ["Vastral", "Amraiwadi", "Odhav", "Vinzol"]
            },
            {
                "name": "Shahibaug",
                "address": "Shahibaug Underbridge",
                "landmark": "Rajasthan Hospital के पास / Near Rajasthan Hospital",
                "directions": "राजस्थान हॉस्पिटल से सिर्फ 100 मीटर की दूरी पर.",
                "areas_served": ["Shahibaug", "Civil Hospital", "Ankur", "Naranpura"]
            },
            {
                "name": "Sattadhar",
                "address": "Sattadhar Crossroads, Ghatlodiya",
                "landmark": "Sattadhar Society के पास / Near Sattadhar Society",
                "directions": "सत्ताधार क्रॉसरोड मुख्य सर्कल पर ही (Right at the Sattadhar crossroad main circle).",
                "areas_served": ["Sattadhar", "Ghatlodiya", "Sola", "Jawahar Nagar"]
            }
        ]
    },

    "tests": {
        "blood": [
            {"name": "सीबीसी (Complete Blood Count)", "price": 170, "time": "6-8 hours", "fasting": False},
            {"name": "हीमोग्लोबिन", "price": 80, "time": "6-8 hours", "fasting": False},
            {"name": "फास्टिंग शुगर", "price": 80, "time": "6-8 hours", "fasting": True},
            {"name": "पीपी शुगर (Post Prandial)", "price": 80, "time": "6-8 hours", "fasting": False},
            {"name": "HbA1c", "price": 350, "time": "6-8 hours", "fasting": False},
            {"name": "थायरॉइड प्रोफाइल (T3, T4, TSH)", "price": 550, "time": "6-8 hours", "fasting": False},
            {"name": "TSH", "price": 250, "time": "6-8 hours", "fasting": False},
            {"name": "लिपिड प्रोफाइल", "price": 350, "time": "6-8 hours", "fasting": True},
            {"name": "किडनी फंक्शन टेस्ट (KFT)", "price": 550, "time": "6-8 hours", "fasting": False},
            {"name": "लिवर फंक्शन टेस्ट (LFT)", "price": 650, "time": "6-8 hours", "fasting": False},
            {"name": "विटामिन डी", "price": 600, "time": "6-8 hours", "fasting": False},
            {"name": "विटामिन बी12", "price": 400, "time": "6-8 hours", "fasting": False},
            {"name": "आयरन प्रोफाइल", "price": 450, "time": "6-8 hours", "fasting": False},
            {"name": "कैल्शियम", "price": 150, "time": "6-8 hours", "fasting": False},
            {"name": "यूरिक एसिड", "price": 150, "time": "6-8 hours", "fasting": False},
            {"name": "क्रिएटिनिन", "price": 120, "time": "6-8 hours", "fasting": False},
            {"name": "ब्लड ग्रुप", "price": 100, "time": "6-8 hours", "fasting": False},
            {"name": "डेंगू टेस्ट", "price": 350, "time": "6-8 hours", "fasting": False},
            {"name": "मलेरिया टेस्ट", "price": 150, "time": "6-8 hours", "fasting": False},
            {"name": "टाइफाइड टेस्ट (Widal)", "price": 150, "time": "6-8 hours", "fasting": False}
        ],
        "urine": [
            {"name": "यूरिन रूटीन", "price": 70, "time": "6-8 hours", "fasting": False},
            {"name": "यूरिन कल्चर", "price": 350, "time": "48-72 hours", "fasting": False},
            {"name": "यूरिन माइक्रोएल्ब्युमिन", "price": 300, "time": "6-8 hours", "fasting": False}
        ],
        "stool": [
            {"name": "स्टूल रूटीन", "price": 80, "time": "6-8 hours", "fasting": False},
            {"name": "स्टूल कल्चर", "price": 450, "time": "48-72 hours", "fasting": False}
        ],
        "packages": [
            {"name": "बेसिक हेल्थ चेकअप", "price": 999, "originalPrice": None, "discount": None, "time": "6-8 hours", "includes": "CBC, Sugar, Urine, LFT"},
            {"name": "फुल बॉडी चेकअप", "price": 2499, "originalPrice": None, "discount": None, "time": "6-8 hours", "includes": "70+ tests"},
            {"name": "डायबिटीज़ पैकेज", "price": 799, "originalPrice": None, "discount": None, "time": "6-8 hours", "includes": "Fasting Sugar, PP Sugar, HbA1c, KFT"},
            {"name": "थायरॉइड पैकेज", "price": 699, "originalPrice": None, "discount": None, "time": "6-8 hours", "includes": "T3, T4, TSH"},
            {"name": "हार्ट पैकेज", "price": 1499, "originalPrice": None, "discount": None, "time": "6-8 hours", "includes": "Lipid Profile, ECG, CBC"},
            {"name": "Allergy Profile", "price": 3000, "originalPrice": 7000, "discount": "57%", "time": "12-48 hours", "includes": "Food Allergy, Inhalant Allergy, Drug Allergy, Contact Allergy"},
            {"name": "Food Intolerance Testing", "price": 6500, "originalPrice": 10000, "discount": "35%", "time": "12-48 hours", "includes": "Bloating, Diarrhea or IBS, Headache, Chronic Fatigue, Depression, Skin Problems, Weight Control, Arthritis"},
            {"name": "Alcohol Impact Profile", "price": 600, "originalPrice": 3550, "discount": "85%", "time": "6-8 hours", "includes": "CBC, Urine RM, RBS, SGPT, SGOT, Creatinine, Alkaline Phosphate, GGT, Total Bilirubin"},
            {"name": "Hypertension Health Package (Basic)", "price": 3150, "originalPrice": 6900, "discount": "54%", "time": "6-8 hours", "includes": "CBC, Bl.Urea, Creatinine, Sodium, Potassium, Lipid Profile, Homocysteine, HS CRP, HbA1c, Urinary Alb./Cre. Ratio, TSH, Vitamin B12, Cortisol am, Cortisol pm"},
            {"name": "Hypertension Health Package (Complete)", "price": 4150, "originalPrice": 8700, "discount": "52%", "time": "6-8 hours", "includes": "CBC, Bl.Urea, Creatinine, Sodium, Potassium, Lipid Profile, Homocysteine, HS CRP, HbA1c, Urinary Alb./Cre. Ratio, TSH, Vitamin B12, Cortisol am, Cortisol pm, NT Pro BNP"},
            {"name": "Obesity Profile", "price": 850, "originalPrice": 2850, "discount": "70%", "time": "6-8 hours", "includes": "CBC, ESR, Urine RM, FBS, Creatinine, Uric Acid, SGPT, Lipid Profile, T3, T4, TSH"},
            {"name": "Metabolic Panel (Basic)", "price": 1350, "originalPrice": 5250, "discount": "74%", "time": "6-8 hours", "includes": "CBC, ESR, Urine RM, FBS, Bl.Urea, BUN, Creatinine, Uric Acid, Sodium, Potassium, Chloride, Calcium, Phosphorous, SGPT, SGOT, Total Bilirubin, Alkaline Phosphate, Total Protein, Albumin, Globulin, A:G Ratio, Lipid Profile"},
            {"name": "Metabolic Panel (Complete)", "price": 1950, "originalPrice": 7950, "discount": "75%", "time": "6-8 hours", "includes": "Basic Metabolic Panel, Insulin (Fasting & PPBS), Cortisol am & pm, PTH"},
            {"name": "PCOD Profile (Basic)", "price": 1050, "originalPrice": 2500, "discount": "58%", "time": "6-8 hours", "includes": "TSH, FSH, LH, Prolactin, HbA1c"},
            {"name": "PCOD Profile (Extended)", "price": 2550, "originalPrice": 4800, "discount": "46%", "time": "6-8 hours", "includes": "TSH, FSH, LH, Prolactin, HbA1c, CA - 125, Insulin (FBS & PPBS), Cortisol am & pm"},
            {"name": "Torch Profile", "price": 1200, "originalPrice": 2400, "discount": "50%", "time": "6-8 hours", "includes": "Toxoplasma IgG & IgM, Rubella IgG & IgM, CMV IgG & IgM, HSV - I & II IgG & IgM"},
            {"name": "Male Fertility Profile (Basic)", "price": 1200, "originalPrice": 2400, "discount": "50%", "time": "6-8 hours", "includes": "TSH, Testosterone, Seminal Fluid Examination, HbA1c"},
            {"name": "Male Fertility Profile (Full)", "price": 3000, "originalPrice": 6000, "discount": "50%", "time": "6-8 hours", "includes": "TSH, FSH, LH, Prolactin, Testosterone, Free Testosterone, HbA1c, Seminal Fluid Examination, Anti Sperm Antibody"},
            {"name": "Pre Marriage Profile (Male)", "price": 1950, "originalPrice": 4800, "discount": "59%", "time": "6-8 hours", "includes": "CBC, RBS, HIV by CLIA, HBsAg by CLIA, VDRL, Blood Group, Testosterone, Hb Electrophoresis, Seminal Fluid Examination"},
            {"name": "Pre Marriage Profile (Female)", "price": 3150, "originalPrice": 6000, "discount": "47%", "time": "6-8 hours", "includes": "CBC, RBS, FSH, LH, Prolactin, Anti Mullerian Hormone (AMH), HIV by CLIA, HBsAg by CLIA, VDRL, Blood Group, Hb Electrophoresis"},
            {"name": "Anaemia Profile (Basic)", "price": 1350, "originalPrice": 4100, "discount": "67%", "time": "6-8 hours", "includes": "CBC, Iron, TIBC, % Transferrin Saturation, Ferritin, Folic Acid, Retic Count, Vitamin B12"},
            {"name": "Arthritic Profile", "price": 600, "originalPrice": 1200, "discount": "50%", "time": "6-8 hours", "includes": "CBC, ESR, RBS, Uric Acid, RA (Quantitative)"},
            {"name": "Osteoporosis Profile", "price": 2050, "originalPrice": 4650, "discount": "55%", "time": "6-8 hours", "includes": "CBC, ESR, RBS, Uric Acid, Calcium, Phosphorous, RA (Quantitative), Cortisol am & pm, Vitamin B12 Level, Vitamin D"},
            {"name": "Cardiac Profile (Basic)", "price": 1700, "originalPrice": 5450, "discount": "68%", "time": "6-8 hours", "includes": "CBC, RBS, Creatinine, EGFR, Sodium, Potassium, Chloride, Lipid Profile, Homocysteine, Hs Troponin-I, CPK MB, HS CRP"},
            {"name": "Cardiac Profile (Advanced)", "price": 3500, "originalPrice": 9450, "discount": "62%", "time": "6-8 hours", "includes": "CBC, RBS, Creatinine, EGFR, Sodium, Potassium, Chloride, Lipid Profile, Homocysteine, hs Troponin-I, CPK MB, HS CRP, NT Pro - BNP, Apolipoprotein A1, Apolipoprotein B, Lipoprotein (a)"},
            {"name": "Lipid Profile (Basic)", "price": 350, "originalPrice": 700, "discount": "50%", "time": "6-8 hours", "includes": "Cholesterol, Triglyceride, HDL, LDL, VLDL, Total Lipid"},
            {"name": "Thyroid Profile (Basic)", "price": 300, "originalPrice": 600, "discount": "50%", "time": "6-8 hours", "includes": "T3, T4, TSH"},
            {"name": "Thyroid Profile (Advanced)", "price": 300, "originalPrice": 850, "discount": "64%", "time": "6-8 hours", "includes": "Free T3, Free T4, TSH"},
            {"name": "Cancer Screening Package (Female)", "price": 6650, "originalPrice": None, "discount": None, "time": "6-8 hours", "includes": "CBC, CA 19.9, CEA, AFP, CA 15.3, CA 125, Beta HCG, Protein Electrophoresis"},
            {"name": "Cancer Screening Package (Male)", "price": 2700, "originalPrice": None, "discount": None, "time": "6-8 hours", "includes": "CBC, CA 19.9, CEA, AFP, Beta HCG, PSA, Free PSA, Protein Electrophoresis"},
            {"name": "Antenatal Profile (Basic)", "price": 500, "originalPrice": 3150, "discount": "84%", "time": "6-8 hours", "includes": "CBC, Urine RM, RBS, HIV by CLIA, HBsAg by CLIA, VDRL, Blood Group"},
            {"name": "Pre Operative Profile (Basic)", "price": 750, "originalPrice": 3100, "discount": "75%", "time": "6-8 hours", "includes": "CBC, Urine RM, RBS, Creatinine, BT-CT, HIV by CLIA, HBsAg by CLIA, Blood Group"},
            {"name": "Full Body Check-up (Diabetic)", "price": 1050, "originalPrice": 5730, "discount": "81%", "time": "6-8 hours", "includes": "CBC, Urine RM, FBS, PPBS, HbA1c, Bl.Urea, BUN, Creatinine, EGFR, Uric Acid, Calcium, Sodium, Potassium, Chloride, Phosphorous, Lipid Profile, SGPT, Urine Microalbumin"},
            {"name": "Full Body Check-up (Customer's Choice)", "price": 4500, "originalPrice": 17950, "discount": "75%", "time": "6-8 hours", "includes": "CBC, ESR, Urine RM, FBS, PPBS, HbA1c, Bl.Urea, Creatinine, EGFR, BUN, Uric Acid, Sodium, Potassium, Chloride, SGPT, SGOT, Total Protein, Albumin, Globulin, Total Bilirubin, Alkaline Phosphate, Calcium, Lipid Profile, RA, Iron Level, TIBC, Ferritin, Folic Acid, Homocysteine, Apolipoprotein A1, Apolipoprotein B, Hs.CRP, IgE Level, Free T3, Free T4, TSH, PSA / CA-125, Vitamin B12, Vitamin D"},
            {"name": "Full Body Check-up (Super Executive)", "price": 5000, "originalPrice": 18850, "discount": "73%", "time": "6-8 hours", "includes": "CBC, ESR, Urine RM, FBS, Bl.Urea, BUN, Creatinine, EGFR, Uric Acid, Calcium, Phosphorous, Sodium, Potassium, Chloride, SGPT, SGOT, Total Bilirubin, Total Protein, Albumin, Globulin, Alkaline Phosphate, Lipid Profile, RA, HbA1c, Iron Level, TIBC, Ferritin, Magnesium, Folic Acid, Homocysteine, Apolipoprotein A1, Apolipoprotein B, Blood Group, IgE Level, Free T3, Free T4, TSH, PSA / CA-125, Vitamin B12, Vitamin D, HIV by CLIA, HBsAg by CLIA, VDRL"},
        ]
    },

    "services": {
        "homeSampleCollection": {
            "available": True,
            "timing": "6:00 AM to 8:00 PM (including Sundays and holidays)",
            "charges": {
                "under_350": 100,
                "between_350_649": 50,
                "above_650": 0
            },
            "booking": "Call 079-67006700. Preferred to book a day in advance.",
            "coverage": "Across Ahmedabad — approximately 5 km radius from each branch"
        },
        "reportDelivery": {
            "whatsapp": True,
            "sms": True,
            "email": True,
            "online_portal": True,
            "hard_copy": True,
            "note": "WhatsApp PDF is the primary and fastest delivery method"
        },
        "payment": {
            "cash": True,
            "upi": True,
            "credit_card": True,
            "debit_card": True,
            "pos_at_lab": True,
            "online": True,
            "policy": "You can make payment in the following ways: Credit card or debit card from our website, UPI payment through our website, POS machine at the laboratory premises, or Cash payment at the laboratory.",
            "insurance": "Tie-up with select insurance panels",
            "gst": False,
            "gst_note": "No GST charged — Sun Pathology is classified as a medical firm"
        }
    },

    "expertInsights": {
        "CBC": "CBC टेस्ट से इन्फेक्शन, एनीमिया और रोग प्रतिरोधक क्षमता का पता चलता है। इसमें हीमोग्लोबिन और प्लेटलेट्स की जांच होती है।",
        "Thyroid": "थायरॉइड शरीर के मेटाबॉलिज्म को कंट्रोल करता है। इसकी जांच हार्मोनल असंतुलन जानने के लिए ज़रूरी है।",
        "LipidProfile": "कोलेस्ट्रॉल की जांच हार्ट हेल्थ के लिए ज़रूरी है। 10-12 घंटे की फास्टिंग इसलिए चाहिए ताकि खाने का असर ब्लड फैट्स पर न पड़े। ध्यान रहे, 12 घंटे से ज्यादा भूखे रहने से रिपोर्ट गलत आती है।",
        "Diabetes": "फास्टिंग शुगर और HbA1c से पिछले 3 महीनों का शुगर एवरेज पता चलता है। फास्टिंग शुगर में 10-12 घंटे से ज्यादा का उपवास नुकसानदायक है।",
        "KFT": "किडनी फंक्शन टेस्ट से पता चलता है कि आपके गुर्दे खून को सही से साफ कर रहे हैं या नहीं।",
        "VitaminD": "हड्डियों की मजबूती और इम्युनिटी के लिए विटामिन डी बहुत ज़रूरी है।",
        "LFT": "लिवर फंक्शन टेस्ट से पता चलता है कि आपका लिवर सही से काम कर रहा है या नहीं। SGPT/SGOT के स्तर से लिवर की सेहत का पता चलता है।",
        "Hemoglobin": "हीमोग्लोबिन की कमी से एनीमिया होता है — थकान, कमजोरी और सांस फूलना इसके लक्षण हैं।"
    },

    "policies": {
        "refund": "Refunds are processed only for cancellations made before sample collection.",
        "confidentiality": "All patient information is securely stored and shared only with authorized individuals.",
        "turnaround": "Routine tests: same day. Culture tests: 48-72 hours. Special tests: as specified.",
        "taxes": "No GST Charges — Sun Pathology is a medical firm; GST is not applicable.",
        "reportGuidance": "The laboratory does not provide medical consultations, but can briefly explain what a test measures.",
        "walkin": "No appointment required for walk-in patients. Just arrive between 7 AM and 8 PM.",
        "escalation": "Dr. Mayank Joshi (Laboratory Director) — 9276843433 — for medical interpretation and corporate/society inquiries."
    },

    "contact": {
        "phone": "079-67006700",
        "whatsapp": "079 6700 6700",
        "escalation_doctor": "Dr. Mayank Joshi",
        "escalation_number": "9276843433",
        "website": "www.sunpathology.in"
    },
    "faq": {} # Deprecated: FAQ logic has moved to faq_database.json for 900+ multi-lingual scaling
}

import os
import json
FAQ_DB_CACHE = None

def load_faq_database():
    global FAQ_DB_CACHE
    if FAQ_DB_CACHE is not None:
        return FAQ_DB_CACHE
    
    db_path = os.path.join(os.path.dirname(__file__), "faq_database.json")
    try:
        with open(db_path, "r", encoding="utf-8") as f:
            FAQ_DB_CACHE = json.load(f)
    except FileNotFoundError:
        FAQ_DB_CACHE = {"en": {}, "hi": {}, "gu": {}}
    return FAQ_DB_CACHE


# ─────────────────────────────────────────────────────────────────────────────
# QUERY CATEGORIES
# ─────────────────────────────────────────────────────────────────────────────

query_categories = {
    "REPORT": "Report Status",
    "BOOKING": "Home Collection Booking",     # NEW — was missing
    "LOCATION": "Location / Branch",
    "TIMING": "Timings",
    "TESTS": "Tests & Preparation",
    "PRICING": "Pricing",
    "CORPORATE": "Corporate / Society Inquiry",  # NEW — was missing
    "GENERAL": "General",
    "OTHER": "Other"
}

# Keywords for category detection — now includes Gujarati + more Hindi
category_keywords = {
    "REPORT": [
        # Hindi
        "रिपोर्ट", "रिजल्ट", "कब मिलेगी", "कब आएगी", "तैयार", "स्टेटस", "नहीं मिली",
        # Gujarati
        "રિપોર્ટ", "ક્યારે મળશે", "રિઝલ્ટ", "તૈયાર",
        # English
        "report", "result", "when will", "not received", "status"
    ],
    "BOOKING": [
        # Hindi
        "घर पर", "घर आकर", "होम कलेक्शन", "होम विजिट", "सैंपल लेने आओ", "घर से लेंगे",
        # Gujarati
        "ઘરે", "ઘર પર", "હોમ કલેક્શન", "ઘરે આવો",
        # English
        "home collection", "home visit", "collect from home", "come to my house", "book home"
    ],
    "LOCATION": [
        # Hindi
        "कहाँ", "पता", "एड्रेस", "रास्ता", "कैसे आएं", "लोकेशन", "नजदीक", "ब्रांच",
        # Gujarati
        "ક્યાં", "સરનામું", "રસ્તો", "નજીક", "શાખા", "કઈ જગ્યા",
        # English
        "address", "location", "branch", "near", "directions", "where", "nearest"
    ],
    "TIMING": [
        # Hindi
        "समय", "कब खुलता", "कब बंद", "टाइमिंग", "रविवार", "शनिवार", "छुट्टी",
        # Gujarati
        "સમય", "ક્યારે ખુલે", "ક્યારે બંધ", "રવિવાર", "શનિવાર", "સોમ",
        # English
        "time", "open", "close", "timing", "sunday", "holiday", "hours", "when"
    ],
    "TESTS": [
        # Hindi
        "टेस्ट", "जांच", "ब्लड", "शुगर", "थायरॉइड", "यूरिन", "CBC", "सीबीसी",
        "फास्टिंग", "खाली पेट", "तैयारी", "क्या पीना", "क्या खाना",
        # Gujarati
        "ટેસ્ટ", "તપાસ", "ફાસ્ટિંગ", "ખાલી પેટ", "CBC", "BSL",
        # English
        "test", "blood", "urine", "fasting", "preparation", "sample", "how to prepare"
    ],
    "PRICING": [
        # Hindi
        "कितने", "कितना", "पैसे", "रुपये", "दाम", "चार्ज", "फीस", "कितना लगेगा",
        # Gujarati
        "કેટલા", "રૂપિયા", "ભાવ", "ચાર્જ", "ફી", "કિંમત",
        # English
        "price", "cost", "charge", "fee", "how much", "rupees", "rate"
    ],
    "CORPORATE": [
        # Hindi
        "कंपनी", "कॉर्पोरेट", "ऑफिस", "कर्मचारी", "सोसाइटी", "ग्रुप", "कैंप",
        # Gujarati
        "કંપની", "ઓફિસ", "કર્મચારી", "સોસાયટી", "ગ્રૂપ", "કેમ્પ",
        # English
        "company", "corporate", "office", "employees", "society", "group", "camp", "bulk"
    ],
}


# ─────────────────────────────────────────────────────────────────────────────
# HELPER FUNCTIONS
# ─────────────────────────────────────────────────────────────────────────────

def detect_language(text: str) -> str:
    """
    Detect the primary language of a message using GRAMMAR, not just script.

    The Sarvam STT often transcribes Hindi speech using Gujarati letters when
    the session language is set to 'gu'. So we cannot rely on Unicode ranges
    alone. Instead we check for common Hindi function words (written in both
    Devanagari AND Gujarati script) to detect when Hindi grammar is present
    despite Gujarati letters.

    Returns:
        "hi" — Hindi grammar detected (regardless of script)
        "gu" — Gujarati grammar detected
        "en" — English (default)
    """
    if not text:
        return "en"

    text_lower = text.lower().strip()

    # ── Step 1: Check for Hindi grammar words written in GUJARATI script ──
    # These are extremely common Hindi function words that do NOT exist in
    # natural Gujarati. If we find them, it's Hindi spoken & mis-transcribed.
    hindi_words_in_gujarati_script = [
        # Pronouns / particles
        "મુજે", "મૈં", "મૈ", "મેરા", "મેરી", "મેરે",
        "હમ", "હમારા", "હમારી", "હમારે", "હમે", "હમેં",
        "આપકા", "આપકી", "આપકે", "આપકો", "તુમ", "તુમ્હારા",
        # Verbs / auxiliaries
        "હૈ", "હૈં", "હું", "થા", "થી", "થે",
        "કરના", "કરતા", "કરતી", "કરો", "કરે", "કરેં",
        "ચાહિએ", "ચાહતા", "ચાહતી",
        "હોતા", "હોતી", "હોતે",
        "બતાઓ", "બતાઈએ", "બોલો",
        "દીજિએ", "કીજિએ", "લીજિએ",
        "સકતા", "સકતી", "સકતે",
        "કરવાના", "કરાના", "કરવાની",
        # Common Hindi postpositions
        "કા", "કી", "કે", "સે", "મેં", "પર", "કો",
        "વાલા", "વાલી", "વાલે",
        # Question words
        "ક્યા", "કૈસે", "કૈસા", "કૈસી",
        "કિતના", "કિતની", "કિતને",
        "કબ", "કહાં", "કિસ", "કિસકા",
        # Common verbs / phrases
        "કરવાના", "કરાના", "જાનના", "જાનકારી",
        "દેના", "લેના", "આના", "જાના",
        "પતા", "માલૂમ",
        # Negation
        "નહીં", "નહિ", "મત",
        # Conjunctions
        "ઔર", "યા", "લેકિન", "ઇસલિએ",
    ]

    # ── Step 2: Check for Hindi grammar words in Devanagari script ──
    hindi_words_in_devanagari = [
        "मुझे", "मैं", "मेरा", "मेरी", "हम", "हमें",
        "आपका", "आपकी", "तुम", "है", "हैं", "था", "थी",
        "करना", "चाहिए", "बताइए", "बताओ", "दीजिए",
        "क्या", "कैसे", "कितना", "कब", "कहाँ",
        "नहीं", "और", "या", "लेकिन",
        "करवाना", "जानकारी", "जानना",
    ]

    # Tokenize the text
    words = text_lower.split()

    # Count grammar matches
    hindi_gu_script_hits = sum(1 for w in words if w in hindi_words_in_gujarati_script)
    hindi_dev_hits = sum(1 for w in words if w in hindi_words_in_devanagari)

    # ── Step 3: Script-based counting ──
    gujarati_count = sum(1 for ch in text if '\u0A80' <= ch <= '\u0AFF')
    devanagari_count = sum(1 for ch in text if '\u0900' <= ch <= '\u097F')
    latin_count = sum(1 for ch in text if 'a' <= ch.lower() <= 'z')

    # ── Step 4: Decision logic ──
    # If Hindi grammar words are found (in either script), it's Hindi
    if hindi_dev_hits > 0:
        return "hi"
    if hindi_gu_script_hits >= 1:
        return "hi"

    # Pure script-based fallback
    if gujarati_count > devanagari_count and gujarati_count > latin_count:
        return "gu"
    if devanagari_count > 0:
        return "hi"
    return "en"


def classify_query(text: str) -> str:
    """
    Classify a patient query into one of the defined categories.

    Priority order (matters when keywords overlap):
        REPORT > BOOKING > PRICING > LOCATION > TIMING > TESTS > CORPORATE > GENERAL

    Returns:
        A key from query_categories, e.g. "REPORT", "PRICING", etc.
    """
    if not text:
        return "GENERAL"

    text_lower = text.lower()

    priority_order = ["REPORT", "BOOKING", "PRICING", "LOCATION", "TIMING", "TESTS", "CORPORATE"]

    for category in priority_order:
        keywords = category_keywords.get(category, [])
        if any(kw.lower() in text_lower for kw in keywords):
            return category

    return "GENERAL"


def get_nearest_branch(area_query: str) -> Optional[dict]:
    """
    Try to find the most relevant branch for an area/locality query.

    Args:
        area_query: patient's area or locality name

    Returns:
        Branch dict from lab_info["location"]["allBranches"], or None if no match.
    """
    if not area_query:
        return None

    query_lower = area_query.lower()

    for branch in lab_info["location"]["allBranches"]:
        # Check branch name
        if branch["name"].lower() in query_lower:
            return branch

        # Check served areas
        for area in branch.get("areas_served", []):
            if area.lower() in query_lower or query_lower in area.lower():
                return branch

        # Check address and landmark
        if (branch["address"].lower() in query_lower or
                any(word in query_lower for word in branch["address"].lower().split(","))):
            return branch

    return None


def get_faq_answer(query: str) -> Optional[str]:
    """
    Try to answer from FAQ directly before calling Gemini.
    Reads from the highly scalable trilingual faq_database.json.
    """
    if not query:
        return None

    query_lower = query.lower().strip()

    # ── Guard against negations (false positives) ──────────────
    negation_words = {"not", "nahi", "nathi", "don't", "dont", "no"}
    query_words = set(query_lower.split())
    if query_words.intersection(negation_words):
        # If the user says "I do NOT want...", let Gemini handle the nuance
        return None

    faq_db = load_faq_database()
    
    # ── Match across all languages ──────────────
    for lang_dict in faq_db.values():
        for question, answer in lang_dict.items():
            question_lower = question.lower()
            # Strict match for very short queries to prevent false positives
            if len(query_lower) < 10:
                if query_lower == question_lower:
                    return answer
            # Flexible match for normal length
            elif question_lower in query_lower or query_lower in question_lower:
                return answer

    # Common patterns not in FAQ keys
    if any(w in query_lower for w in ["sunday", "रविवार", "રવિવાર"]):
        return lab_info["faq"].get("क्या रविवार को खुले हैं")

    if any(w in query_lower for w in ["appointment", "book", "बुकिंग", "appointment chahiye"]):
        return "No appointment is needed for walk-in visits. Just come to any Sun Pathology branch between 7 AM and 8 PM."

    if any(w in query_lower for w in ["gst", "tax", "टैक्स"]):
        return lab_info["policies"]["taxes"]

    return None