"""
MediBuddy - Healthcare Database
Comprehensive drug, payer, pricing, and interaction data.
"""

from models import (
    Drug, DrugIdentifiers, DrugPricing, DrugWarning, DrugIndication,
    DrugInteraction, DrugSchedule, PregnancyCategory, InteractionSeverity,
    Payer, PayerType, CoverageDetails, FormularyTier,
    SpecialtyPharmacy, JCode
)
from typing import Dict, List, Optional
import random

# ============================================================================
# DRUG DATABASE - 50+ Common Medications
# ============================================================================

DRUGS_DB: Dict[str, Drug] = {}

def _create_drug(
    id: str, brand: str, generic: str, manufacturer: str,
    ndc: str, gpi: str, ahfs: str, drug_class: str, mechanism: str,
    forms: List[str], strengths: List[str], route: str,
    indications: List[tuple], contraindications: List[str],
    warnings: List[tuple], adverse_effects: List[str],
    schedule: DrugSchedule, pregnancy: PregnancyCategory, lactation_safe: bool,
    awp: float, wac: float, nadac: float = None, goodrx: float = None,
    rems: bool = False, pa_required: bool = False
) -> Drug:
    return Drug(
        id=id,
        brand_name=brand,
        generic_name=generic,
        manufacturer=manufacturer,
        identifiers=DrugIdentifiers(ndc=ndc, gpi=gpi, gcn=f"GCN{random.randint(10000,99999)}", ahfs=ahfs),
        dosage_forms=forms,
        strengths=strengths,
        route=route,
        drug_class=drug_class,
        mechanism=mechanism,
        indications=[DrugIndication(condition=c, fda_approved=a, evidence_level=e) for c, a, e in indications],
        contraindications=contraindications,
        warnings=[DrugWarning(type=t, title=ti, description=d) for t, ti, d in warnings],
        adverse_effects=adverse_effects,
        schedule=schedule,
        pregnancy_category=pregnancy,
        lactation_safe=lactation_safe,
        pricing=DrugPricing(
            awp=awp, wac=wac, nadac=nadac,
            asp=wac * 1.06 if wac else None,
            price_340b=wac * 0.5 if wac else None,
            goodrx_low=goodrx,
            costplus_price=wac * 0.15 + 3 if wac else None
        ),
        requires_prior_auth=pa_required,
        rems_required=rems
    )

# === Diabetes Medications ===
DRUGS_DB["metformin"] = _create_drug(
    "metformin", "Glucophage", "metformin HCl", "Bristol-Myers Squibb",
    "00087-6060-05", "27200020000310", "68:20.04", "Biguanide", "Decreases hepatic glucose production, increases insulin sensitivity",
    ["Tablet", "Tablet Extended-Release", "Oral Solution"], ["500mg", "850mg", "1000mg"], "Oral",
    [("Type 2 Diabetes Mellitus", True, None), ("Polycystic Ovary Syndrome", False, "B"), ("Weight Management", False, "C")],
    ["Hypersensitivity to metformin", "Severe renal impairment (eGFR <30)", "Metabolic acidosis"],
    [("Black Box", "Lactic Acidosis", "Metformin may cause lactic acidosis, a rare but serious condition. Risk increases with renal impairment, sepsis, dehydration, excess alcohol, hepatic impairment, and hypoxic states.")],
    ["GI upset", "Diarrhea", "Nausea", "Vitamin B12 deficiency", "Metallic taste"],
    DrugSchedule.NONE, PregnancyCategory.B, False,
    45.00, 12.50, 4.20, 4.00
)

DRUGS_DB["ozempic"] = _create_drug(
    "ozempic", "Ozempic", "semaglutide", "Novo Nordisk",
    "00169-4132-12", "27700060102110", "68:20.06", "GLP-1 Receptor Agonist", "Stimulates insulin release, suppresses glucagon, slows gastric emptying",
    ["Injection Pen"], ["0.25mg/dose", "0.5mg/dose", "1mg/dose", "2mg/dose"], "Subcutaneous",
    [("Type 2 Diabetes Mellitus", True, None), ("Cardiovascular Risk Reduction", True, None), ("Obesity", False, "A")],
    ["Personal/family history of MTC", "MEN 2 syndrome", "Hypersensitivity"],
    [("Black Box", "Thyroid C-Cell Tumors", "In rodents, semaglutide causes thyroid C-cell tumors. Contraindicated in patients with MEN 2 or personal/family history of MTC.")],
    ["Nausea", "Vomiting", "Diarrhea", "Abdominal pain", "Constipation", "Injection site reactions"],
    DrugSchedule.NONE, PregnancyCategory.C, False,
    1029.35, 935.77, None, 892.00, pa_required=True
)

DRUGS_DB["jardiance"] = _create_drug(
    "jardiance", "Jardiance", "empagliflozin", "Boehringer Ingelheim",
    "00597-0152-30", "27700050302010", "68:20.18", "SGLT2 Inhibitor", "Inhibits SGLT2 in kidneys, increasing urinary glucose excretion",
    ["Tablet"], ["10mg", "25mg"], "Oral",
    [("Type 2 Diabetes", True, None), ("Heart Failure", True, None), ("CKD", True, None)],
    ["Severe renal impairment", "Dialysis", "Type 1 diabetes"],
    [],
    ["UTI", "Genital mycotic infections", "Hypotension", "Ketoacidosis"],
    DrugSchedule.NONE, PregnancyCategory.C, False,
    628.20, 570.18, None, 542.00, pa_required=True
)

# === Cardiovascular ===
DRUGS_DB["lisinopril"] = _create_drug(
    "lisinopril", "Prinivil/Zestril", "lisinopril", "Merck/AstraZeneca",
    "00006-0019-54", "36100010100310", "24:32.04", "ACE Inhibitor", "Inhibits angiotensin-converting enzyme, reduces angiotensin II",
    ["Tablet"], ["2.5mg", "5mg", "10mg", "20mg", "40mg"], "Oral",
    [("Hypertension", True, None), ("Heart Failure", True, None), ("Post-MI", True, None), ("Diabetic Nephropathy", True, None)],
    ["Angioedema history", "Bilateral renal artery stenosis", "Pregnancy"],
    [],
    ["Dry cough", "Hyperkalemia", "Dizziness", "Hypotension", "Angioedema (rare)"],
    DrugSchedule.NONE, PregnancyCategory.D, False,
    25.00, 8.50, 2.80, 4.00
)

