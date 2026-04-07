# generate_faqs.py
import json
import time
from deep_translator import GoogleTranslator

# The base English QA pairs derived from the Training Manual
en_faqs = {
    # GENERAL
    "what are your lab timings": "Sun Pathology centers are open from 7 AM to 8 PM, with sample collection starting at 6 AM.",
    "do you provide home collection": "Yes, we provide home sample collection across Ahmedabad.",
    "how can i book a test": "You can book a test by providing your mobile number, name, address, and preferred time slot right here.",
    "do i need appointment": "No appointment is needed for lab visits. You can walk in anytime between 7 AM and 8 PM.",
    "what tests are available": "We offer a complete range of diagnostic services including blood tests, pathology, PFT, portable X-Ray, ECG, and full body profiles.",
    "where is the nearest branch": "We have 10 branches across Ahmedabad including Science City, Satellite, Bopal, Vastral, and others. Please tell me your area so I can guide you.",
    "do you accept walk-in patients": "Yes, walk-in patients are always welcome between 7 AM and 8 PM.",
    "what are your working days": "We are open all 7 days of the week, Monday to Sunday.",
    "do you work on sunday": "Yes, all Sun Pathology branches are fully open on Sundays from 7 AM to 8 PM.",
    "do you work on holidays": "Yes, we remain open on public holidays for your convenience.",
    "how long does a test take": "A routine sample collection takes only a few minutes. Specific testing times depend on the parameter.",
    "when will report be ready": "Most routine test reports are ready on the same day. Culture or specialized tests may take 48-72 hours.",
    "can i get urgent report": "If you have an emergency, please visit the lab directly. Urgent priority testing is available for critical cases.",
    "can reports be sent online": "Yes, reports are sent automatically online via WhatsApp, Email, or our website portal.",
    "can reports be sent by email": "Yes, securely encrypted PDF reports are sent to your registered email address.",
    "can i download reports": "Yes, you can easily download your reports using your registered mobile number on our website.",
    "can someone else collect my report": "Yes, anyone with the original receipt or authorized by the patient can collect a physical copy.",
    "can reports be printed again": "Yes, physical copies can be reprinted at the laboratory anytime.",
    "do you store old reports": "Yes, our digital archive stores your historical reports safely for future reference.",
    "can i access previous reports": "Yes, you can access your historical data anytime through the Sun Pathology online portal.",
    "do you provide health packages": "Yes, we offer discounted full body health packages starting at 2499 rupees.",
    "do you provide preventive checkups": "Yes, we have specialized preventive checkups evaluating all major organ functions.",
    "do you provide corporate health checkups": "Yes, we conduct comprehensive Corporate Employee Health Programs and Factory Act Compliance checkups.",
    "do you provide senior citizen packages": "Yes, we offer specialized senior citizen diagnostic profiles at discounted rates.",
    "do you provide executive packages": "Yes, we provide premium executive health checkup packages.",
    "is your lab certified": "Yes, Sun Pathology is NABL accredited and uses US FDA-approved diagnostic equipment.",
    "is your lab reliable": "Absolutely, Sun Pathology has 27 years of trusted experience performing over 30 million precise tests.",
    "are reports doctor verified": "Yes, every clinical report is reviewed and digitally signed by an expert Pathologist.",
    "who signs reports": "Dr. Mayank Joshi (Laboratory Director), Dr. Arpita Shah, or another of our expert senior pathologists will sign your report.",
    "are machines calibrated": "Yes, our machines operate under strict daily internal quality control calibrations to maintain Six Sigma performance.",
    "are technicians trained": "Yes, our staff consists only of highly trained and certified phlebotomists.",
    "is blood collection safe": "Yes, blood collection is 100% safe. We strictly follow sterile, standardized medical protocols.",
    "are needles disposable": "Yes, we exclusively use single-use, sterile, disposable needles that are destroyed immediately after one use.",
    "is equipment sterilized": "Yes, hygiene and sterilization are our highest priorities.",
    "are results accurate": "Yes, our advanced Vitros and Sysmex analyzers ensure highly definitive and accurate testing.",
    "can children do blood tests": "Yes, we use 'Less Pain Needle Technology' which is specifically designed to be gentle on children.",
    "can elderly patients give samples": "Yes, our phlebotomists are highly experienced with delicate, elderly veins.",
    "can pregnant women do tests": "Yes, we perform all specialized antenatal profiles and care testing safely.",
    "can bedridden patients give samples": "Yes, our expert phlebotomists can visit your home for bedridden sample extraction.",
    "do you test infants": "Yes, we have specialized infant care testing staff.",
    "do you provide ecg": "Yes, resting ECG testing is available, including field ECGs for corporate camps.",
    "do you provide hormone tests": "Yes, we have advanced immunoassay systems for all hormonal profile testing.",
    "do you provide vitamin tests": "Yes, tests for critical vitamins like Vitamin D and Vitamin B12 are available.",
    "do you provide infection tests": "Yes, advanced infectious disease screening and blood cultures are performed.",
    "do you provide allergy tests": "Yes, extensive allergen panels are available to detect specific immune sensitivities.",
    "do you provide cancer markers": "Yes, precision tumor marker and cancer diagnostic screening panels are available.",
    "do you provide diabetes tests": "Yes, comprehensive metabolic panels including Fasting Sugar, PPBS, and HbA1c are provided.",
    "do you provide thyroid tests": "Yes, Total Thyroid and Free Thyroid diagnostic profiles are available.",
    "do you provide liver tests": "Yes, complete Liver Function Tests (LFT) and enzyme screenings are handled.",
    "do you provide kidney tests": "Yes, comprehensive Kidney Function Tests (KFT) including creatinine and urea are available.",

    # PRICING
    "what is cbc price": "The MRP is 350 rupees, but at Sun Pathology you pay only 170 rupees.",
    "what is thyroid profile price": "The MRP is 660 rupees, but at Sun Pathology you pay only 280 rupees.",
    "what is lipid profile price": "The MRP is 850 rupees, but at Sun Pathology you pay only 360 rupees.",
    "what is vitamin d price": "The MRP is 1450 rupees, but at Sun Pathology you pay only 590 rupees.",
    "what is vitamin b12 price": "The MRP is 1200 rupees, but at Sun Pathology you pay only 490 rupees.",
    "what is hba1c price": "The MRP is 650 rupees, but at Sun Pathology you pay only 290 rupees.",
    "what is liver function test price": "The MRP is 1000 rupees, but at Sun Pathology you pay only 420 rupees.",
    "what is kidney function test price": "The MRP is 950 rupees, but at Sun Pathology you pay only 390 rupees.",
    "what is crp test price": "The MRP is 650 rupees, but at Sun Pathology you pay only 380 rupees.",
    "what is esr test price": "The MRP is 180 rupees, but at Sun Pathology you pay only 100 rupees.",
    "why are your prices cheaper": "Each laboratory has its own pricing structure. The MRP of tests is fixed, but our laboratory provides these tests at a discounted price to make diagnostics affordable for patients.",
    "do you give discounts": "Yes! We run discounted pricing across nearly all our tests compared to standard MRP.",
    "do you give package discounts": "Yes, we offer heavy discounts on bundled comprehensive Health Packages.",
    "are prices fixed": "Yes, the discounted prices quoted by Sun Pathology are fixed and highly competitive.",
    "do prices change": "Our internal discount prices remain stable to maximize patient affordability.",
    "do you accept cash": "Yes, cash payments are accepted directly at the diagnostic laboratory.",
    "do you accept upi": "Yes, UPI payments (Google Pay, PhonePe, Paytm, etc.) are fully accepted.",
    "do you accept cards": "Yes, we have POS machines at the lab to accept direct Credit or Debit card payments.",
    "do you provide bill": "Yes, a fully computerized invoice is generated for every registration.",
    "do you provide gst bill": "No GST is charged — Sun Pathology is a medical firm, so GST is not applicable.",
    "can payment be done online": "Yes, secure online payments can be made through a payment link sent via WhatsApp.",
    "can payment be done after report": "Payment is generally required at the time of registration and sample collection.",
    "do you offer membership discount": "Our standard price is already heavily discounted for all walk-in and home collection patients.",
    "do you have seasonal offers": "Yes, we occasionally run seasonal preventive health camp programs at extreme discounts.",
    "do you provide corporate pricing": "Yes, we offer customized quotation pricing for bulk corporate health checkup programs.",
    "are home visit charges extra": "Home collection is 100 rupees if the bill is < 350. It is 50 rupees if the bill is 350-649. It is FREE if the bill is 650 rupees or more.",
    "do packages include home visit": "All complete health packages typically exceed the free threshold, qualifying you for free home collection.",
    "do you provide free consultation": "We do not provide free physician consultation. Dr. Mayank Joshi can aid in report interpretation, but final diagnosis lies with your clinician.",
    "are packages refundable": "Refunds are processed only for cancellations made *before* the sample is successfully collected.",
    "do you match other lab prices": "We confidently offer one of the most technologically advanced and affordable testing ecosystems in Ahmedabad.",

    # PREPARATION
    "do i need fasting": "Only tests like Lipid Profile and Fasting Blood Sugar require fasting. CBC, Vitamins, Liver, and Kidney tests can be done anytime.",
    "how many hours fasting": "For fasting tests, strictly 10-12 hours of overnight fasting is required.",
    "can i drink water during fasting": "Yes, normal drinking water is perfectly allowed during a fasting period.",
    "can i drink tea": "No, tea (even without sugar) disrupts gastric enzymes and will interfere with standard fasting parameters.",
    "can i drink coffee": "No, coffee should be strictly avoided before fasting blood extraction.",
    "can i take medicines": "Standard daily medications (except diabetic insulin logic) are generally fine with plain water. Consult your doctor if unsure.",
    "should i stop medicines": "Do not stop critical cardiac or chronic medications without explicitly asking your treating physician.",
    "can i exercise before test": "Heavy exercise alters muscle enzymes (like CPK and AST) and hydration, so resting before testing is advised.",
    "can i smoke before test": "No, smoking causes acute spikes in white blood cells and alters lipids. Avoid smoking before testing.",
    "can i drink alcohol before test": "No, alcohol massively alters Liver enzymes (SGOT/SGPT) and cholesterol levels. Avoid it for 24-48 hours before testing.",
    "can i eat fruits": "No, fruits contain fructose sugars which will ruin a Fasting Blood Sugar test.",
    "can i eat breakfast": "If your test is 'Fasting', do not eat breakfast until the sample is successfully collected.",
    "can i brush teeth": "Yes, brushing your teeth with standard toothpaste does not alter fasting blood parameters.",
    "can i chew gum": "No, chewing gum often contains hidden sugars or stimulates gastric acid, interfering with fasting.",
    "can i take supplements": "Vitamin supplements (especially Biotin) can interfere with thyroid (TSH) assays. Take them *after* the blood test.",
    "can i take vitamins": "Do not take Vitamin D or B12 supplements immediately on the morning of testing to avoid artificial spike errors.",
    "can i take insulin": "If giving a fasting sugar sample, withhold your morning insulin until immediately *after* the sample is collected.",
    "can i take blood pressure medicine": "Yes, taking blood pressure medication with plain water is typically fine before a fasting test.",
    "can i take thyroid medicine": "It is generally advised to provide the sample *before* taking your morning dose of Thyroid medicine.",
    "can i take antibiotics": "Standard antibiotics do not natively interfere with routine biochemistry, but tell your technician.",
    "can dehydration affect tests": "Yes, severe dehydration can artificially elevate electrolyte and kidney parameters.",
    "can stress affect results": "Yes, acute stress spikes Cortisol, triggers white blood cell mobilization, and elevates heart rate temporarily.",
    "can sleep affect results": "Yes, extreme sleep deprivation disrupts the circadian rhythm of hormones like Cortisol and Thyroid.",
    "can exercise affect results": "Yes, aggressive physical activity can spike muscle enzyme leakage (CPK) into the blood.",
    "can diet affect results": "Yes, heavy, fatty meals the night before a test will visibly turn blood serum cloudy (lipemic) and ruin triglyceride accuracy.",
    "can infection affect reports": "Yes, ongoing viral or bacterial infections natively alter total CBC profiles and trigger CRP inflammation markers.",
    "can fever affect tests": "A fever is an immune response that dramatically shifts blood cell ratios and ESR results.",
    "can menstrual cycle affect tests": "Yes, reproductive hormonal baselines completely change depending on the phase of the menstrual cycle.",
    "can pregnancy affect reports": "Yes, normal physiological shifts in pregnancy alter reference ranges for thyroid, sugars, and hemoglobin.",
    "can travel affect reports": "Extreme jet lag or changing time zones can affect circadian-indexed hormone sampling times.",
    "can fasting more than 12 hours affect results": "Yes, 'over-fasting' (14+ hours) pushes the body into starvation. Cortisol goes up and sugars can misleadingly drop.",
    "can late night meals affect results": "Yes, heavy late-night dinners prevent accurate 10-hour fasting baseline clearing.",
    "can energy drinks affect tests": "Yes, heavy caffeine and sugars alter hepatic and glycemic metabolic resting states.",
    "can high protein diet affect results": "Extreme high-protein diets can slightly elevate Urea or BUN measurements.",
    "can low carb diet affect results": "Keto diets significantly alter lipid metabolisms and baseline ketone measurements.",
    "can fasting sugar change daily": "Yes, daily sugar is influenced by exact dinner carb intake, stress, and sleep the previous night.",
    "can cholesterol change daily": "While total cholesterol is stable, Triglycerides are hyper-reactive to recent daily dietary fats.",
    "can thyroid fluctuate": "Mild TSH fluctuations are normal and vary slightly by time of day relative to the circadian clock.",
    "can vitamin levels change": "Water-soluble vitamins (like B-complex) fluctuate depending on recent diet. Fat-soluble vitamins take weeks to shift.",
    "can hormone levels vary": "Yes, hormones are secreted in pulsatile bursts and dynamically fluctuate throughout the entire day.",
    "why do reference ranges differ": "Different reference ranges exist because different labs use totally different reagent chemicals and diagnostic methodologies.",
    "why do labs use different machines": "Different diagnostic companies (Roche, Siemens, Vitros) patent their own unique biochemical assessment mechanisms.",
    "why do reports vary slightly": "Test results naturally change from day to day because the human body is dynamic. Also, labs use different analytical thresholds.",
    "why do results change daily": "Factors like stress, sleep behaviour, diet, hydration, physical activity, and minor infections influence daily biological baselines.",
    "why are normal ranges different for age": "Biological norms shift: a healthy liver enzyme limit for a child differs completely from a 70-year-old.",
    "why do male and female ranges differ": "Hormones and average muscle mass distributions (like Creatinine) drastically separate male and female normal distributions.",
    "why do children have different ranges": "Children are actively growing. Their bone alkaline phosphatase enzymes are naturally double that of an adult.",
    "why do elderly patients have different ranges": "Organ efficiency naturally changes, affecting baseline normal clearances of the kidneys and liver.",
    "why do labs repeat tests": "If a value is critically high/low (panic value), a strict protocol forces our machines to dilute and cross-check it before releasing the report.",
    "why do some tests take longer": "Culture tests require giving bacteria 48-72 hours to physically grow in an incubator before we can assess them.",
    "why do some tests need fasting": "Fasting provides a clean, neutral baseline completely uncorrupted by recent food digestion spikes (like blood sugar spikes).",
    "why do some tests require morning sample": "Hormones like Cortisol and Testosterone peak sharply in the early morning according to the natural circadian rhythm.",
    "why do some tests require urine sample": "Urine filters metabolic waste. Spotting protein or glucose in urine signals a failure of the kidney's filtering gate.",
    "why do stool tests take time": "Stool culture processing requires isolation in specialized mediums that slowly grow bacterial traces.",
    "why do hormone tests depend on timing": "Hormones are 'pulsatile'. Taking a female hormone panel on Day 3 of a cycle means something completely different than Day 21.",

    # REPORTS
    "my report value is high": "If a value is high, please do not panic. Small elevations are common. For a proper diagnosis, consult your physician.",
    "my report value is low": "If a value is below the reference range, show the report to your clinician for proper medical context.",
    "what does abnormal mean": "It simply highlights that the mathematical value falls outside the statistical average of a healthy population. A doctor must evaluate the context.",
    "what does borderline mean": "A borderline result sits on the absolute edge of the normal limit, suggesting preventative caution or a repeat test later.",
    "what does critical mean": "Critical or 'Panic' values require immediate clinical attention and you should consult a hospital or your doctor instantly.",
    "can reports be wrong": "No laboratory is statistically 100% infallible, but Sun Pathology uses Six Sigma automated processes to eliminate human error.",
    "can machines make mistakes": "Advanced automated machines internally cross-check flags using internal quality-control serums to prevent mechanical mistakes.",
    "can sample mix up happen": "No. Sun Pathology operates on strict Barcoding automation where a label is dynamically locked to a sample instantly at collection.",
    "can i repeat the test": "Yes, you can absolutely book a repeat sample for peace of mind, though biological changes mean identical matching is unlikely.",
    "can i get second opinion": "Yes, we always encourage you to discuss findings with multiple clinical practitioners for comprehensive diagnostics.",
    "why is my result different from last year": "Over the span of a year, massive shifts in diet, age, metabolic health, or minor chronic conditions inevitably alter test baselines.",
    "why is my result different from yesterday": "Hydration levels, sleep deprivation, stress, and diet from the past 24 hours heavily swing acute markers like sugar and liver enzymes.",
    "why is my result different from another lab": "Laboratory test values can vary slightly between laboratories because different labs may use different machines, reagents, and reference ranges.",
    "why is my value fluctuating": "The human body is an active, dynamic machine constantly compensating for food, environment, and physical demands.",
    "why did my value increase suddenly": "An acute spike usually points to an active infection, a sharp physical stressor, or a change in recent dietary intake.",
    "why did my value decrease suddenly": "A sharp decrease may relate to dilution, sudden lifestyle changes, or simply the time of day the sample was drawn.",
    "can stress change reports": "Yes, anxiety and severe stress violently flood the body with cortisol and catecholamines, altering lab parameters.",
    "can sleep behaviour change reports": "Yes, poor sleep severely degrades glucose tolerance and alters immune cell generation for the day.",
    "can diet change reports": "Yes, regular consumption of excess fat or sugar over time permanently shifts resting lipid and HbA1c panels.",
    "can medicines change reports": "Yes, antibiotics heavily suppress liver enzymes and cultures. BP medications can alter potassium and sodium markers.",
    "can infections change reports": "Yes. A minor viral cold you got last Tuesday will still leave a spike in your white blood cells today.",
    "can dehydration change reports": "Yes. Severe lack of water physically shrinks plasma volume, making all cells and proteins look artificially 'concentrated' and high.",
    "can exercise change reports": "Yes, intense weightlifting or running causes micro-tears in muscles, dumping CPK enzymes into the blood test.",
    "can pregnancy change reports": "Yes, a developing fetus drastically alters hormonal demand, iron storage, and baseline sugar tolerances.",
    "can hormonal cycle change reports": "Yes, female estrogen and progesterone aggressively shift reference ranges based on the day of the cycle.",
    "who should explain my report": "Only a qualified clinical doctor who understands your specific pre-existing medical history should execute the interpretation.",
    "can lab explain results": "A lab can explain what a specific marker does (e.g., 'HbA1c measures 3-month sugar'), but cannot give clinical advice.",
    "should i consult doctor": "Yes, always take your printed or digital report directly to your primary care physician.",
    "can pathologist explain report": "Dr. Mayank Joshi can aid in explaining discrepancies or the scientific integrity of the result via his WhatsApp number.",
    "can i call lab director": "Yes! For serious test-related doubts, message both reports to Laboratory Director Dr. Mayank Joshi at 9276843433.",
    "can i send report on whatsapp": "Yes, simply message the PDF to Dr. Mayank Joshi at 9276843433 for specific laboratory queries.",
    "can doctor receive report directly": "If authorized or linked directly to an ongoing clinical inquiry, reports can be routed.",
    "can reports be corrected": "If there is a typographical error in your name or age, contact the lab and an official addendum will be issued immediately.",
    "can report name be changed": "Yes, patient demographic typos can be amended by producing a valid government ID to the Sun Pathology front desk.",
    "can age be corrected": "Yes, if the age input was incorrect, the lab software can amend it upon verification.",
    "can report be reprinted": "Yes, official physical copies with fresh stamps can be reprinted at no extra cost at the lab.",
    "can old report be retrieved": "Yes, providing your registered mobile number allows our staff to pull reports securely from past archives.",
    "what if report is delayed": "I apologize for any delay. Some specialized tests demand extra incubation or cross-checking time. Please provide your mobile number so I can check.",
    
    # HOME COLLECTION 
    "how to book home visit": "We provide home sample collection. Share your mobile number, name, address, and test requirement to schedule a slot.",
    "what time does home visit start": "Our specialized home collection technicians begin morning routes starting precisely at 6 AM.",
    "can i choose time slot": "Yes! You can pick explicit hourly slots starting from 6-7 AM all the way up to 7-8 PM.",
    "are home visits safe": "Absolutely safely executed by trained professionals utilizing sterile vacutainers and disposable gloves.",
    "are staff trained": "Every Sun Pathology mobile technician undergoes rigorous phlebotomy certification and continuous hygiene training.",
    "do staff use disposable needles": "Yes! 100% of the needles utilized are premium, sterile, and strictly single-use only.",
    "can elderly patients give sample at home": "Yes! Our technicians specialize in drawing blood safely from sensitive or weak veins.",
    "can bedridden patients give sample": "Absolutely. Home collection is specifically designed to safely accommodate immobilized or bedridden patients.",
    "can children give sample at home": "Yes! We employ Less Pain Needle Technology effectively lowering pediatric distress in a familiar home setting.",
    "can urine sample be collected at home": "Yes! Our technicians bring sterile, sealed culture containers for fast collection and secure transport.",
    "can fasting sample be taken at home": "Yes! Our busiest time slots are 6-8 AM purely dedicated to collecting overnight fasting samples.",
    "can society camps be organized": "Yes! Sun Pathology eagerly organizes massive residential society camps featuring blood tests and ECG setups.",
    "can corporate camps be organized": "Yes! We organize full Factory Act Compliance health camps directly at your corporate premises.",
    
    # TRUST AND QUALITY
    "is sun pathology reliable": "With over 27 years of experience, 30 million completed tests, and strict NABL adherence, Sun Pathology remains deeply reliable.",
    "who is lab director": "Dr. Mayank Joshi is the distinguished Laboratory Director overseeing our strict quality guidelines.",
    "are machines automated": "Yes, we proudly operate a futuristic Total Lab Automation line driven by AI, mitigating human error.",
    "are reagents standardized": "Yes. We operate exclusively strictly with FDA and CE-approved reagents from premier global clinical suppliers.",
    "are reports reviewed before release": "Every flagged or critical report stops directly at the desk of our senior pathologists for manual cross-verification.",
    "are samples stored properly": "Post-analysis, serums are safely archived in secure refrigerated logs strictly following standard protocol mandates.",
    "why choose sun pathology": "We guarantee state-of-the-art diagnostic science fused directly with uncompromising compassion and affordability."
}

