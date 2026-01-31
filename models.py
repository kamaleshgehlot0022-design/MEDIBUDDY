"""
MediBuddy - Pydantic Models
Enterprise healthcare data models for drugs, payers, pricing, and interactions.
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from enum import Enum
from datetime import date


# === Enums ===

class DrugSchedule(str, Enum):
    NONE = "None"
    CV = "Schedule V"
    CIV = "Schedule IV"
    CIII = "Schedule III"
    CII = "Schedule II"


class PregnancyCategory(str, Enum):
    A = "A - No risk in controlled studies"
    B = "B - No risk in animal studies"
    C = "C - Risk cannot be ruled out"
    D = "D - Positive evidence of risk"
    X = "X - Contraindicated in pregnancy"
    NA = "N/A - Not classified"


class FormularyTier(int, Enum):
    TIER_0 = 0  # Preferred generic - $0 copay
    TIER_1 = 1  # Generic
    TIER_2 = 2  # Preferred brand
    TIER_3 = 3  # Non-preferred brand
    TIER_4 = 4  # Specialty
    TIER_5 = 5  # Specialty - highest cost
    NOT_COVERED = 6


class InteractionSeverity(str, Enum):
    MAJOR = "Major"
    MODERATE = "Moderate"
    MINOR = "Minor"
    NONE = "None"


class PayerType(str, Enum):
    COMMERCIAL = "Commercial"
    MEDICARE_D = "Medicare Part D"
    MEDICARE_ADV = "Medicare Advantage"
    MEDICAID = "Medicaid"


# === Drug Models ===

class DrugIdentifiers(BaseModel):
    ndc: str = Field(..., description="11-digit National Drug Code")
    gpi: str = Field(..., description="Generic Product Identifier")
    gcn: Optional[str] = Field(None, description="Generic Code Number")
    ahfs: str = Field(..., description="AHFS Pharmacologic-Therapeutic Classification")


class DrugPricing(BaseModel):
    awp: float = Field(..., description="Average Wholesale Price")
    wac: float = Field(..., description="Wholesale Acquisition Cost")
    nadac: Optional[float] = Field(None, description="National Average Drug Acquisition Cost")
    asp: Optional[float] = Field(None, description="Average Sales Price")
    price_340b: Optional[float] = Field(None, description="340B ceiling price")
    goodrx_low: Optional[float] = Field(None, description="GoodRx lowest price")
    costplus_price: Optional[float] = Field(None, description="Mark Cuban Cost Plus price")


class DrugWarning(BaseModel):
    type: str  # "Black Box", "REMS", "Contraindication"
    title: str
    description: str


class DrugIndication(BaseModel):
    condition: str
    fda_approved: bool
    evidence_level: Optional[str] = None  # "A", "B", "C" for off-label


class Drug(BaseModel):
    id: str
    brand_name: str
    generic_name: str
    manufacturer: str
    identifiers: DrugIdentifiers
    dosage_forms: List[str]
    strengths: List[str]
    route: str
    drug_class: str
    mechanism: str
    indications: List[DrugIndication]
    contraindications: List[str]
    warnings: List[DrugWarning]
    adverse_effects: List[str]
    schedule: DrugSchedule
    pregnancy_category: PregnancyCategory
    lactation_safe: bool
    pricing: DrugPricing
    requires_prior_auth: bool = False
    rems_required: bool = False


class DrugInteraction(BaseModel):
    drug_a: str
    drug_b: str
    severity: InteractionSeverity
    description: str
    clinical_effect: str
    management: str


# === Payer/Coverage Models ===

class CoverageDetails(BaseModel):
    tier: FormularyTier
    copay: Optional[float] = None
    coinsurance: Optional[float] = None  # Percentage
    prior_auth_required: bool = False
    pa_criteria: Optional[str] = None
    step_therapy_required: bool = False
    step_therapy_drugs: Optional[List[str]] = None
    quantity_limit: Optional[str] = None
    age_restriction: Optional[str] = None
    diagnosis_restriction: Optional[List[str]] = None


class Payer(BaseModel):
    id: str
    name: str
    type: PayerType
    state: Optional[str] = None  # For Medicaid
    plan_name: str
    covered_drugs: dict  # drug_id -> CoverageDetails


class PriorAuthForm(BaseModel):
    drug_name: str
    payer_name: str
    patient_diagnosis: str
    clinical_justification: str
    supporting_trials: List[str]
    predicted_success_rate: float
    form_content: str
    appeal_letter: Optional[str] = None


# === Specialty Pharmacy Models ===

class SpecialtyPharmacy(BaseModel):
    id: str
    name: str
    phone: str
    specialty_drugs: List[str]
    states_served: List[str]
    buy_and_bill: bool
    white_bagging: bool
    brown_bagging: bool


class JCode(BaseModel):
    code: str
    description: str
    drug_name: str
    asp_price: float
    rvu: float


# === Request/Response Models ===

class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None


class ChatResponse(BaseModel):
    response: str
    sources: List[str] = []
    confidence: float = 0.95


class InteractionCheckRequest(BaseModel):
    drugs: List[str]


class InteractionCheckResponse(BaseModel):
    interactions: List[DrugInteraction]
    has_major_interaction: bool
    summary: str


class CoverageRequest(BaseModel):
    drug_name: str
    payer_id: Optional[str] = None
    payer_name: Optional[str] = None
    state: Optional[str] = None


class CoverageResponse(BaseModel):
    drug_name: str
    payer_name: str
    coverage: CoverageDetails
    alternatives: List[dict] = []


class PriorAuthRequest(BaseModel):
    drug_name: str
    payer_name: str
    diagnosis: str
    failed_alternatives: Optional[List[str]] = None
    patient_info: Optional[dict] = None


class DrugSearchRequest(BaseModel):
    query: str
    limit: int = 10


class PricingCompareRequest(BaseModel):
    drug_name: str
    quantity: int = 30