DRUGS_DB["atorvastatin"] = _create_drug(
    "atorvastatin", "Lipitor", "atorvastatin calcium", "Pfizer",
    "00071-0155-40", "39400010100310", "24:06.08", "HMG-CoA Reductase Inhibitor", "Inhibits cholesterol synthesis in liver",
    ["Tablet"], ["10mg", "20mg", "40mg", "80mg"], "Oral",
    [("Hyperlipidemia", True, None), ("ASCVD Prevention", True, None), ("Familial Hypercholesterolemia", True, None)],
    ["Active liver disease", "Pregnancy", "Breastfeeding"],
    [],
    ["Myalgia", "Elevated LFTs", "Headache", "GI upset", "Rhabdomyolysis (rare)"],
    DrugSchedule.NONE, PregnancyCategory.X, False,
    312.00, 15.20, 4.50, 9.00
)

DRUGS_DB["warfarin"] = _create_drug(
    "warfarin", "Coumadin", "warfarin sodium", "Bristol-Myers Squibb",
    "00056-0172-75", "83200030100310", "20:12.04", "Vitamin K Antagonist", "Inhibits vitamin K-dependent clotting factors (II, VII, IX, X)",
    ["Tablet"], ["1mg", "2mg", "2.5mg", "3mg", "4mg", "5mg", "6mg", "7.5mg", "10mg"], "Oral",
    [("DVT/PE Treatment", True, None), ("AFib Stroke Prevention", True, None), ("Mechanical Heart Valve", True, None)],
    ["Active bleeding", "Pregnancy", "Severe uncontrolled hypertension"],
    [("Black Box", "Bleeding Risk", "Warfarin can cause major or fatal bleeding. Regular INR monitoring required. Many drug and food interactions exist.")],
    ["Bleeding", "Bruising", "Skin necrosis (rare)", "Purple toe syndrome"],
    DrugSchedule.NONE, PregnancyCategory.X, False,
    35.00, 18.50, 7.20, 8.00
)

DRUGS_DB["eliquis"] = _create_drug(
    "eliquis", "Eliquis", "apixaban", "Bristol-Myers Squibb/Pfizer",
    "00003-0893-21", "83200050202010", "20:12.04", "Factor Xa Inhibitor", "Directly inhibits factor Xa, reducing thrombin generation",
    ["Tablet"], ["2.5mg", "5mg"], "Oral",
    [("AFib Stroke Prevention", True, None), ("DVT/PE Treatment", True, None), ("DVT/PE Prophylaxis", True, None)],
    ["Active pathological bleeding", "Severe hypersensitivity"],
    [("Black Box", "Spinal Hematoma", "Epidural or spinal hematomas may occur with neuraxial anesthesia. Risk increased with indwelling catheters, NSAIDs, or platelet inhibitors."),
     ("Black Box", "Discontinuation Risk", "Premature discontinuation increases risk of thrombotic events. If anticoagulation must be discontinued, consider bridge therapy.")],
    ["Bleeding", "Anemia", "Bruising", "Nausea"],
    DrugSchedule.NONE, PregnancyCategory.B, False,
    598.00, 543.00, None, 480.00
)

DRUGS_DB["metoprolol"] = _create_drug(
    "metoprolol", "Lopressor/Toprol-XL", "metoprolol", "Novartis/AstraZeneca",
    "00028-0051-01", "33200020200310", "24:24.00", "Beta-1 Selective Blocker", "Blocks beta-1 adrenergic receptors in heart",
    ["Tablet", "Tablet Extended-Release", "Injection"], ["25mg", "50mg", "100mg", "200mg"], "Oral/IV",
    [("Hypertension", True, None), ("Angina", True, None), ("Heart Failure", True, None), ("Post-MI", True, None), ("AFib Rate Control", True, None)],
    ["Severe bradycardia", "Heart block", "Cardiogenic shock", "Decompensated HF"],
    [],
    ["Bradycardia", "Fatigue", "Dizziness", "Cold extremities", "Depression"],
    DrugSchedule.NONE, PregnancyCategory.C, True,
    38.00, 12.00, 3.50, 4.00
)

# === Pain / Controlled Substances ===
DRUGS_DB["oxycodone"] = _create_drug(
    "oxycodone", "OxyContin/Roxicodone", "oxycodone HCl", "Purdue/Various",
    "59011-0420-10", "65100020100320", "28:08.08", "Opioid Agonist", "Binds to mu-opioid receptors in CNS",
    ["Tablet", "Tablet Extended-Release", "Capsule", "Oral Solution"], ["5mg", "10mg", "15mg", "20mg", "30mg", "40mg", "80mg"], "Oral",
    [("Severe Pain", True, None)],
    ["Respiratory depression", "Paralytic ileus", "Known hypersensitivity"],
    [("Black Box", "Addiction/Abuse/Misuse", "Oxycodone exposes patients to risks of opioid addiction, abuse, and misuse, leading to overdose and death."),
     ("Black Box", "Respiratory Depression", "Serious, life-threatening, or fatal respiratory depression may occur."),
     ("REMS", "Opioid REMS", "REMS program required to mitigate risk of addiction, abuse, and misuse.")],
    ["Constipation", "Nausea", "Sedation", "Respiratory depression", "Euphoria", "Pruritus"],
    DrugSchedule.CII, PregnancyCategory.C, False,
    180.00, 95.00, 42.00, 35.00, rems=True, pa_required=True
)

DRUGS_DB["gabapentin"] = _create_drug(
    "gabapentin", "Neurontin", "gabapentin", "Pfizer",
    "00071-0805-24", "72600030000310", "28:12.92", "GABA Analog", "Binds to alpha-2-delta calcium channel subunit",
    ["Capsule", "Tablet", "Oral Solution"], ["100mg", "300mg", "400mg", "600mg", "800mg"], "Oral",
    [("Epilepsy (Partial Seizures)", True, None), ("Postherpetic Neuralgia", True, None), ("Neuropathic Pain", False, "A"), ("Restless Legs", False, "B")],
    ["Hypersensitivity to gabapentin"],
    [],
    ["Dizziness", "Somnolence", "Peripheral edema", "Ataxia", "Fatigue"],
    DrugSchedule.CV, PregnancyCategory.C, True,
    159.00, 28.00, 8.50, 12.00
)

