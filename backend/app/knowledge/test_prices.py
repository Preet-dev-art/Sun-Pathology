"""
test_prices.py
Sun Pathology Laboratory & Research Institute
Production-Grade Test Price Lookup

Improvements over v1:
  1. Fuzzy matching via rapidfuzz (handles typos: "lipied profile" → Lipid Profile)
  2. Hindi & Gujarati test name aliases for multilingual voice/chat queries
  3. Single find_test_price() that handles English, Hindi, Gujarati, and typos
  4. Home collection charge calculator
  5. All prices are integers (no string formatting here — formatting is the prompt's job)

Install dependency: pip install rapidfuzz
"""

from typing import Optional

# ─────────────────────────────────────────────────────────────────────────────
# PRICE DATABASE
# ─────────────────────────────────────────────────────────────────────────────
test_prices = [
    {"id": 1, "name": "17-OH Progesterone", "matchNames": ["17-OH Progesterone", "17 OH Progesterone"], "mrp": 1100, "price": 600},
    {"id": 2, "name": "24 Hrs Urinary Albumin Creatinine Ratio", "matchNames": ["24 Hrs Urinary Albumin Creatinine Ratio", "Albumin Creatinine Ratio"], "mrp": 700, "price": 350},
    {"id": 3, "name": "24 Hrs Urinary Protein", "matchNames": ["24 Hrs Urinary Protein", "Urinary Protein"], "mrp": 500, "price": 250},
    {"id": 4, "name": "24 Hrs Urine Microalbumine", "matchNames": ["24 Hrs Urine Microalbumine", "Microalbumine"], "mrp": 600, "price": 300},
    {"id": 5, "name": "24 Hrs Creatinine Clearance Test", "matchNames": ["24 Hrs Creatinine Clearance Test", "Creatinine Clearance"], "mrp": 500, "price": 250},
    {"id": 6, "name": "24 Hrs Specific Gravity", "matchNames": ["24 Hrs Specific Gravity", "Specific Gravity"], "mrp": 400, "price": 200},
    {"id": 7, "name": "24 Hrs Urinary Sodium", "matchNames": ["24 Hrs Urinary Sodium", "Urinary Sodium"], "mrp": 500, "price": 250},
    {"id": 8, "name": "24 Hrs Urine Calcium", "matchNames": ["24 Hrs Urine Calcium", "Urinary Calcium"], "mrp": 300, "price": 150},
    {"id": 9, "name": "24 Hrs Urinary VMA", "matchNames": ["24 Hrs Urinary VMA", "Urinary VMA"], "mrp": 2500, "price": 1250},
    {"id": 10, "name": "A.S.O.Titer", "matchNames": ["A.S.O.Titer", "ASO Titer"], "mrp": 600, "price": 300},
    {"id": 11, "name": "ACA IgG IgM", "matchNames": ["ACA IgG IgM", "ACA"], "mrp": 1200, "price": 600},
    {"id": 12, "name": "ACE Level", "matchNames": ["ACE Level"], "mrp": 1500, "price": 1000},
    {"id": 13, "name": "Acetyl Choline Receptor Antibody", "matchNames": ["Acetyl Choline Receptor Antibody"], "mrp": 3100, "price": 2100},
    {"id": 14, "name": "ACTH", "matchNames": ["ACTH"], "mrp": 1100, "price": 800},
    {"id": 15, "name": "ADA Level (Adenosine Deaminase)", "matchNames": ["ADA Level", "Adenosine Deaminase"], "mrp": 600, "price": 400},
    {"id": 16, "name": "AFB Culture", "matchNames": ["AFB Culture"], "mrp": 1200, "price": 800},
    {"id": 17, "name": "Albumin", "matchNames": ["Albumin"], "mrp": 300, "price": 150},
    {"id": 18, "name": "Aldosterone", "matchNames": ["Aldosterone"], "mrp": 1500, "price": 1000},
    {"id": 19, "name": "Alkaline Phosphatase", "matchNames": ["Alkaline Phosphatase"], "mrp": 300, "price": 150},
    {"id": 20, "name": "Allergy Profile", "matchNames": ["Allergy Profile"], "mrp": 7000, "price": 3000},
    {"id": 21, "name": "Alpha Feto Protein", "matchNames": ["Alpha Feto Protein", "AFP"], "mrp": 700, "price": 350},
    {"id": 22, "name": "Ammonia", "matchNames": ["Ammonia"], "mrp": 600, "price": 300},
    {"id": 23, "name": "Amylase", "matchNames": ["Amylase"], "mrp": 600, "price": 300},
    {"id": 24, "name": "ANA By IF", "matchNames": ["ANA By IF"], "mrp": 800, "price": 400},
    {"id": 25, "name": "ANA Profile (Blot)", "matchNames": ["ANA Profile", "ANA Blot"], "mrp": 3800, "price": 2000},
    {"id": 26, "name": "ANCA By IF", "matchNames": ["ANCA By IF"], "mrp": 2700, "price": 1800},
    {"id": 27, "name": "ANCA MPO PR3", "matchNames": ["ANCA MPO PR3"], "mrp": 3600, "price": 1600},
    {"id": 28, "name": "Anti Cardiolipin Ab(IgG)", "matchNames": ["Anti Cardiolipin Ab(IgG)", "Cardiolipin IgG"], "mrp": 600, "price": 300},
    {"id": 29, "name": "Anti Cardiolipin Ab(IgM)", "matchNames": ["Anti Cardiolipin Ab(IgM)", "Cardiolipin IgM"], "mrp": 600, "price": 300},
    {"id": 30, "name": "Anti CCP Ab", "matchNames": ["Anti CCP Ab", "Anti CCP"], "mrp": 800, "price": 550},
    {"id": 31, "name": "Anti Ds D.N.A.By IF", "matchNames": ["Anti Ds D.N.A.By IF", "Ds DNA"], "mrp": 800, "price": 400},
    {"id": 32, "name": "Anti Gad", "matchNames": ["Anti Gad"], "mrp": 2000, "price": 1900},
    {"id": 33, "name": "Anti GBM Antibody", "matchNames": ["Anti GBM Antibody"], "mrp": 2000, "price": 1000},
    {"id": 34, "name": "Anti Hbc IgM", "matchNames": ["Anti Hbc IgM"], "mrp": 800, "price": 400},
    {"id": 35, "name": "Anti Hbc Total", "matchNames": ["Anti Hbc Total"], "mrp": 800, "price": 500},
    {"id": 36, "name": "Anti Hbe", "matchNames": ["Anti Hbe"], "mrp": 800, "price": 400},
    {"id": 37, "name": "Anti Hbs", "matchNames": ["Anti Hbs"], "mrp": 800, "price": 400},
    {"id": 38, "name": "Anti HEV IgM", "matchNames": ["Anti HEV IgM"], "mrp": 800, "price": 500},
    {"id": 39, "name": "Anti Mitochondrial Antibody", "matchNames": ["Anti Mitochondrial Antibody", "AMA"], "mrp": 1500, "price": 800},
    {"id": 40, "name": "Anti Mullarian Hormone", "matchNames": ["Anti Mullarian Hormone", "AMH"], "mrp": 1200, "price": 900},
    {"id": 41, "name": "Anti Parietal Cell Ab", "matchNames": ["Anti Parietal Cell Ab"], "mrp": 1500, "price": 800},
    {"id": 42, "name": "Anti Phospholipase A2 Antibody Receptor", "matchNames": ["Anti Phospholipase A2 Antibody Receptor"], "mrp": 4600, "price": 4500},
    {"id": 43, "name": "Anti Phospholipid Ab (IgG)", "matchNames": ["Anti Phospholipid Ab (IgG)"], "mrp": 600, "price": 300},
    {"id": 44, "name": "Anti Phospholipid Ab (IgM)", "matchNames": ["Anti Phospholipid Ab (IgM)"], "mrp": 600, "price": 300},
    {"id": 45, "name": "Anti Saccharomyces Cerevisiae Antibody IgG IgA", "matchNames": ["Anti Saccharomyces Cerevisiae Antibody"], "mrp": 4200, "price": 2600},
    {"id": 46, "name": "Anti Smooth Muscle Antibody (By IF)", "matchNames": ["Anti Smooth Muscle Antibody", "ASMA"], "mrp": 1500, "price": 800},
    {"id": 47, "name": "Anti Sperm Antibody", "matchNames": ["Anti Sperm Antibody"], "mrp": 900, "price": 900},
    {"id": 48, "name": "Anti TG", "matchNames": ["Anti TG"], "mrp": 600, "price": 500},
    {"id": 49, "name": "Anti TPO", "matchNames": ["Anti TPO"], "mrp": 600, "price": 350},
    {"id": 50, "name": "Antiphospholipid Antibody IgG IgM", "matchNames": ["Antiphospholipid Antibody"], "mrp": 1200, "price": 600},
    {"id": 51, "name": "Apolipoprotein A1", "matchNames": ["Apolipoprotein A1"], "mrp": 600, "price": 300},
    {"id": 52, "name": "Apolipoprotein B", "matchNames": ["Apolipoprotein B"], "mrp": 600, "price": 300},
    {"id": 53, "name": "APTT", "matchNames": ["APTT"], "mrp": 500, "price": 250},
    {"id": 54, "name": "Aspergillus Specific IgE", "matchNames": ["Aspergillus Specific IgE"], "mrp": 550, "price": 450},
    {"id": 55, "name": "B2 Microglobulin", "matchNames": ["B2 Microglobulin"], "mrp": 1400, "price": 700},
    {"id": 56, "name": "BCR ABL Quantitative By PCR", "matchNames": ["BCR ABL Quantitative By PCR", "BCR ABL"], "mrp": 5500, "price": 5500},
    {"id": 57, "name": "Beta 2 Glycoprotein IgG IgM", "matchNames": ["Beta 2 Glycoprotein"], "mrp": 1400, "price": 700},
    {"id": 58, "name": "Beta HCG Estimation", "matchNames": ["Beta HCG Estimation", "Beta HCG"], "mrp": 600, "price": 300},
    {"id": 59, "name": "Billirubin", "matchNames": ["Billirubin", "Bilirubin"], "mrp": 300, "price": 150},
    {"id": 60, "name": "Blood Culture (Aerobic)", "matchNames": ["Blood Culture (Aerobic)"], "mrp": 1200, "price": 1200},
    {"id": 61, "name": "Blood Culture (Anaerobic)", "matchNames": ["Blood Culture (Anaerobic)"], "mrp": 1200, "price": 1200},
    {"id": 62, "name": "Blood Group & Rh Type", "matchNames": ["Blood Group & Rh Type", "Blood Group", "ब्लड ग्रुप", "લોહી ગ્રૂપ"], "mrp": 200, "price": 100},
    {"id": 63, "name": "Blood Urea Nitrogen", "matchNames": ["Blood Urea Nitrogen", "BUN"], "mrp": 300, "price": 150},
    {"id": 64, "name": "Brucella IgG IgM", "matchNames": ["Brucella IgG IgM"], "mrp": 1200, "price": 600},
    {"id": 65, "name": "Brucellosis(Aglutination)", "matchNames": ["Brucellosis"], "mrp": 900, "price": 600},
    {"id": 66, "name": "BT CT", "matchNames": ["BT CT"], "mrp": 100, "price": 50},
    {"id": 67, "name": "C3 Level", "matchNames": ["C3 Level"], "mrp": 600, "price": 400},
    {"id": 68, "name": "C4 Level", "matchNames": ["C4 Level"], "mrp": 600, "price": 400},
    {"id": 69, "name": "CA 15.3", "matchNames": ["CA 15.3"], "mrp": 1200, "price": 600},
    {"id": 70, "name": "CA 19.9", "matchNames": ["CA 19.9"], "mrp": 1200, "price": 500},
    {"id": 71, "name": "CA 125", "matchNames": ["CA 125"], "mrp": 800, "price": 400},
    {"id": 72, "name": "Calcitonine", "matchNames": ["Calcitonine"], "mrp": 1300, "price": 650},
    {"id": 73, "name": "Calcium", "matchNames": ["Calcium", "कैल्शियम", "કેલ્શિયમ"], "mrp": 300, "price": 150},
    {"id": 74, "name": "CBC With Mp By Antigen", "matchNames": ["CBC With Mp By Antigen", "CBC", "सीबीसी", "સીબીસી", "Complete Blood Count", "complete blood count"], "mrp": 350, "price": 170},
    {"id": 75, "name": "CD4 & CD8 Count", "matchNames": ["CD4 & CD8 Count"], "mrp": 2000, "price": 1000},
    {"id": 76, "name": "CEA", "matchNames": ["CEA"], "mrp": 800, "price": 400},
    {"id": 77, "name": "Ceruloplasmin", "matchNames": ["Ceruloplasmin"], "mrp": 800, "price": 400},
    {"id": 78, "name": "Chikun Gunya PCR", "matchNames": ["Chikun Gunya PCR", "Chikungunya", "चिकनगुनिया"], "mrp": 2200, "price": 900},
    {"id": 79, "name": "Chloride", "matchNames": ["Chloride"], "mrp": 300, "price": 150},
    {"id": 80, "name": "Cholesterol", "matchNames": ["Cholesterol", "कोलेस्ट्रॉल", "કોલેસ્ટ્રોલ"], "mrp": 300, "price": 150},
    {"id": 81, "name": "Chromogranin A", "matchNames": ["Chromogranin A"], "mrp": 4500, "price": 3000},
    {"id": 82, "name": "CMV Viral Load Quantitative(PCR)", "matchNames": ["CMV Viral Load"], "mrp": 4000, "price": 3000},
    {"id": 83, "name": "Coomb's Test (Direct & Indirect)", "matchNames": ["Coomb's Test (Direct & Indirect)", "Coombs Test"], "mrp": 1200, "price": 600},
    {"id": 84, "name": "Coomb's Test (Direct)", "matchNames": ["Coomb's Test (Direct)"], "mrp": 600, "price": 300},
    {"id": 85, "name": "Coomb's Test (Indirect)", "matchNames": ["Coomb's Test (Indirect)"], "mrp": 600, "price": 300},
    {"id": 86, "name": "Copper Level", "matchNames": ["Copper Level"], "mrp": 1000, "price": 500},
    {"id": 87, "name": "Cortisol AM", "matchNames": ["Cortisol AM"], "mrp": 700, "price": 350},
    {"id": 88, "name": "Cortisol AM PM", "matchNames": ["Cortisol AM PM"], "mrp": 1400, "price": 700},
    {"id": 89, "name": "Cortisol PM", "matchNames": ["Cortisol PM"], "mrp": 700, "price": 350},
    {"id": 90, "name": "Cortisol Random", "matchNames": ["Cortisol Random"], "mrp": 700, "price": 350},
    {"id": 91, "name": "Covid-19 By Rt-PCR", "matchNames": ["Covid-19 By Rt-PCR", "Covid PCR", "RTPCR", "कोविड", "COVID"], "mrp": 400, "price": 400},
    {"id": 92, "name": "C-Peptide (FBS)", "matchNames": ["C-Peptide (FBS)"], "mrp": 1300, "price": 650},
    {"id": 93, "name": "C-Peptide (PPBS)", "matchNames": ["C-Peptide (PPBS)"], "mrp": 1300, "price": 650},
    {"id": 94, "name": "C-Peptide (RBS)", "matchNames": ["C-Peptide (RBS)"], "mrp": 1300, "price": 650},
    {"id": 95, "name": "CPK MB", "matchNames": ["CPK MB"], "mrp": 700, "price": 350},
    {"id": 96, "name": "CPK Total", "matchNames": ["CPK Total"], "mrp": 700, "price": 350},
    {"id": 97, "name": "Creatinine", "matchNames": ["Creatinine"], "mrp": 300, "price": 150},
    {"id": 98, "name": "CRP", "matchNames": ["CRP", "C Reactive Protein"], "mrp": 450, "price": 220},
    {"id": 99, "name": "Cytomagalovirus(IgG & IgM)", "matchNames": ["Cytomagalovirus(IgG & IgM)", "CMV IgG IgM"], "mrp": 800, "price": 400},
    {"id": 100, "name": "Cytomagalovirus(IgG)", "matchNames": ["Cytomagalovirus(IgG)", "CMV IgG"], "mrp": 400, "price": 200},
    {"id": 101, "name": "Cytomegalovirus (IgM)", "matchNames": ["Cytomegalovirus (IgM)", "CMV IgM"], "mrp": 400, "price": 200},
    {"id": 102, "name": "D-Dimer", "matchNames": ["D-Dimer"], "mrp": 900, "price": 400},
    {"id": 103, "name": "Dengue Test", "matchNames": ["Dengue Test", "Dengue", "dengue", "डेंगू", "NS1 Antigen", "Dengue NS1"], "mrp": 700, "price": 350},
    {"id": 104, "name": "Dengue Chikungunia PCR Combo", "matchNames": ["Dengue Chikungunia PCR Combo"], "mrp": 4000, "price": 1800},
    {"id": 105, "name": "Dengue IgG (CLIA)", "matchNames": ["Dengue IgG (CLIA)"], "mrp": 800, "price": 300},
    {"id": 106, "name": "Dengue IgG (ELISA)", "matchNames": ["Dengue IgG (ELISA)"], "mrp": 800, "price": 650},
    {"id": 107, "name": "Dengue IgM (CLIA)", "matchNames": ["Dengue IgM (CLIA)"], "mrp": 800, "price": 300},
    {"id": 108, "name": "Dengue IgM (ELISA)", "matchNames": ["Dengue IgM (ELISA)"], "mrp": 800, "price": 650},
    {"id": 109, "name": "Dengue Ns1 (CLIA)", "matchNames": ["Dengue Ns1 (CLIA)"], "mrp": 800, "price": 300},
    {"id": 110, "name": "Dengue Ns1 (ELISA)", "matchNames": ["Dengue Ns1 (ELISA)"], "mrp": 800, "price": 650},
    {"id": 111, "name": "Dengue PCR", "matchNames": ["Dengue PCR"], "mrp": 2200, "price": 900},
    {"id": 112, "name": "Dengue(Ns1)-Rapid", "matchNames": ["Dengue(Ns1)-Rapid", "Dengue Rapid"], "mrp": 700, "price": 280},
    {"id": 113, "name": "DHEAS", "matchNames": ["DHEAS"], "mrp": 750, "price": 400},
    {"id": 114, "name": "Digoxin Level", "matchNames": ["Digoxin Level"], "mrp": 800, "price": 400},
    {"id": 115, "name": "Double Marker", "matchNames": ["Double Marker"], "mrp": 2100, "price": 1700},
    {"id": 116, "name": "E2 (Estrogen/ Estradiol)", "matchNames": ["E2", "Estrogen", "Estradiol"], "mrp": 550, "price": 300},
    {"id": 117, "name": "E3 (Estriol)", "matchNames": ["E3", "Estriol"], "mrp": 1000, "price": 600},
    {"id": 118, "name": "EBV Qualitative PCR", "matchNames": ["EBV Qualitative PCR"], "mrp": 3000, "price": 2100},
    {"id": 119, "name": "EBV Quantitative PCR", "matchNames": ["EBV Quantitative PCR"], "mrp": 5000, "price": 3400},
    {"id": 120, "name": "Electrolytes", "matchNames": ["Electrolytes"], "mrp": 750, "price": 360},
    {"id": 121, "name": "ESR", "matchNames": ["ESR"], "mrp": 100, "price": 50},
    {"id": 122, "name": "Fasting Blood Sugar", "matchNames": ["Fasting Blood Sugar", "FBS", "Fasting Sugar", "फास्टिंग शुगर", "fasting sugar", "Sugar Test", "sugar test", "ब्लड शुगर", "ફાસ્ટિંગ શુગર", "glucose", "Fasting Plasma Glucose"], "mrp": 160, "price": 80},
    {"id": 123, "name": "Ferritin Level", "matchNames": ["Ferritin Level", "Ferritin"], "mrp": 750, "price": 350},
    {"id": 124, "name": "Fibrin Degradation Product(FDP)", "matchNames": ["Fibrin Degradation Product", "FDP"], "mrp": 900, "price": 500},
    {"id": 125, "name": "Fibrinogen Level", "matchNames": ["Fibrinogen Level", "Fibrinogen"], "mrp": 750, "price": 500},
    {"id": 126, "name": "Fluid Culture", "matchNames": ["Fluid Culture"], "mrp": 650, "price": 400},
    {"id": 127, "name": "Fluid R & M", "matchNames": ["Fluid R & M"], "mrp": 600, "price": 300},
    {"id": 128, "name": "Folic Acid", "matchNames": ["Folic Acid"], "mrp": 800, "price": 500},
    {"id": 129, "name": "Food Intolerance Testing", "matchNames": ["Food Intolerance Testing", "Food Intolerance"], "mrp": 10000, "price": 6500},
    {"id": 130, "name": "Free Light Chain", "matchNames": ["Free Light Chain"], "mrp": 4000, "price": 3600},
    {"id": 131, "name": "Free Prostate Specific Antigen", "matchNames": ["Free Prostate Specific Antigen", "Free PSA"], "mrp": 1000, "price": 550},
    {"id": 132, "name": "Free Testosterone", "matchNames": ["Free Testosterone"], "mrp": 900, "price": 500},
    {"id": 133, "name": "FSH", "matchNames": ["FSH"], "mrp": 550, "price": 250},
    {"id": 134, "name": "FT3", "matchNames": ["FT3"], "mrp": 300, "price": 150},
    {"id": 135, "name": "FT4", "matchNames": ["FT4"], "mrp": 300, "price": 150},
    {"id": 136, "name": "Fungus Culture & Sensitivity", "matchNames": ["Fungus Culture & Sensitivity"], "mrp": 1000, "price": 850},
    {"id": 137, "name": "Fungus Sensitivity For Urine", "matchNames": ["Fungus Sensitivity For Urine"], "mrp": 500, "price": 400},
    {"id": 138, "name": "G.G.T.", "matchNames": ["G.G.T.", "GGT"], "mrp": 550, "price": 330},
    {"id": 139, "name": "G6PD Quantitative Test", "matchNames": ["G6PD Quantitative Test", "G6PD"], "mrp": 550, "price": 400},
    {"id": 140, "name": "Galactomannan Aspergillus Ag", "matchNames": ["Galactomannan Aspergillus Ag"], "mrp": 1200, "price": 900},
    {"id": 141, "name": "GCT (1 Hour - 50 Gm Glucose)", "matchNames": ["GCT 50g"], "mrp": 100, "price": 50},
    {"id": 142, "name": "GCT (1 Hour - 75 Gm Glucose)", "matchNames": ["GCT 75g"], "mrp": 100, "price": 50},
    {"id": 143, "name": "Glucose Tolerance Test(3 Sample)", "matchNames": ["Glucose Tolerance Test 3 Sample", "GTT 3 Sample"], "mrp": 400, "price": 200},
    {"id": 144, "name": "Glucose Tolerance Test(5 Sample)", "matchNames": ["Glucose Tolerance Test 5 Sample", "GTT 5 Sample"], "mrp": 600, "price": 300},
    {"id": 145, "name": "HbA1c", "matchNames": ["HbA1c", "Glycosylated Hb", "Glycated Hemoglobin", "HBA1C", "hba1c", "एचबीए1सी", "ગ્લાઇકેટેડ"], "mrp": 700, "price": 350},
    {"id": 146, "name": "Growth Hormone", "matchNames": ["Growth Hormone"], "mrp": 800, "price": 400},
    {"id": 147, "name": "GTT(Modified)", "matchNames": ["GTT Modified"], "mrp": 100, "price": 50},
    {"id": 148, "name": "H.Pylori IgG", "matchNames": ["H.Pylori IgG"], "mrp": 800, "price": 400},
    {"id": 149, "name": "H1N1", "matchNames": ["H1N1"], "mrp": 4500, "price": 4200},
    {"id": 150, "name": "Hemoglobin", "matchNames": ["Hemoglobin", "Haemoglobin", "Hb", "हीमोग्लोबिन", "hemoglobin", "Hgb", "HB test", "hb test", "હિમોગ્લોબિન"], "mrp": 160, "price": 80},
    {"id": 151, "name": "Haemoglobin Electrophoresis", "matchNames": ["Haemoglobin Electrophoresis"], "mrp": 800, "price": 500},
    {"id": 152, "name": "HAV Antibody IgM", "matchNames": ["HAV Antibody IgM", "Hep A IgM"], "mrp": 800, "price": 500},
    {"id": 153, "name": "Hbe Ag", "matchNames": ["Hbe Ag"], "mrp": 800, "price": 400},
    {"id": 154, "name": "HBsAg By CLIA", "matchNames": ["HBsAg By CLIA", "Hepatitis B"], "mrp": 700, "price": 350},
    {"id": 155, "name": "HBV DNA Qualitative By PCR", "matchNames": ["HBV DNA Qualitative"], "mrp": 2200, "price": 1300},
    {"id": 156, "name": "HBV DNA Quantitative Viral Load By PCR", "matchNames": ["HBV DNA Quantitative Viral Load By PCR", "HBV DNA Quantitative"], "mrp": 4000, "price": 2500},
    {"id": 157, "name": "HCO3(Bi-Carbonate)", "matchNames": ["HCO3", "Bicarbonate"], "mrp": 1200, "price": 400},
    {"id": 158, "name": "HCV By CLIA", "matchNames": ["HCV By CLIA", "Hepatitis C"], "mrp": 700, "price": 600},
    {"id": 159, "name": "HCV RNA Qualitative By RT PCR", "matchNames": ["HCV RNA Qualitative"], "mrp": 3000, "price": 2000},
    {"id": 160, "name": "HCV RNA Quantitative By RT PCR", "matchNames": ["HCV RNA Quantitative"], "mrp": 4800, "price": 3500},
    {"id": 161, "name": "HIV I Qualitative PCR", "matchNames": ["HIV I Qualitative PCR"], "mrp": 2500, "price": 1600},
    {"id": 162, "name": "HIV I Quantitative Viral Load By PCR", "matchNames": ["HIV I Quantitative Viral Load"], "mrp": 4500, "price": 3300},
    {"id": 163, "name": "HIV By CLIA", "matchNames": ["HIV By CLIA", "HIV"], "mrp": 700, "price": 350},
    {"id": 164, "name": "HIV Western Blot", "matchNames": ["HIV Western Blot"], "mrp": 2500, "price": 1700},
    {"id": 165, "name": "HLAB27", "matchNames": ["HLAB27"], "mrp": 2000, "price": 1300},
    {"id": 166, "name": "Homa Index Insulin Resistance Test", "matchNames": ["Homa Index"], "mrp": 800, "price": 400},
    {"id": 167, "name": "Homocysteine", "matchNames": ["Homocysteine"], "mrp": 1200, "price": 800},
    {"id": 168, "name": "HsCRP", "matchNames": ["HsCRP"], "mrp": 400, "price": 350},
    {"id": 169, "name": "HSV I & II By PCR Qualitative", "matchNames": ["HSV I & II By PCR"], "mrp": 3500, "price": 2600},
    {"id": 170, "name": "HSV II IgG", "matchNames": ["HSV II IgG"], "mrp": 400, "price": 200},
    {"id": 171, "name": "HSV II IgG IgM", "matchNames": ["HSV II IgG IgM"], "mrp": 800, "price": 400},
    {"id": 172, "name": "HSV II IgM", "matchNames": ["HSV II IgM"], "mrp": 400, "price": 200},
    {"id": 173, "name": "HSV I IgG", "matchNames": ["HSV I IgG"], "mrp": 400, "price": 200},
    {"id": 174, "name": "HSV I IgG IgM", "matchNames": ["HSV I IgG IgM"], "mrp": 800, "price": 400},
    {"id": 175, "name": "HSV I IgM", "matchNames": ["HSV I IgM"], "mrp": 400, "price": 200},
    {"id": 176, "name": "IgA", "matchNames": ["IgA"], "mrp": 600, "price": 300},
    {"id": 177, "name": "IgE", "matchNames": ["IgE"], "mrp": 600, "price": 350},
    {"id": 178, "name": "IgF-1", "matchNames": ["IgF-1"], "mrp": 1600, "price": 1200},
    {"id": 179, "name": "IgG", "matchNames": ["IgG"], "mrp": 600, "price": 300},
    {"id": 180, "name": "IgM", "matchNames": ["IgM"], "mrp": 600, "price": 300},
    {"id": 181, "name": "Inorganic Phosphorous", "matchNames": ["Inorganic Phosphorous", "Phosphorous"], "mrp": 400, "price": 200},
    {"id": 182, "name": "Insulin FBS", "matchNames": ["Insulin FBS", "Fasting Insulin"], "mrp": 800, "price": 400},
    {"id": 183, "name": "Insulin FBS PPBS", "matchNames": ["Insulin FBS PPBS"], "mrp": 1600, "price": 800},
    {"id": 184, "name": "Insulin PG1H", "matchNames": ["Insulin PG1H"], "mrp": 800, "price": 400},
    {"id": 185, "name": "Insulin PG2H", "matchNames": ["Insulin PG2H"], "mrp": 800, "price": 400},
    {"id": 186, "name": "Insulin PG30", "matchNames": ["Insulin PG30"], "mrp": 800, "price": 400},
    {"id": 187, "name": "Insulin PPBS", "matchNames": ["Insulin PPBS"], "mrp": 800, "price": 400},
    {"id": 188, "name": "Insulin RBS", "matchNames": ["Insulin RBS"], "mrp": 800, "price": 400},
    {"id": 189, "name": "Ionized Calcium", "matchNames": ["Ionized Calcium"], "mrp": 600, "price": 300},
    {"id": 190, "name": "Iron , Tibc ,Transferrin Saturation", "matchNames": ["Iron Studies", "Iron Profile"], "mrp": 1000, "price": 500},
    {"id": 191, "name": "Iron Level", "matchNames": ["Iron Level"], "mrp": 500, "price": 300},
    {"id": 192, "name": "Karyotyping Couple", "matchNames": ["Karyotyping Couple"], "mrp": 4700, "price": 3600},
    {"id": 193, "name": "KOH For Fungus", "matchNames": ["KOH For Fungus", "KOH Smear"], "mrp": 500, "price": 300},
    {"id": 194, "name": "LDH", "matchNames": ["LDH"], "mrp": 600, "price": 300},
    {"id": 195, "name": "LDL Cholesterol(Direct)", "matchNames": ["LDL Cholesterol", "LDL"], "mrp": 600, "price": 300},
    {"id": 196, "name": "LH", "matchNames": ["LH", "Luteinizing Hormone"], "mrp": 550, "price": 250},
    {"id": 197, "name": "Lipase Estimation", "matchNames": ["Lipase Estimation", "Lipase"], "mrp": 600, "price": 400},
    {"id": 198, "name": "Lipid Profile", "matchNames": ["Lipid Profile", "lipid profile", "Cholesterol Test", "लिपिड प्रोफाइल", "lipied profile", "lipd profile", "લિપિડ પ્રોફાઈલ"], "mrp": 700, "price": 350},
    {"id": 199, "name": "Lipoprotein (A)", "matchNames": ["Lipoprotein (A)"], "mrp": 800, "price": 600},
    {"id": 200, "name": "Lithium", "matchNames": ["Lithium"], "mrp": 700, "price": 350},
    {"id": 201, "name": "LKM-1", "matchNames": ["LKM-1"], "mrp": 2000, "price": 1700},
    {"id": 202, "name": "Lupus Anti Coagulant", "matchNames": ["Lupus Anti Coagulant", "LAC"], "mrp": 1500, "price": 800},
    {"id": 203, "name": "Magnesium Level", "matchNames": ["Magnesium Level"], "mrp": 450, "price": 300},
    {"id": 204, "name": "Mantoux Test(M.T.)", "matchNames": ["Mantoux Test", "Mantoux"], "mrp": 200, "price": 100},
    {"id": 205, "name": "Measles Antibody IgG IgM", "matchNames": ["Measles Antibody"], "mrp": 1000, "price": 600},
    {"id": 206, "name": "Malaria Test", "matchNames": ["Malaria Test", "Malaria", "मलेरिया", "MP Test", "mp test", "MP By Antigen Card", "Malaria Antigen"], "mrp": 300, "price": 150},
    {"id": 207, "name": "Multiplex Respiratory Viral Panel", "matchNames": ["Multiplex Respiratory Viral Panel"], "mrp": 5000, "price": 5000},
    {"id": 208, "name": "Mumps Antibody Titer IgG", "matchNames": ["Mumps Antibody Titer IgG"], "mrp": 600, "price": 300},
    {"id": 209, "name": "Mumps Antibody Titre IgM", "matchNames": ["Mumps Antibody Titre IgM"], "mrp": 600, "price": 300},
    {"id": 210, "name": "Neonatal Bilirubin", "matchNames": ["Neonatal Bilirubin"], "mrp": 300, "price": 150},
    {"id": 211, "name": "NT Pro BNP", "matchNames": ["NT Pro BNP"], "mrp": 1800, "price": 1600},
    {"id": 212, "name": "PPBS", "matchNames": ["PPBS", "Post Prandial Blood Sugar", "PP Sugar", "पीपी शुगर", "Post Prandial", "PP Test", "P. P.Plasma Glucose Analysis", "PP Plasma Glucose"], "mrp": 160, "price": 80},
    {"id": 213, "name": "Parathyroid Hormone Level", "matchNames": ["Parathyroid Hormone Level", "PTH"], "mrp": 900, "price": 600},
    {"id": 214, "name": "Phenytoin Level", "matchNames": ["Phenytoin Level"], "mrp": 800, "price": 400},
    {"id": 215, "name": "Plasma Osmolarity", "matchNames": ["Plasma Osmolarity"], "mrp": 800, "price": 400},
    {"id": 216, "name": "Plasma Renin Activity", "matchNames": ["Plasma Renin Activity", "Renin"], "mrp": 1000, "price": 800},
    {"id": 217, "name": "Platelets Count", "matchNames": ["Platelets Count", "Platelet"], "mrp": 250, "price": 100},
    {"id": 218, "name": "Potassium", "matchNames": ["Potassium"], "mrp": 300, "price": 150},
    {"id": 219, "name": "Pro Calcitonin", "matchNames": ["Pro Calcitonin", "PCT"], "mrp": 2400, "price": 150},
    {"id": 220, "name": "Progesterone Estimation", "matchNames": ["Progesterone Estimation"], "mrp": 550, "price": 350},
    {"id": 221, "name": "Prolactin Estimation", "matchNames": ["Prolactin Estimation", "Prolactin"], "mrp": 550, "price": 250},
    {"id": 222, "name": "Protein Electrophorosis", "matchNames": ["Protein Electrophorosis"], "mrp": 1000, "price": 500},
    {"id": 223, "name": "Protein Level", "matchNames": ["Protein Level", "Total Protein"], "mrp": 300, "price": 150},
    {"id": 224, "name": "Prothrombin Time", "matchNames": ["Prothrombin Time", "PT INR"], "mrp": 300, "price": 200},
    {"id": 225, "name": "PSA", "matchNames": ["PSA", "Prostate Specific Antigen"], "mrp": 700, "price": 350},
    {"id": 226, "name": "Pus Culture", "matchNames": ["Pus Culture"], "mrp": 650, "price": 400},
    {"id": 227, "name": "Quadrople Marker", "matchNames": ["Quadrople Marker"], "mrp": 3000, "price": 2600},
    {"id": 228, "name": "RA", "matchNames": ["RA Factor", "Rheumatoid Arthritis"], "mrp": 700, "price": 350},
    {"id": 229, "name": "Random Blood Sugar", "matchNames": ["Random Blood Sugar", "RBS"], "mrp": 100, "price": 50},
    {"id": 230, "name": "Retic Count", "matchNames": ["Retic Count", "Reticulocyte Count"], "mrp": 300, "price": 300},
    {"id": 231, "name": "RPR", "matchNames": ["RPR"], "mrp": 200, "price": 100},
    {"id": 232, "name": "Rubela IgG", "matchNames": ["Rubela IgG", "Rubella IgG"], "mrp": 400, "price": 200},
    {"id": 233, "name": "Rubela IgG & IgM", "matchNames": ["Rubela IgG & IgM", "Rubella IgG IgM"], "mrp": 800, "price": 400},
    {"id": 234, "name": "Rubela IgM", "matchNames": ["Rubela IgM", "Rubella IgM"], "mrp": 400, "price": 200},
    {"id": 235, "name": "S.G.O.T. (AST)", "matchNames": ["S.G.O.T.", "AST", "SGOT"], "mrp": 300, "price": 150},
    {"id": 236, "name": "S.G.P.T. (ALT)", "matchNames": ["S.G.P.T.", "ALT", "SGPT"], "mrp": 300, "price": 150},
    {"id": 237, "name": "Semen Analysis", "matchNames": ["Semen Analysis"], "mrp": 1000, "price": 700},
    {"id": 238, "name": "Serum Acetone", "matchNames": ["Serum Acetone"], "mrp": 500, "price": 250},
    {"id": 239, "name": "Serum Immunofixation Electrophoresis", "matchNames": ["Serum Immunofixation Electrophoresis"], "mrp": 4800, "price": 3600},
    {"id": 240, "name": "Serum Osmolality", "matchNames": ["Serum Osmolality"], "mrp": 800, "price": 400},
    {"id": 241, "name": "Sodium", "matchNames": ["Sodium"], "mrp": 300, "price": 150},
    {"id": 242, "name": "Sp.AFB", "matchNames": ["Sp.AFB", "Sputum AFB"], "mrp": 250, "price": 100},
    {"id": 243, "name": "Sp.AFB 3 Days", "matchNames": ["Sp.AFB 3 Days"], "mrp": 750, "price": 300},
    {"id": 244, "name": "Sperm DNA Fragmentation", "matchNames": ["Sperm DNA Fragmentation"], "mrp": 5000, "price": 4000},
    {"id": 245, "name": "Sputum Culture", "matchNames": ["Sputum Culture"], "mrp": 650, "price": 400},
    {"id": 246, "name": "Sputum For KOH", "matchNames": ["Sputum For KOH"], "mrp": 250, "price": 150},
    {"id": 247, "name": "Sputum Genexpert", "matchNames": ["Sputum Genexpert", "Genexpert"], "mrp": 2200, "price": 1900},
    {"id": 248, "name": "Sputum Routien", "matchNames": ["Sputum Routien", "Sputum Routine"], "mrp": 400, "price": 300},
    {"id": 249, "name": "Stool Calprotectin", "matchNames": ["Stool Calprotectin"], "mrp": 2200, "price": 1900},
    {"id": 250, "name": "Stool Culture", "matchNames": ["Stool Culture"], "mrp": 650, "price": 400},
    {"id": 251, "name": "Stool Examination", "matchNames": ["Stool Examination", "Stool Routine"], "mrp": 250, "price": 100},
    {"id": 252, "name": "Stool For AFB", "matchNames": ["Stool For AFB"], "mrp": 250, "price": 100},
    {"id": 253, "name": "Stool For Clostridia Difficile Toxin A & B", "matchNames": ["Stool For Clostridia Difficile"], "mrp": 3500, "price": 3500},
    {"id": 254, "name": "Stool For Modified Z N Stain", "matchNames": ["Stool For Modified Z N Stain"], "mrp": 400, "price": 200},
    {"id": 255, "name": "Stool OBT", "matchNames": ["Stool OBT", "Occult Blood"], "mrp": 150, "price": 50},
    {"id": 256, "name": "Stool OBT 3 Days", "matchNames": ["Stool OBT 3 Days"], "mrp": 450, "price": 150},
    {"id": 257, "name": "Stool R & M For 3 Days", "matchNames": ["Stool R & M For 3 Days"], "mrp": 750, "price": 300},
    {"id": 258, "name": "Sugar (Post-Dinner)", "matchNames": ["Sugar (Post-Dinner)", "Post Dinner Sugar"], "mrp": 100, "price": 50},
    {"id": 259, "name": "Sugar(15 Min. - 75 Gm Glucose)", "matchNames": ["Sugar 75 Gm Glucose"], "mrp": 100, "price": 50},
    {"id": 260, "name": "Sugar(Post Lunch)", "matchNames": ["Sugar(Post Lunch)", "Post Lunch Sugar", "PPBS"], "mrp": 100, "price": 50},
    {"id": 261, "name": "Sugar(Pre Dinner)", "matchNames": ["Sugar(Pre Dinner)", "Pre Dinner Sugar"], "mrp": 100, "price": 50},
    {"id": 262, "name": "Sugar(Pre Lunch)", "matchNames": ["Sugar(Pre Lunch)", "Pre Lunch Sugar"], "mrp": 100, "price": 50},
    {"id": 263, "name": "Swab Culture", "matchNames": ["Swab Culture"], "mrp": 650, "price": 400},
    {"id": 264, "name": "Syphilis By CLIA", "matchNames": ["Syphilis By CLIA", "Syphilis"], "mrp": 600, "price": 600},
    {"id": 265, "name": "T3", "matchNames": ["T3", "Triiodothyronine"], "mrp": 200, "price": 130},
    {"id": 266, "name": "T4", "matchNames": ["T4", "Thyroxine"], "mrp": 200, "price": 130},
    {"id": 267, "name": "Tb Gold", "matchNames": ["Tb Gold", "TB Gold"], "mrp": 3000, "price": 2600},
    {"id": 268, "name": "TB PCR (Quantitative)", "matchNames": ["TB PCR (Quantitative)"], "mrp": 1800, "price": 900},
    {"id": 269, "name": "Testosterone", "matchNames": ["Testosterone"], "mrp": 550, "price": 350},
    {"id": 270, "name": "Thyroglobulin", "matchNames": ["Thyroglobulin"], "mrp": 1300, "price": 650},
    {"id": 271, "name": "TIBC", "matchNames": ["TIBC"], "mrp": 450, "price": 350},
    {"id": 272, "name": "Torch Complex", "matchNames": ["Torch Complex"], "mrp": 2400, "price": 1200},
    {"id": 273, "name": "Toxoplasma IgG", "matchNames": ["Toxoplasma IgG"], "mrp": 400, "price": 200},
    {"id": 274, "name": "Toxoplasma IgG & IgM", "matchNames": ["Toxoplasma IgG & IgM"], "mrp": 800, "price": 400},
    {"id": 275, "name": "Toxoplasma IgM", "matchNames": ["Toxoplasma IgM"], "mrp": 400, "price": 200},
    {"id": 276, "name": "TPHA", "matchNames": ["TPHA"], "mrp": 600, "price": 150},
    {"id": 277, "name": "Triglycerides", "matchNames": ["Triglycerides"], "mrp": 260, "price": 130},
    {"id": 278, "name": "Tripple Marker", "matchNames": ["Tripple Marker", "Triple Marker"], "mrp": 3000, "price": 1300},
    {"id": 279, "name": "Troponin I (Quantitative)", "matchNames": ["Troponin I"], "mrp": 1000, "price": 500},
    {"id": 280, "name": "Troponin T", "matchNames": ["Troponin T"], "mrp": 1000, "price": 600},
    {"id": 281, "name": "TSH (Ultrasensitive)", "matchNames": ["TSH (Ultrasensitive)", "TSH"], "mrp": 250, "price": 150},
    {"id": 282, "name": "TSH Receptor Antibody", "matchNames": ["TSH Receptor Antibody"], "mrp": 4000, "price": 2600},
    {"id": 283, "name": "TTG IgA", "matchNames": ["TTG IgA"], "mrp": 1000, "price": 900},
    {"id": 284, "name": "Typhi By ELISA", "matchNames": ["Typhi By ELISA", "Typhoid ELISA"], "mrp": 600, "price": 600},
    {"id": 285, "name": "Typhidot", "matchNames": ["Typhidot"], "mrp": 600, "price": 300},
    {"id": 286, "name": "Typhidot IgG/IgM", "matchNames": ["Typhidot IgG/IgM"], "mrp": 700, "price": 350},
    {"id": 287, "name": "Typhoid Antigen Antibody Test", "matchNames": ["Typhoid Antigen Antibody Test"], "mrp": 600, "price": 300},
    {"id": 288, "name": "Urea", "matchNames": ["Urea"], "mrp": 300, "price": 150},
    {"id": 289, "name": "Uric Acid", "matchNames": ["Uric Acid", "uric acid", "यूरिक एसिड", "Gout Test", "યુરિક એસિડ"], "mrp": 300, "price": 150},
    {"id": 290, "name": "Urinary Albumin Creatinine Ratio", "matchNames": ["Urinary Albumin Creatinine Ratio"], "mrp": 800, "price": 400},
    {"id": 291, "name": "Urinary Protein", "matchNames": ["Urinary Protein"], "mrp": 500, "price": 150},
    {"id": 292, "name": "Urine Acetone", "matchNames": ["Urine Acetone"], "mrp": 100, "price": 50},
    {"id": 293, "name": "Urine AFB 3 Days", "matchNames": ["Urine AFB 3 Days"], "mrp": 750, "price": 300},
    {"id": 294, "name": "Urine B.J.Protein", "matchNames": ["Urine B.J.Protein", "Bence Jones Protein"], "mrp": 200, "price": 100},
    {"id": 295, "name": "Urine Calcium", "matchNames": ["Urine Calcium"], "mrp": 250, "price": 150},
    {"id": 296, "name": "Urine Creatinine", "matchNames": ["Urine Creatinine"], "mrp": 300, "price": 150},
    {"id": 297, "name": "Urine Culture", "matchNames": ["Urine Culture"], "mrp": 700, "price": 350},
    {"id": 298, "name": "Urine For AFB", "matchNames": ["Urine For AFB"], "mrp": 250, "price": 100},
    {"id": 299, "name": "Urine For Bile Pigment And Salt", "matchNames": ["Urine Bile Pigment", "Bile Salt"], "mrp": 80, "price": 40},
    {"id": 300, "name": "Urine Gene Expert", "matchNames": ["Urine Gene Expert"], "mrp": 2200, "price": 1700},
    {"id": 301, "name": "Urine Microalbumin", "matchNames": ["Urine Microalbumin"], "mrp": 600, "price": 300},
    {"id": 302, "name": "Urine Osmolality", "matchNames": ["Urine Osmolality"], "mrp": 800, "price": 400},
    {"id": 303, "name": "Urine Porphobilinogen", "matchNames": ["Urine Porphobilinogen"], "mrp": 350, "price": 150},
    {"id": 304, "name": "Urine Potassium", "matchNames": ["Urine Potassium"], "mrp": 300, "price": 150},
    {"id": 305, "name": "Urine Pregnancy Test", "matchNames": ["Urine Pregnancy Test", "UPT"], "mrp": 300, "price": 100},
    {"id": 306, "name": "Urine Protein Creatinine Ratio", "matchNames": ["Urine Protein Creatinine Ratio", "PCR"], "mrp": 900, "price": 450},
    {"id": 307, "name": "Urine Routine", "matchNames": ["Urine Routine", "Urine R&M", "यूरिन रूटीन", "urine test", "urine routine", "Urine RM", "Urine Test", "યૂરિન રૂટિન"], "mrp": 250, "price": 70},
    {"id": 308, "name": "Urine Sodium", "matchNames": ["Urine Sodium"], "mrp": 300, "price": 150},
    {"id": 309, "name": "Urine Toxicology", "matchNames": ["Urine Toxicology"], "mrp": 1800, "price": 1800},
    {"id": 310, "name": "Valporic Acid", "matchNames": ["Valporic Acid"], "mrp": 800, "price": 500},
    {"id": 311, "name": "Varicella Zoster Ab. IgG IgM", "matchNames": ["Varicella Zoster", "Chicken Pox"], "mrp": 2000, "price": 1500},
    {"id": 312, "name": "VDRL", "matchNames": ["VDRL"], "mrp": 400, "price": 100},
    {"id": 313, "name": "Vitamin B-12", "matchNames": ["Vitamin B-12", "B12", "b12", "Vitamin B12", "vitamin b12", "विटामिन बी12", "B-12", "Vit B12", "વિટામિન B12"], "mrp": 900, "price": 400},
    {"id": 314, "name": "Vitamin D", "matchNames": ["Vitamin D", "vitamin d", "Vit D", "विटामिन डी", "Vitamin D3", "D3", "25-OH Vitamin D", "વિટામિન ડી"], "mrp": 1400, "price": 600},
    {"id": 315, "name": "Widal Test", "matchNames": ["Widal Test", "Widal", "widal", "Typhoid Test", "typhoid", "Typhoid", "टाइफाइड"], "mrp": 300, "price": 150},
    {"id": 316, "name": "Zinc Level", "matchNames": ["Zinc Level", "Zinc"], "mrp": 1500, "price": 1300},
    {"id": 317, "name": "Kidney Function Test", "matchNames": ["Kidney Function Test", "KFT", "RFT", "Renal Function", "किडनी फंक्शन", "kidney function", "કિડની ફંક્શન"], "mrp": 1100, "price": 550},
    {"id": 318, "name": "Liver Function Test", "matchNames": ["Liver Function Test", "LFT", "Liver Function", "लिवर फंक्शन", "liver function", "લિવર ફંક્શન", "SGPT SGOT"], "mrp": 1300, "price": 650},
    {"id": 319, "name": "Thyroid Profile", "matchNames": ["Thyroid Profile", "thyroid", "Thyroid", "थायरॉइड", "T3 T4 TSH", "TSH", "tsh", "thyroid test", "Thyroid Test", "થાઇરોઇડ"], "mrp": 1000, "price": 550}
]