def translate_and_save():
    translator_hi = GoogleTranslator(source='en', target='hi')
    translator_gu = GoogleTranslator(source='en', target='gu')
    
    final_db = {
        "en": {},
        "hi": {},
        "gu": {}
    }
    
    print(f"Translating {len(en_faqs)} questions...")
    total = len(en_faqs)
    
    for i, (q_en, a_en) in enumerate(en_faqs.items()):
        # Store english originally
        final_db["en"][q_en.lower()] = a_en
        
        # Translate to Hindi
        try:
            q_hi = translator_hi.translate(q_en)
            a_hi = translator_hi.translate(a_en)
            if q_hi and a_hi:
                final_db["hi"][q_hi.lower()] = a_hi
        except Exception as e:
            print(f"Hindi error on {q_en}: {e}")
            
        # Translate to Gujarati
        try:
            q_gu = translator_gu.translate(q_en)
            a_gu = translator_gu.translate(a_en)
            if q_gu and a_gu:
                final_db["gu"][q_gu.lower()] = a_gu
        except Exception as e:
            print(f"Gujarati error on {q_en}: {e}")
            
        time.sleep(0.5) # Sleep to avoid rate limits
        if (i+1) % 10 == 0:
            print(f"Completed {i+1} / {total}")
            
    with open('app/knowledge/faq_database.json', 'w', encoding='utf-8') as f:
        json.dump(final_db, f, ensure_ascii=False, indent=4)
        
    print("Successfully built faq_database.json with all entries!")

if __name__ == "__main__":
    translate_and_save()