# === Antibiotics ===
DRUGS_DB["amoxicillin"] = _create_drug(
    "amoxicillin", "Amoxil", "amoxicillin", "GlaxoSmithKline/Various",
    "00029-6008-31", "01200010200310", "08:12.16", "Aminopenicillin", "Inhibits bacterial cell wall synthesis",
    ["Capsule", "Tablet", "Oral Suspension"], ["250mg", "500mg", "875mg"], "Oral",
    [("Respiratory Tract Infections", True, None), ("Otitis Media", True, None), ("H. pylori (with clarithromycin/PPI)", True, None), ("UTI", True, None)],
    ["Penicillin allergy", "Mononucleosis (rash risk)"],
    [],
    ["Diarrhea", "Nausea", "Rash", "Vaginitis"],
    DrugSchedule.NONE, PregnancyCategory.B, True,
    32.00, 8.50, 3.20, 4.00
)

DRUGS_DB["azithromycin"] = _create_drug(
    "azithromycin", "Zithromax/Z-Pak", "azithromycin", "Pfizer",
    "00069-3060-75", "01200020102010", "08:12.12", "Macrolide", "Binds 50S ribosomal subunit, inhibits protein synthesis",
    ["Tablet", "Oral Suspension", "IV"], ["250mg", "500mg", "600mg"], "Oral/IV",
    [("Community-Acquired Pneumonia", True, None), ("COPD Exacerbation", True, None), ("Chlamydia", True, None), ("MAC Prophylaxis", True, None)],
    ["Hypersensitivity to macrolides", "Cholestatic jaundice history"],
    [],
    ["Diarrhea", "Nausea", "Abdominal pain", "QT prolongation"],
    DrugSchedule.NONE, PregnancyCategory.B, True,
    58.00, 22.00, 8.50, 12.00
)

# === Mental Health ===
DRUGS_DB["sertraline"] = _create_drug(
    "sertraline", "Zoloft", "sertraline HCl", "Pfizer",
    "00049-4900-66", "58160034100310", "28:16.04", "SSRI", "Selectively inhibits serotonin reuptake",
    ["Tablet", "Oral Solution"], ["25mg", "50mg", "100mg"], "Oral",
    [("Major Depressive Disorder", True, None), ("Panic Disorder", True, None), ("PTSD", True, None), ("OCD", True, None), ("Social Anxiety", True, None)],
    ["MAO inhibitor use (within 14 days)", "Pimozide use", "Disulfiram use (oral solution)"],
    [("Black Box", "Suicidal Ideation", "Antidepressants increase suicidal thinking and behavior in children, adolescents, and young adults. Monitor closely for clinical worsening.")],
    ["Nausea", "Diarrhea", "Insomnia", "Sexual dysfunction", "Dizziness", "Dry mouth"],
    DrugSchedule.NONE, PregnancyCategory.C, True,
    245.00, 18.00, 5.20, 8.00
)

DRUGS_DB["alprazolam"] = _create_drug(
    "alprazolam", "Xanax", "alprazolam", "Pfizer",
    "00009-0029-01", "57100010000310", "28:24.08", "Benzodiazepine", "Enhances GABA-A receptor activity",
    ["Tablet", "Tablet Extended-Release", "Oral Solution", "ODT"], ["0.25mg", "0.5mg", "1mg", "2mg"], "Oral",
    [("Anxiety Disorders", True, None), ("Panic Disorder", True, None)],
    ["Acute narrow-angle glaucoma", "Ketoconazole/itraconazole use"],
    [("Black Box", "Opioid Interaction", "Concomitant use with opioids may result in profound sedation, respiratory depression, coma, and death."),
     ("Black Box", "Dependence", "Risk of abuse, physical dependence, and withdrawal. Limit duration and taper gradually.")],
    ["Sedation", "Dizziness", "Memory impairment", "Dependence", "Paradoxical reactions"],
    DrugSchedule.CIV, PregnancyCategory.D, False,
    128.00, 32.00, 12.50, 15.00
)

# === Respiratory ===
DRUGS_DB["albuterol"] = _create_drug(
    "albuterol", "ProAir/Ventolin/Proventil", "albuterol sulfate", "Various",
    "00173-0682-20", "44200010200370", "12:12.08", "Short-Acting Beta-2 Agonist", "Relaxes bronchial smooth muscle",
    ["Inhalation Aerosol (MDI)", "Nebulizer Solution", "Tablet"], ["90mcg/actuation", "0.083%", "2mg", "4mg"], "Inhalation/Oral",
    [("Asthma (acute)", True, None), ("COPD (acute)", True, None), ("Exercise-Induced Bronchospasm", True, None)],
    ["Hypersensitivity"],
    [],
    ["Tachycardia", "Tremor", "Nervousness", "Headache", "Hypokalemia"],
    DrugSchedule.NONE, PregnancyCategory.C, True,
    78.00, 45.00, 22.00, 25.00
)

DRUGS_DB["symbicort"] = _create_drug(
    "symbicort", "Symbicort", "budesonide/formoterol", "AstraZeneca",
    "00186-0372-20", "44200060202030", "12:12.08", "ICS/LABA Combination", "Corticosteroid + long-acting beta-2 agonist",
    ["Inhalation Aerosol"], ["80/4.5mcg", "160/4.5mcg"], "Inhalation",
    [("Asthma (maintenance)", True, None), ("COPD (maintenance)", True, None)],
    ["Primary treatment of acute bronchospasm"],
    [("Black Box", "Asthma-Related Death", "LABAs increase the risk of asthma-related death. Use only with ICS.")],
    ["Oral candidiasis", "Headache", "Nasopharyngitis", "Upper respiratory infection"],
    DrugSchedule.NONE, PregnancyCategory.C, True,
    362.00, 328.00, None, 285.00
)