# ─────────────────────────────────────────────────────────────────────────────
# LOOKUP FUNCTIONS
# ─────────────────────────────────────────────────────────────────────────────

def find_test_price(query: str, max_results: int = 3) -> list[dict]:
    """
    Find test prices matching a patient query.

    Strategy (in order of priority):
      1. Exact substring match (fast, zero-dependency)
      2. Fuzzy match via rapidfuzz (handles typos, voice-to-text errors)

    Returns a list of matched test dicts (up to max_results).
    Each result includes 'formatted_price' and 'formatted_mrp' for convenience.
    """
    if not query:
        return []

    query_lower = query.lower().strip()
    exact_matches = []
    seen_ids = set()

    # Pass 1: exact substring matching
    for test in test_prices:
        name_match = test["name"].lower() in query_lower
        alias_match = any(alias.lower() in query_lower for alias in test["matchNames"])

        if (name_match or alias_match) and test["id"] not in seen_ids:
            seen_ids.add(test["id"])
            exact_matches.append(_enrich_test(test))

        if len(exact_matches) >= max_results:
            break

    if exact_matches:
        return exact_matches

    # Pass 2: fuzzy matching for typos / voice-to-text errors
    # Only runs if no exact match found
    try:
        from rapidfuzz import process, fuzz

        # Build a flat candidate list: (test, alias_string)
        candidates = []
        for test in test_prices:
            for alias in [test["name"]] + test["matchNames"]:
                candidates.append((test, alias))

        # Score each candidate
        scored = []
        for test, alias in candidates:
            score = fuzz.partial_ratio(query_lower, alias.lower())
            if score >= 75:  # threshold: adjust if too many false positives
                scored.append((score, test))

        # Sort by score descending, deduplicate by id
        scored.sort(key=lambda x: x[0], reverse=True)
        fuzzy_matches = []
        fuzzy_seen = set()
        for score, test in scored:
            if test["id"] not in fuzzy_seen and test["id"] not in seen_ids:
                fuzzy_seen.add(test["id"])
                fuzzy_matches.append(_enrich_test(test))
            if len(fuzzy_matches) >= max_results:
                break

        return fuzzy_matches

    except ImportError:
        # rapidfuzz not installed — graceful fallback to empty
        return []


def _enrich_test(test: dict) -> dict:
    """Add formatted price strings to a test dict copy."""
    enriched = test.copy()
    enriched["formatted_price"] = f"{test['price']} rupees"
    enriched["formatted_mrp"] = f"{test['mrp']} rupees"
    enriched["savings"] = test["mrp"] - test["price"]
    enriched["formatted_savings"] = f"{test['mrp'] - test['price']} rupees"
    return enriched


def get_test_preparation(test_name: str, lang: str = "en") -> str:
    """
    Return the sample preparation instructions for a test in the requested language.

    Args:
        test_name: name or alias of the test
        lang: "en", "hi", or "gu"

    Returns:
        Preparation instruction string.
    """
    if not test_name:
        return _no_prep(lang)

    lower = test_name.lower()

    if any(k in lower for k in ["fasting", "fbs", "f.b.s", "homocysteine"]):
        return {
            "gu": "૧૦ થી ૧૨ કલાક નું ફાસ્ટિંગ (ભૂખ્યા પેટે) જરૂરી છે. માત્ર પાણી પી શકો છો. ૧૨ કલાકથી વધારે ભૂખ્યા ન રહેવું — એ રિપોર્ટ ખોટો આવી શકે.",
            "hi": "10 से 12 घंटे की फास्टिंग (खाली पेट) ज़रूरी है। सिर्फ पानी पी सकते हैं। 12 घंटे से ज़्यादा भूखे न रहें — इससे रिपोर्ट गलत आ सकती है।",
            "en": "Strictly 10-12 hours fasting required. Only water is allowed. Do NOT fast for more than 12 hours — overfasting gives incorrect results.",
        }.get(lang, "Strictly 10-12 hours fasting required. Only water allowed. Do not overfast beyond 12 hours.")

    if any(k in lower for k in ["ppbs", "post lunch", "post prandial", "post-dinner", "post dinner", "pp sugar"]):
        return {
            "gu": "જમ્યાના બરાબર ૨ કલાક પછી સેમ્પલ આપવાનું છે.",
            "hi": "खाने के ठीक 2 घंटे बाद सैंपल देना है।",
            "en": "Sample must be given exactly 2 hours after a meal.",
        }.get(lang, "Sample exactly 2 hours after a meal.")

    if any(k in lower for k in ["lipid", "cholesterol", "triglyceride"]):
        return {
            "gu": "૧૦ થી ૧૨ કલાક નું ફાસ્ટિંગ જરૂરી છે. રાત્રે ભારે જમવાનું ટાળો. ૧૨ કલાકથી વધુ ભૂખ્યા ન રહેવું.",
            "hi": "10 से 12 घंटे की फास्टिंग ज़रूरी है। रात में भारी खाना न खाएं। 12 घंटे से ज़्यादा भूखे न रहें।",
            "en": "10-12 hours fasting required. Avoid heavy dinner. Do NOT fast beyond 12 hours.",
        }.get(lang, "10-12 hours fasting. Avoid heavy dinner. No overfasting.")

    if any(k in lower for k in ["thyroid", "tsh", "t3", "t4", "free t3", "free t4"]):
        return {
            "gu": "સવારનું સેમ્પલ આપવું વધુ સારું છે. ખાલી પેટ હોય તો વધુ સારું.",
            "hi": "सुबह का सैंपल देना बेहतर है। खाली पेट हो तो और अच्छा।",
            "en": "Morning sample preferred. Empty stomach is ideal but not mandatory.",
        }.get(lang, "Morning sample preferred.")

    if any(k in lower for k in ["urine culture", "urine routine", "urine r&m", "urine rm"]):
        return {
            "gu": "સવારનું પ્રથમ મિડ-સ્ટ્રીમ યુરિન સેમ્પલ આપવું. ક્લીન કન્ટેઇનરમાં.",
            "hi": "सुबह का पहला मिड-स्ट्रीम यूरिन सैंपल देना है। साफ कंटेनर में।",
            "en": "First morning mid-stream urine sample. Use a clean container.",
        }.get(lang, "First morning mid-stream urine sample.")

    if any(k in lower for k in ["vitamin d", "vit d", "d3"]):
        return {
            "gu": "કોઈ ખાસ તૈયારી ની જરૂર નથી, ગમે ત્યારે સેમ્પલ આપી શકો.",
            "hi": "कोई खास परहेज़ नहीं, कभी भी सैंपल दे सकते हैं।",
            "en": "No special preparation needed. Sample can be given anytime.",
        }.get(lang, "No special preparation needed.")

    if any(k in lower for k in ["b12", "vitamin b", "vit b"]):
        return {
            "gu": "કોઈ ખાસ સાવચેતી નથી, ગમે ત્યારે સેમ્પલ આપી શકો.",
            "hi": "कोई खास परहेज़ नहीं, कभी भी सैंपल दे सकते हैं।",
            "en": "No special preparation needed. Anytime sample.",
        }.get(lang, "No special preparation needed.")

    if "cortisol am" in lower:
        return {
            "gu": "સવારે ૮ થી ૯ વાગ્યા વચ્ચે સેમ્પલ આપવું જોઈએ.",
            "hi": "सुबह 8 से 9 बजे के बीच सैंपल देना चाहिए।",
            "en": "Sample must be collected between 8-9 AM.",
        }.get(lang, "Sample between 8-9 AM.")

    if "cortisol pm" in lower:
        return {
            "gu": "સાંજે ૪ થી ૫ વાગ્યા વચ્ચે સેમ્પલ આપવું જોઈએ.",
            "hi": "शाम 4 से 5 बजे के बीच सैंपल देना चाहिए।",
            "en": "Sample must be collected between 4-5 PM.",
        }.get(lang, "Sample between 4-5 PM.")

    if any(k in lower for k in ["stool", "occult blood"]):
        return {
            "gu": "સ્ટૂલ સેમ્પલ ક્લીન, ડ્રાય કન્ટેઇનરમાં આપો. 3 દિવસ ના સ્ટૂલ OBT માટે.",
            "hi": "स्टूल सैंपल साफ, सूखे कंटेनर में दें। OBT के लिए 3 दिन।",
            "en": "Stool sample in a clean, dry container. For OBT: 3 consecutive days.",
        }.get(lang, "Clean stool sample. OBT requires 3 days.")

    return _no_prep(lang)