# === GI ===
DRUGS_DB["omeprazole"] = _create_drug(
    "omeprazole", "Prilosec", "omeprazole", "AstraZeneca/Various",
    "00186-5020-31", "49270040000310", "56:28.36", "Proton Pump Inhibitor", "Irreversibly inhibits H+/K+-ATPase proton pump",
    ["Capsule Delayed-Release", "Tablet", "Oral Suspension"], ["10mg", "20mg", "40mg"], "Oral",
    [("GERD", True, None), ("Peptic Ulcer Disease", True, None), ("H. pylori Eradication", True, None), ("Zollinger-Ellison", True, None)],
    ["Hypersensitivity to PPIs"],
    [],
    ["Headache", "Diarrhea", "Abdominal pain", "C. diff risk", "Vitamin B12 deficiency", "Bone fracture (long-term)"],
    DrugSchedule.NONE, PregnancyCategory.C, True,
    268.00, 14.00, 3.80, 4.00
)

# === Thyroid ===
DRUGS_DB["levothyroxine"] = _create_drug(
    "levothyroxine", "Synthroid/Levoxyl", "levothyroxine sodium", "AbbVie/Various",
    "00074-6624-90", "30100010100310", "68:36.04", "Thyroid Hormone", "Replaces endogenous thyroxine (T4)",
    ["Tablet", "Capsule", "Injection"], ["25mcg", "50mcg", "75mcg", "88mcg", "100mcg", "112mcg", "125mcg", "137mcg", "150mcg", "175mcg", "200mcg", "300mcg"], "Oral/IV",
    [("Hypothyroidism", True, None), ("TSH Suppression (thyroid cancer)", True, None), ("Myxedema Coma", True, None)],
    ["Untreated adrenal insufficiency", "Acute MI (relative)"],
    [],
    ["Tachycardia", "Palpitations", "Weight loss", "Insomnia", "Heat intolerance", "Bone loss (overtreatment)"],
    DrugSchedule.NONE, PregnancyCategory.A, True,
    72.00, 28.00, 12.50, 8.00
)

# === Biologics / Specialty ===
DRUGS_DB["humira"] = _create_drug(
    "humira", "Humira", "adalimumab", "AbbVie",
    "00074-4339-02", "66100010002050", "92:36.00", "TNF-alpha Inhibitor", "Human IgG1 monoclonal antibody targeting TNF-alpha",
    ["Prefilled Syringe", "Prefilled Pen"], ["40mg/0.8mL", "40mg/0.4mL"], "Subcutaneous",
    [("Rheumatoid Arthritis", True, None), ("Psoriatic Arthritis", True, None), ("Ankylosing Spondylitis", True, None), ("Crohn's Disease", True, None), ("Ulcerative Colitis", True, None), ("Plaque Psoriasis", True, None)],
    ["Active serious infections"],
    [("Black Box", "Serious Infections", "Risk of serious infections leading to hospitalization or death, including TB, fungal, bacterial, and viral infections."),
     ("Black Box", "Malignancy", "Lymphoma and other malignancies reported in children and adolescents.")],
    ["Injection site reactions", "URI", "Headache", "Rash", "Serious infections"],
    DrugSchedule.NONE, PregnancyCategory.B, True,
    7021.00, 6380.00, None, None, pa_required=True
)

DRUGS_DB["keytruda"] = _create_drug(
    "keytruda", "Keytruda", "pembrolizumab", "Merck",
    "00006-3026-02", "21200080002080", "10:00.00", "PD-1 Inhibitor", "Humanized IgG4 anti-PD-1 monoclonal antibody",
    ["IV Solution"], ["100mg/4mL"], "Intravenous",
    [("Melanoma", True, None), ("NSCLC", True, None), ("HNSCC", True, None), ("Hodgkin Lymphoma", True, None), ("Urothelial Carcinoma", True, None), ("MSI-H/dMMR Cancers", True, None)],
    ["None absolute - evaluate risk/benefit"],
    [],
    ["Fatigue", "Diarrhea", "Nausea", "Immune-mediated adverse reactions (pneumonitis, colitis, hepatitis, nephritis, endocrinopathies)"],
    DrugSchedule.NONE, PregnancyCategory.D, False,
    10897.00, 9906.00, None, None, pa_required=True
)

# Add more drugs... (abbreviated for brevity, full list would have 50+)
DRUGS_DB["amlodipine"] = _create_drug(
    "amlodipine", "Norvasc", "amlodipine besylate", "Pfizer",
    "00069-1530-66", "34000010100310", "24:28.08", "Calcium Channel Blocker", "Inhibits calcium influx in vascular smooth muscle",
    ["Tablet"], ["2.5mg", "5mg", "10mg"], "Oral",
    [("Hypertension", True, None), ("Coronary Artery Disease", True, None), ("Angina", True, None)],
    ["Hypersensitivity"],
    [],
    ["Peripheral edema", "Fatigue", "Flushing", "Palpitations", "Dizziness"],
    DrugSchedule.NONE, PregnancyCategory.C, True,
    92.00, 8.50, 2.80, 4.00
)

DRUGS_DB["losartan"] = _create_drug(
    "losartan", "Cozaar", "losartan potassium", "Merck",
    "00006-0951-31", "36100020100310", "24:32.08", "ARB", "Blocks angiotensin II AT1 receptors",
    ["Tablet"], ["25mg", "50mg", "100mg"], "Oral",
    [("Hypertension", True, None), ("Diabetic Nephropathy", True, None), ("Stroke Prevention (with LVH)", True, None)],
    ["Pregnancy", "Bilateral renal artery stenosis"],
    [],
    ["Dizziness", "Hyperkalemia", "Hypotension", "Fatigue", "Cough (less than ACEi)"],
    DrugSchedule.NONE, PregnancyCategory.D, False,
    168.00, 22.00, 8.50, 10.00
)

DRUGS_DB["prednisone"] = _create_drug(
    "prednisone", "Deltasone", "prednisone", "Various",
    "00591-5442-01", "22100010000310", "68:04.00", "Corticosteroid", "Decreases inflammation and immune response",
    ["Tablet", "Oral Solution"], ["1mg", "2.5mg", "5mg", "10mg", "20mg", "50mg"], "Oral",
    [("Inflammatory Conditions", True, None), ("Autoimmune Diseases", True, None), ("Allergic Reactions", True, None), ("Asthma Exacerbation", True, None)],
    ["Systemic fungal infections", "Live vaccines"],
    [],
    ["Hyperglycemia", "Weight gain", "Insomnia", "Mood changes", "Osteoporosis", "Adrenal suppression"],
    DrugSchedule.NONE, PregnancyCategory.C, True,
    18.00, 5.50, 2.10, 4.00
)

DRUGS_DB["montelukast"] = _create_drug(
    "montelukast", "Singulair", "montelukast sodium", "Merck",
    "00006-0711-31", "44200050100310", "48:10.24", "Leukotriene Receptor Antagonist", "Blocks cysteinyl leukotriene receptor",
    ["Tablet", "Chewable Tablet", "Oral Granules"], ["4mg", "5mg", "10mg"], "Oral",
    [("Asthma (maintenance)", True, None), ("Allergic Rhinitis", True, None), ("Exercise-Induced Bronchospasm", True, None)],
    ["Hypersensitivity"],
    [("Black Box", "Neuropsychiatric Events", "Serious neuropsychiatric events including suicidal thoughts/behavior reported. Evaluate risks vs benefits.")],
    ["Headache", "Abdominal pain", "Cough", "Neuropsychiatric events"],
    DrugSchedule.NONE, PregnancyCategory.B, True,
    298.00, 16.00, 6.20, 12.00
)

DRUGS_DB["fluticasone"] = _create_drug(
    "fluticasone", "Flonase", "fluticasone propionate", "GSK",
    "00173-0453-01", "44200080001060", "52:08.08", "Intranasal Corticosteroid", "Anti-inflammatory effect on nasal mucosa",
    ["Nasal Spray"], ["50mcg/spray"], "Intranasal",
    [("Allergic Rhinitis", True, None), ("Non-Allergic Rhinitis", True, None)],
    ["Hypersensitivity"],
    [],
    ["Headache", "Epistaxis", "Nasal irritation", "Pharyngitis"],
    DrugSchedule.NONE, PregnancyCategory.C, True,
    128.00, 18.00, 12.50, 14.00
)

DRUGS_DB["pantoprazole"] = _create_drug(
    "pantoprazole", "Protonix", "pantoprazole sodium", "Pfizer",
    "00008-0841-81", "49270070100310", "56:28.36", "Proton Pump Inhibitor", "Irreversibly inhibits H+/K+-ATPase",
    ["Tablet Delayed-Release", "IV"], ["20mg", "40mg"], "Oral/IV",
    [("GERD", True, None), ("Erosive Esophagitis", True, None), ("Zollinger-Ellison", True, None), ("Stress Ulcer Prophylaxis", True, None)],
    ["Hypersensitivity to PPIs"],
    [],
    ["Headache", "Diarrhea", "Nausea", "C. diff risk"],
    DrugSchedule.NONE, PregnancyCategory.B, True,
    428.00, 14.00, 4.20, 6.00
)

DRUGS_DB["tramadol"] = _create_drug(
    "tramadol", "Ultram", "tramadol HCl", "Various",
    "00045-0659-60", "65100060100310", "28:08.08", "Opioid Agonist + NRI/SRI", "Binds mu-opioid receptors, inhibits NE/5-HT reuptake",
    ["Tablet", "Tablet Extended-Release", "Capsule"], ["50mg", "100mg", "200mg", "300mg"], "Oral",
    [("Moderate to Moderately Severe Pain", True, None)],
    ["Significant respiratory depression", "Acute intoxication", "MAO inhibitor use"],
    [("Black Box", "Addiction/Abuse", "Risk of opioid addiction, abuse, and misuse."),
     ("Black Box", "Respiratory Depression", "Serious, life-threatening respiratory depression may occur."),
     ("Black Box", "Neonatal Opioid Withdrawal", "Prolonged use during pregnancy can result in NOWS.")],
    ["Nausea", "Dizziness", "Constipation", "Headache", "Somnolence", "Seizures (rare)"],
    DrugSchedule.CIV, PregnancyCategory.C, False,
    85.00, 22.00, 8.50, 15.00
)

DRUGS_DB["clopidogrel"] = _create_drug(
    "clopidogrel", "Plavix", "clopidogrel bisulfate", "Bristol-Myers Squibb/Sanofi",
    "00024-1877-10", "83100010100310", "20:12.18", "P2Y12 Inhibitor", "Irreversibly blocks P2Y12 ADP receptor on platelets",
    ["Tablet"], ["75mg", "300mg"], "Oral",
    [("ACS", True, None), ("Recent MI/Stroke/PAD", True, None), ("PCI with Stent", True, None)],
    ["Active bleeding", "Hypersensitivity"],
    [("Black Box", "CYP2C19 Poor Metabolizers", "Reduced effectiveness in CYP2C19 poor metabolizers. Consider alternative therapy.")],
    ["Bleeding", "Bruising", "Dyspepsia", "Diarrhea", "Rash"],
    DrugSchedule.NONE, PregnancyCategory.B, False,
    268.00, 18.00, 6.80, 12.00
)

# ============================================================================
# DRUG INTERACTIONS DATABASE
# ============================================================================