def _no_prep(lang: str) -> str:
    return {
        "gu": "આ ટેસ્ટ માટે કોઈ ખાસ તૈયારી ની જરૂર નથી.",
        "hi": "इस टेस्ट के लिए किसी विशेष तैयारी की आवश्यकता नहीं है।",
        "en": "No special preparation required for this test.",
    }.get(lang, "No special preparation required.")


# ─────────────────────────────────────────────────────────────────────────────
# HOME COLLECTION CHARGE CALCULATOR
# ─────────────────────────────────────────────────────────────────────────────

def calculate_home_collection_charge(total_amount: int) -> dict:
    """
    Calculate the home collection charge based on Sun Pathology's tiered policy.

    Args:
        total_amount: total bill amount in rupees (integer)

    Returns:
        dict with keys:
            charge (int): home collection charge in rupees
            is_free (bool): True if home collection is free
            message_en (str): human-readable message in English
            message_hi (str): human-readable message in Hindi
            message_gu (str): human-readable message in Gujarati
    """
    if total_amount < 350:
        charge = 100
        is_free = False
    elif total_amount < 650:
        charge = 50
        is_free = False
    else:
        charge = 0
        is_free = True

    total_payable = total_amount + charge

    if is_free:
        return {
            "charge": 0,
            "is_free": True,
            "total_payable": total_amount,
            "message_en": f"Great news! Since your total is {total_amount} rupees, home collection is completely FREE.",
            "message_hi": f"खुशखबरी! आपका कुल बिल {total_amount} रुपये है, इसलिए होम कलेक्शन बिल्कुल मुफ्त है।",
            "message_gu": f"સારા સમાચાર! તમારો કુલ બિલ {total_amount} રૂપિયા છે, એટલે હોમ કલેક્શન સંપૂર્ણ ફ્રી છે.",
        }
    else:
        return {
            "charge": charge,
            "is_free": False,
            "total_payable": total_payable,
            "message_en": f"Your test total is {total_amount} rupees. Home collection charge will be {charge} rupees. Total payable: {total_payable} rupees.",
            "message_hi": f"आपके टेस्ट का कुल {total_amount} रुपये है। होम कलेक्शन चार्ज {charge} रुपये होगा। कुल देय: {total_payable} रुपये।",
            "message_gu": f"તમારા ટેસ્ટ નો કુલ {total_amount} રૂપિયા છે. હોમ કલેક્શન ચાર્જ {charge} રૂપિયા રહેશે. કુલ ચૂકવવાનો: {total_payable} રૂપિયા.",
        }