INTERACTIONS_DB: List[DrugInteraction] = [
    DrugInteraction(
        drug_a="warfarin", drug_b="aspirin", severity=InteractionSeverity.MAJOR,
        description="Increased bleeding risk",
        clinical_effect="Aspirin inhibits platelet function and may displace warfarin from protein binding, significantly increasing hemorrhagic risk.",
        management="Avoid combination unless specifically indicated (mechanical valve). If used, monitor INR closely and watch for signs of bleeding."
    ),
    DrugInteraction(
        drug_a="warfarin", drug_b="amiodarone", severity=InteractionSeverity.MAJOR,
        description="Increased warfarin effect",
        clinical_effect="Amiodarone inhibits CYP2C9 and CYP3A4, significantly increasing warfarin levels and anticoagulant effect.",
        management="Reduce warfarin dose by 30-50% when starting amiodarone. Monitor INR closely for 6-8 weeks."
    ),
    DrugInteraction(
        drug_a="metformin", drug_b="contrast dye", severity=InteractionSeverity.MAJOR,
        description="Lactic acidosis risk",
        clinical_effect="Iodinated contrast can cause acute kidney injury, reducing metformin clearance and increasing lactic acidosis risk.",
        management="Hold metformin 48 hours before and after contrast administration. Confirm renal function before resuming."
    ),
    DrugInteraction(
        drug_a="lisinopril", drug_b="potassium", severity=InteractionSeverity.MODERATE,
        description="Hyperkalemia risk",
        clinical_effect="ACE inhibitors reduce aldosterone, decreasing potassium excretion. Supplemental potassium can cause dangerous hyperkalemia.",
        management="Avoid potassium supplements unless hypokalemic. Monitor potassium levels regularly."
    ),
    DrugInteraction(
        drug_a="lisinopril", drug_b="NSAIDs", severity=InteractionSeverity.MODERATE,
        description="Reduced antihypertensive effect, AKI risk",
        clinical_effect="NSAIDs inhibit prostaglandins, reducing renal blood flow and counteracting ACE inhibitor benefits. Risk of acute kidney injury.",
        management="Use lowest NSAID dose for shortest duration. Monitor blood pressure and renal function."
    ),
    DrugInteraction(
        drug_a="sertraline", drug_b="tramadol", severity=InteractionSeverity.MAJOR,
        description="Serotonin syndrome risk",
        clinical_effect="Both drugs increase serotonin. Combination can cause potentially fatal serotonin syndrome.",
        management="Avoid combination if possible. If necessary, start with low doses and monitor for hyperthermia, rigidity, myoclonus."
    ),
    DrugInteraction(
        drug_a="alprazolam", drug_b="oxycodone", severity=InteractionSeverity.MAJOR,
        description="Profound sedation, respiratory depression",
        clinical_effect="Combined CNS depression can cause profound sedation, respiratory depression, coma, and death.",
        management="FDA Black Box Warning - Avoid concurrent use unless no alternatives. Use lowest doses and shortest duration."
    ),
    DrugInteraction(
        drug_a="clopidogrel", drug_b="omeprazole", severity=InteractionSeverity.MODERATE,
        description="Reduced clopidogrel effectiveness",
        clinical_effect="Omeprazole inhibits CYP2C19, reducing conversion of clopidogrel to active metabolite.",
        management="Use pantoprazole instead (less CYP2C19 inhibition) or consider H2 blocker if PPI needed."
    ),
    DrugInteraction(
        drug_a="methotrexate", drug_b="NSAIDs", severity=InteractionSeverity.MAJOR,
        description="Methotrexate toxicity",
        clinical_effect="NSAIDs reduce renal clearance of methotrexate, significantly increasing toxicity risk.",
        management="Avoid NSAIDs with high-dose methotrexate. With low-dose, use with caution and monitor closely."
    ),
    DrugInteraction(
        drug_a="simvastatin", drug_b="amiodarone", severity=InteractionSeverity.MAJOR,
        description="Increased myopathy/rhabdomyolysis risk",
        clinical_effect="Amiodarone inhibits CYP3A4 and transport proteins, significantly increasing simvastatin levels.",
        management="Do not exceed simvastatin 20mg daily with amiodarone. Consider atorvastatin or rosuvastatin instead."
    ),
    DrugInteraction(
        drug_a="fluoxetine", drug_b="MAOIs", severity=InteractionSeverity.MAJOR,
        description="Fatal serotonin syndrome",
        clinical_effect="Combination causes severe serotonin syndrome with hyperthermia, muscle rigidity, cardiovascular instability.",
        management="Contraindicated. Wait at least 5 weeks after stopping fluoxetine before starting MAOI (14 days MAOI to fluoxetine)."
    ),
    DrugInteraction(
        drug_a="digoxin", drug_b="amiodarone", severity=InteractionSeverity.MAJOR,
        description="Digoxin toxicity",
        clinical_effect="Amiodarone increases digoxin levels by 70-100% via P-gp inhibition and reduced renal clearance.",
        management="Reduce digoxin dose by 50% when starting amiodarone. Monitor digoxin levels and for toxicity."
    ),
    DrugInteraction(
        drug_a="lithium", drug_b="lisinopril", severity=InteractionSeverity.MAJOR,
        description="Lithium toxicity",
        clinical_effect="ACE inhibitors reduce lithium clearance, potentially causing lithium toxicity.",
        management="If combination necessary, monitor lithium levels closely. May need 50% dose reduction."
    ),
    DrugInteraction(
        drug_a="amlodipine", drug_b="simvastatin", severity=InteractionSeverity.MODERATE,
        description="Increased simvastatin levels",
        clinical_effect="Amlodipine inhibits CYP3A4, modestly increasing simvastatin levels and myopathy risk.",
        management="Do not exceed simvastatin 20mg daily with amlodipine."
    ),
    DrugInteraction(
        drug_a="metoprolol", drug_b="verapamil", severity=InteractionSeverity.MAJOR,
        description="Severe bradycardia, heart block, hypotension",
        clinical_effect="Both drugs slow AV conduction and decrease contractility. Combined effect can cause complete heart block.",
        management="Avoid combination. If necessary, monitor ECG and blood pressure closely."
    ),
]

# ============================================================================
# PAYER/FORMULARY DATABASE
# ============================================================================

def _create_coverage(tier: FormularyTier, copay: float = None, coinsurance: float = None,
                    pa: bool = False, pa_criteria: str = None, step: bool = False,
                    step_drugs: List[str] = None, ql: str = None) -> CoverageDetails:
    return CoverageDetails(
        tier=tier, copay=copay, coinsurance=coinsurance,
        prior_auth_required=pa, pa_criteria=pa_criteria,
        step_therapy_required=step, step_therapy_drugs=step_drugs,
        quantity_limit=ql
    )

PAYERS_DB: Dict[str, Payer] = {
    "aetna_comm": Payer(
        id="aetna_comm", name="Aetna", type=PayerType.COMMERCIAL, plan_name="Aetna Open Access",
        covered_drugs={
            "metformin": _create_coverage(FormularyTier.TIER_1, copay=10),
            "ozempic": _create_coverage(FormularyTier.TIER_3, copay=75, pa=True, pa_criteria="Must have tried and failed metformin. A1c >7% required.", step=True, step_drugs=["metformin", "glipizide"]),
            "jardiance": _create_coverage(FormularyTier.TIER_2, copay=45, pa=True, pa_criteria="Diabetes diagnosis with documented CVD or CKD for tier 2"),
            "lisinopril": _create_coverage(FormularyTier.TIER_1, copay=10),
            "atorvastatin": _create_coverage(FormularyTier.TIER_1, copay=10),
            "eliquis": _create_coverage(FormularyTier.TIER_2, copay=45),
            "humira": _create_coverage(FormularyTier.TIER_5, coinsurance=25, pa=True, pa_criteria="Must fail 2 conventional DMARDs. Specialist prescription required."),
            "sertraline": _create_coverage(FormularyTier.TIER_1, copay=10),
            "omeprazole": _create_coverage(FormularyTier.TIER_1, copay=10),
            "albuterol": _create_coverage(FormularyTier.TIER_1, copay=15),
            "symbicort": _create_coverage(FormularyTier.TIER_2, copay=50),
        }
    ),
    "bcbs_comm": Payer(
        id="bcbs_comm", name="Blue Cross Blue Shield", type=PayerType.COMMERCIAL, plan_name="BlueCross BlueShield PPO",
        covered_drugs={
            "metformin": _create_coverage(FormularyTier.TIER_1, copay=5),
            "ozempic": _create_coverage(FormularyTier.TIER_3, copay=90, pa=True, pa_criteria="A1c >7.5% after metformin therapy x 3 months"),
            "jardiance": _create_coverage(FormularyTier.TIER_3, copay=65, pa=True),
            "lisinopril": _create_coverage(FormularyTier.TIER_1, copay=5),
            "atorvastatin": _create_coverage(FormularyTier.TIER_1, copay=5),
            "eliquis": _create_coverage(FormularyTier.TIER_3, copay=65),
            "warfarin": _create_coverage(FormularyTier.TIER_1, copay=5),
            "humira": _create_coverage(FormularyTier.TIER_5, coinsurance=30, pa=True),
            "gabapentin": _create_coverage(FormularyTier.TIER_1, copay=10),
        }
    ),
    "united_comm": Payer(
        id="united_comm", name="UnitedHealthcare", type=PayerType.COMMERCIAL, plan_name="UHC Choice Plus",
        covered_drugs={
            "metformin": _create_coverage(FormularyTier.TIER_1, copay=10),
            "ozempic": _create_coverage(FormularyTier.TIER_2, copay=50, pa=False),  # Preferred!
            "jardiance": _create_coverage(FormularyTier.TIER_2, copay=45),
            "lisinopril": _create_coverage(FormularyTier.TIER_1, copay=10),
            "losartan": _create_coverage(FormularyTier.TIER_1, copay=10),
            "eliquis": _create_coverage(FormularyTier.TIER_2, copay=40),
            "keytruda": _create_coverage(FormularyTier.TIER_5, coinsurance=20, pa=True, pa_criteria="Oncologist prescription. FDA-approved indication required."),
        }
    ),
    "cigna_comm": Payer(
        id="cigna_comm", name="Cigna", type=PayerType.COMMERCIAL, plan_name="Cigna Open Access Plus",
        covered_drugs={
            "metformin": _create_coverage(FormularyTier.TIER_1, copay=10),
            "ozempic": _create_coverage(FormularyTier.TIER_3, copay=80, pa=True, step=True, step_drugs=["metformin"]),
            "lisinopril": _create_coverage(FormularyTier.TIER_1, copay=10),
            "amlodipine": _create_coverage(FormularyTier.TIER_1, copay=10),
            "sertraline": _create_coverage(FormularyTier.TIER_1, copay=10),
            "alprazolam": _create_coverage(FormularyTier.TIER_2, copay=25, ql="60 tablets/30 days"),
        }
    ),
    "humana_ma": Payer(
        id="humana_ma", name="Humana", type=PayerType.MEDICARE_ADV, plan_name="Humana Gold Plus HMO",
        covered_drugs={
            "metformin": _create_coverage(FormularyTier.TIER_1, copay=0),
            "ozempic": _create_coverage(FormularyTier.TIER_3, copay=47, pa=True),
            "lisinopril": _create_coverage(FormularyTier.TIER_1, copay=0),
            "atorvastatin": _create_coverage(FormularyTier.TIER_1, copay=0),
            "eliquis": _create_coverage(FormularyTier.TIER_3, copay=42),
            "levothyroxine": _create_coverage(FormularyTier.TIER_1, copay=0),
            "gabapentin": _create_coverage(FormularyTier.TIER_1, copay=5),
            "oxycodone": _create_coverage(FormularyTier.TIER_2, copay=15, pa=True, ql="120 tablets/30 days"),
        }
    ),
    "medicare_d": Payer(
        id="medicare_d", name="Medicare", type=PayerType.MEDICARE_D, plan_name="Medicare Part D Standard",
        covered_drugs={
            "metformin": _create_coverage(FormularyTier.TIER_1, copay=5),
            "ozempic": _create_coverage(FormularyTier.TIER_3, coinsurance=33),
            "jardiance": _create_coverage(FormularyTier.TIER_3, coinsurance=33),
            "lisinopril": _create_coverage(FormularyTier.TIER_1, copay=5),
            "warfarin": _create_coverage(FormularyTier.TIER_1, copay=5),
            "eliquis": _create_coverage(FormularyTier.TIER_3, coinsurance=33),
            "humira": _create_coverage(FormularyTier.TIER_5, coinsurance=25, pa=True),
        }
    ),
    "medicaid_tx": Payer(
        id="medicaid_tx", name="Texas Medicaid", type=PayerType.MEDICAID, state="TX", plan_name="Texas Medicaid",
        covered_drugs={
            "metformin": _create_coverage(FormularyTier.TIER_0, copay=0),
            "ozempic": _create_coverage(FormularyTier.TIER_3, copay=3, pa=True),
            "lisinopril": _create_coverage(FormularyTier.TIER_0, copay=0),
            "atorvastatin": _create_coverage(FormularyTier.TIER_0, copay=0),
            "sertraline": _create_coverage(FormularyTier.TIER_0, copay=0),
            "gabapentin": _create_coverage(FormularyTier.TIER_0, copay=0),
            "albuterol": _create_coverage(FormularyTier.TIER_0, copay=0),
        }
    ),
    "medicaid_ca": Payer(
        id="medicaid_ca", name="Medi-Cal", type=PayerType.MEDICAID, state="CA", plan_name="Medi-Cal Rx",
        covered_drugs={
            "metformin": _create_coverage(FormularyTier.TIER_0, copay=0),
            "ozempic": _create_coverage(FormularyTier.TIER_3, copay=1, pa=True, pa_criteria="Documented A1c >8%, BMI >27, failed metformin x 3 months"),
            "lisinopril": _create_coverage(FormularyTier.TIER_0, copay=0),
            "omeprazole": _create_coverage(FormularyTier.TIER_0, copay=0),
            "levothyroxine": _create_coverage(FormularyTier.TIER_0, copay=0),
            "prednisone": _create_coverage(FormularyTier.TIER_0, copay=0),
        }
    ),
    "medicaid_ny": Payer(
        id="medicaid_ny", name="NY Medicaid", type=PayerType.MEDICAID, state="NY", plan_name="New York Medicaid",
        covered_drugs={
            "metformin": _create_coverage(FormularyTier.TIER_0, copay=0),
            "jardiance": _create_coverage(FormularyTier.TIER_2, copay=1, pa=True),
            "lisinopril": _create_coverage(FormularyTier.TIER_0, copay=0),
            "losartan": _create_coverage(FormularyTier.TIER_0, copay=0),
            "metoprolol": _create_coverage(FormularyTier.TIER_0, copay=0),
            "sertraline": _create_coverage(FormularyTier.TIER_0, copay=0),
        }
    ),
    "medicaid_fl": Payer(
        id="medicaid_fl", name="Florida Medicaid", type=PayerType.MEDICAID, state="FL", plan_name="Florida Medicaid",
        covered_drugs={
            "metformin": _create_coverage(FormularyTier.TIER_0, copay=0),
            "lisinopril": _create_coverage(FormularyTier.TIER_0, copay=0),
            "amlodipine": _create_coverage(FormularyTier.TIER_0, copay=0),
            "omeprazole": _create_coverage(FormularyTier.TIER_0, copay=0),
            "fluticasone": _create_coverage(FormularyTier.TIER_0, copay=0),
            "montelukast": _create_coverage(FormularyTier.TIER_0, copay=0),
        }
    ),
}

# ============================================================================
# SPECIALTY PHARMACY DATABASE
# ============================================================================

SPECIALTY_PHARMACIES: List[SpecialtyPharmacy] = [
    SpecialtyPharmacy(
        id="cvs_specialty", name="CVS Specialty", phone="1-800-237-2767",
        specialty_drugs=["humira", "keytruda", "ozempic", "enbrel", "stelara"],
        states_served=["ALL"], buy_and_bill=True, white_bagging=True, brown_bagging=False
    ),
    SpecialtyPharmacy(
        id="accredo", name="Accredo (Express Scripts)", phone="1-800-803-2523",
        specialty_drugs=["humira", "keytruda", "remicade", "ocrevus"],
        states_served=["ALL"], buy_and_bill=True, white_bagging=True, brown_bagging=True
    ),
    SpecialtyPharmacy(
        id="optum_specialty", name="Optum Specialty Pharmacy", phone="1-855-427-4682",
        specialty_drugs=["humira", "enbrel", "ozempic", "trulicity"],
        states_served=["ALL"], buy_and_bill=False, white_bagging=True, brown_bagging=False
    ),
    SpecialtyPharmacy(
        id="briova", name="Briova Rx", phone="1-855-427-4682",
        specialty_drugs=["keytruda", "opdivo", "yervoy"],
        states_served=["ALL"], buy_and_bill=True, white_bagging=True, brown_bagging=True
    ),
]

# ============================================================================
# J-CODE DATABASE
# ============================================================================

JCODES_DB: Dict[str, JCode] = {
    "J0135": JCode(code="J0135", description="Injection, adalimumab, 20mg", drug_name="humira", asp_price=3190.50, rvu=0.00),
    "J9271": JCode(code="J9271", description="Injection, pembrolizumab, 1mg", drug_name="keytruda", asp_price=49.72, rvu=0.00),
    "J1745": JCode(code="J1745", description="Injection, infliximab, 10mg", drug_name="remicade", asp_price=95.84, rvu=0.00),
    "J2350": JCode(code="J2350", description="Injection, ocrelizumab, 1mg", drug_name="ocrevus", asp_price=8.62, rvu=0.00),
    "J3490": JCode(code="J3490", description="Unclassified drugs", drug_name="various", asp_price=0.00, rvu=0.00),
}

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def search_drugs(query: str, limit: int = 10) -> List[Drug]:
    """Search drugs by brand name, generic name, or drug class."""
    query = query.lower()
    results = []
    for drug in DRUGS_DB.values():
        if (query in drug.brand_name.lower() or 
            query in drug.generic_name.lower() or 
            query in drug.drug_class.lower()):
            results.append(drug)
        if len(results) >= limit:
            break
    return results

def get_drug(name: str) -> Optional[Drug]:
    """Get drug by ID, brand name, or generic name."""
    name_lower = name.lower().replace(" ", "").replace("-", "")
    
    # Direct ID lookup
    if name_lower in DRUGS_DB:
        return DRUGS_DB[name_lower]
    
    # Search by brand/generic name
    for drug in DRUGS_DB.values():
        if (name_lower == drug.brand_name.lower().replace(" ", "").replace("-", "") or
            name_lower == drug.generic_name.lower().replace(" ", "").replace("-", "")):
            return drug
    
    return None

def check_interactions(drug_names: List[str]) -> List[DrugInteraction]:
    """Check for interactions between a list of drugs."""
    interactions = []
    drug_names_lower = [d.lower() for d in drug_names]
    
    for interaction in INTERACTIONS_DB:
        a_lower = interaction.drug_a.lower()
        b_lower = interaction.drug_b.lower()
        
        if a_lower in drug_names_lower and b_lower in drug_names_lower:
            interactions.append(interaction)
    
    return interactions

def get_coverage(drug_name: str, payer_id: str = None, payer_name: str = None) -> List[tuple]:
    """Get coverage for a drug across payers."""
    drug = get_drug(drug_name)
    if not drug:
        return []
    
    results = []
    for payer in PAYERS_DB.values():
        if payer_id and payer.id != payer_id:
            continue
        if payer_name and payer_name.lower() not in payer.name.lower():
            continue
        
        if drug.id in payer.covered_drugs:
            results.append((payer, payer.covered_drugs[drug.id]))
    
    return results

def get_alternatives(drug_name: str) -> List[Drug]:
    """Get therapeutic alternatives for a drug."""
    drug = get_drug(drug_name)
    if not drug:
        return []
    
    alternatives = []
    for d in DRUGS_DB.values():
        if d.id != drug.id and d.drug_class == drug.drug_class:
            alternatives.append(d)
    
    return alternatives
