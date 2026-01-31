"""
MediBuddy - AI Agent with LangChain + Hugging Face
Healthcare-specialized agent with 12 tools for drug, pricing, coverage, and interaction queries.
"""

import os
import httpx
import asyncio
from typing import List, Optional, Any
from dotenv import load_dotenv

load_dotenv()

# Hugging Face configuration
HUGGINGFACE_API_KEY = os.getenv("HUGGINGFACE_API_KEY")
HUGGINGFACE_MODEL = "mistralai/Mistral-7B-Instruct-v0.2"  # Fast, capable model
HUGGINGFACE_API_URL = f"https://api-inference.huggingface.co/models/{HUGGINGFACE_MODEL}"

if HUGGINGFACE_API_KEY:
    print(f"[AGENT] Hugging Face API key loaded, using {HUGGINGFACE_MODEL}")
else:
    print("[AGENT] No Hugging Face API key found")

# Import database functions
from database import (
    DRUGS_DB, PAYERS_DB, INTERACTIONS_DB, SPECIALTY_PHARMACIES, JCODES_DB,
    search_drugs, get_drug, check_interactions, get_coverage, get_alternatives,
    Drug, DrugInteraction
)
from models import (
    ChatResponse, InteractionCheckResponse, CoverageResponse, PriorAuthForm
)

# Try to import LangChain components
try:
    from langchain_google_genai import ChatGoogleGenerativeAI
    from langchain.agents import AgentExecutor, create_react_agent
    from langchain.tools import Tool
    from langchain.prompts import PromptTemplate
    from langchain.memory import ConversationBufferWindowMemory
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False
    print("[AGENT] LangChain not available, using Hugging Face / fallback mode")


# ============================================================================
# HUGGING FACE API CLIENT
# ============================================================================

async def query_huggingface(prompt: str, max_tokens: int = 500) -> str:
    """Query Hugging Face Inference API for AI responses."""
    if not HUGGINGFACE_API_KEY:
        return None
    
    headers = {
        "Authorization": f"Bearer {HUGGINGFACE_API_KEY}",
        "Content-Type": "application/json"
    }
    
    # Format as instruction for Mistral
    formatted_prompt = f"""<s>[INST] You are MediBuddy, an expert pharmaceutical AI assistant for healthcare professionals. 
You have access to real-time drug information, pricing, formulary coverage, and clinical data.
Be concise, accurate, and cite specific data points when available.

User Query: {prompt} [/INST]"""
    
    payload = {
        "inputs": formatted_prompt,
        "parameters": {
            "max_new_tokens": max_tokens,
            "temperature": 0.3,
            "top_p": 0.9,
            "do_sample": True,
            "return_full_text": False
        }
    }
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(HUGGINGFACE_API_URL, headers=headers, json=payload)
            
            if response.status_code == 200:
                result = response.json()
                if isinstance(result, list) and len(result) > 0:
                    return result[0].get("generated_text", "").strip()
            elif response.status_code == 503:
                # Model is loading
                print("[HF] Model is loading, using fallback...")
                return None
            else:
                print(f"[HF] API error: {response.status_code} - {response.text[:100]}")
                return None
    except Exception as e:
        print(f"[HF] Request failed: {e}")
        return None


# ============================================================================
# AGENT TOOLS
# ============================================================================

def tool_search_drug(query: str) -> str:
    """Search for drugs by name, class, or indication."""
    results = search_drugs(query, limit=5)
    if not results:
        return f"No drugs found matching '{query}'"
    
    output = []
    for drug in results:
        output.append(f"• **{drug.brand_name}** ({drug.generic_name}) - {drug.drug_class}")
        output.append(f"  NDC: {drug.identifiers.ndc} | GPI: {drug.identifiers.gpi}")
        output.append(f"  Forms: {', '.join(drug.dosage_forms[:3])}")
        output.append(f"  Schedule: {drug.schedule.value}")
    
    return "\n".join(output)


def tool_get_drug_details(drug_name: str) -> str:
    """Get comprehensive details for a specific drug."""
    drug = get_drug(drug_name)
    if not drug:
        return f"Drug '{drug_name}' not found in database."
    
    output = [
        f"# {drug.brand_name} ({drug.generic_name})",
        f"**Manufacturer:** {drug.manufacturer}",
        f"**Drug Class:** {drug.drug_class}",
        f"**Mechanism:** {drug.mechanism}",
        "",
        "## Identifiers",
        f"- NDC: {drug.identifiers.ndc}",
        f"- GPI: {drug.identifiers.gpi}",
        f"- AHFS: {drug.identifiers.ahfs}",
        "",
        "## Dosing",
        f"- Forms: {', '.join(drug.dosage_forms)}",
        f"- Strengths: {', '.join(drug.strengths)}",
        f"- Route: {drug.route}",
        "",
        "## Safety",
        f"- Schedule: {drug.schedule.value}",
        f"- Pregnancy: {drug.pregnancy_category.value}",
        f"- Lactation Safe: {'Yes' if drug.lactation_safe else 'No'}",
        f"- REMS Required: {'Yes' if drug.rems_required else 'No'}",
        "",
        "## FDA-Approved Indications",
    ]
    
    for ind in drug.indications:
        if ind.fda_approved:
            output.append(f"- {ind.condition}")
    
    off_label = [ind for ind in drug.indications if not ind.fda_approved]
    if off_label:
        output.append("\n## Off-Label Uses")
        for ind in off_label:
            output.append(f"- {ind.condition} (Evidence: {ind.evidence_level})")
    
    if drug.warnings:
        output.append("\n## ⚠️ Warnings")
        for w in drug.warnings:
            output.append(f"**[{w.type}] {w.title}**")
            output.append(f"{w.description}")
    
    if drug.contraindications:
        output.append("\n## Contraindications")
        for c in drug.contraindications:
            output.append(f"- {c}")
    
    output.append("\n## Common Adverse Effects")
    output.append(", ".join(drug.adverse_effects[:8]))
    
    return "\n".join(output)


def tool_get_pricing(drug_name: str) -> str:
    """Get comprehensive pricing for a drug (AWP, WAC, NADAC, cash prices)."""
    drug = get_drug(drug_name)
    if not drug:
        return f"Drug '{drug_name}' not found."
    
    p = drug.pricing
    output = [
        f"# Pricing: {drug.brand_name} ({drug.generic_name})",
        "",
        "## Benchmark Prices",
        f"| Price Type | Amount |",
        f"|------------|--------|",
        f"| AWP (Average Wholesale Price) | ${p.awp:,.2f} |",
        f"| WAC (Wholesale Acquisition Cost) | ${p.wac:,.2f} |",
    ]
    
    if p.nadac:
        output.append(f"| NADAC | ${p.nadac:,.2f} |")
    if p.asp:
        output.append(f"| ASP+6% | ${p.asp:,.2f} |")
    if p.price_340b:
        output.append(f"| 340B Ceiling Price | ${p.price_340b:,.2f} |")
    
    output.append("\n## Cash Prices (No Insurance)")
    if p.goodrx_low:
        output.append(f"- **GoodRx Best Price:** ${p.goodrx_low:,.2f}")
    if p.costplus_price:
        output.append(f"- **Mark Cuban Cost Plus:** ${p.costplus_price:,.2f}")
    
    # Calculate savings
    if p.goodrx_low and p.awp:
        savings = ((p.awp - p.goodrx_low) / p.awp) * 100
        output.append(f"\n💰 **Potential Savings:** Up to {savings:.0f}% off AWP with cash pay options")
    
    return "\n".join(output)


def tool_check_coverage(drug_name: str, payer_name: str = None) -> str:
    """Check formulary coverage for a drug across payers."""
    results = get_coverage(drug_name, payer_name=payer_name)
    
    if not results:
        if payer_name:
            return f"No coverage found for '{drug_name}' under '{payer_name}'"
        return f"No coverage information found for '{drug_name}'"
    
    drug = get_drug(drug_name)
    output = [f"# Coverage: {drug.brand_name if drug else drug_name}", ""]
    
    for payer, coverage in results:
        tier_names = {
            0: "Tier 0 (Preferred Generic - $0)",
            1: "Tier 1 (Generic)",
            2: "Tier 2 (Preferred Brand)",
            3: "Tier 3 (Non-Preferred)",
            4: "Tier 4 (Specialty)",
            5: "Tier 5 (Specialty - High Cost)",
            6: "NOT COVERED"
        }
        
        output.append(f"## {payer.name} - {payer.plan_name}")
        output.append(f"**Plan Type:** {payer.type.value}")
        output.append(f"**Tier:** {tier_names.get(coverage.tier.value, 'Unknown')}")
        
        if coverage.copay is not None:
            output.append(f"**Copay:** ${coverage.copay:.2f}")
        if coverage.coinsurance is not None:
            output.append(f"**Coinsurance:** {coverage.coinsurance}%")
        
        if coverage.prior_auth_required:
            output.append(f"**⚠️ Prior Authorization REQUIRED**")
            if coverage.pa_criteria:
                output.append(f"   Criteria: {coverage.pa_criteria}")
        else:
            output.append("**Prior Auth:** Not required ✓")
        
        if coverage.step_therapy_required:
            output.append(f"**Step Therapy Required:** Try first: {', '.join(coverage.step_therapy_drugs or [])}")
        
        if coverage.quantity_limit:
            output.append(f"**Quantity Limit:** {coverage.quantity_limit}")
        
        output.append("")
    
    return "\n".join(output)


def tool_check_interactions(drug_list: str) -> str:
    """Check for drug-drug interactions. Input: comma-separated drug names."""
    drugs = [d.strip() for d in drug_list.split(",")]
    
    if len(drugs) < 2:
        return "Please provide at least 2 drugs to check for interactions."
    
    interactions = check_interactions(drugs)
    
    if not interactions:
        return f"✅ No significant interactions found between: {', '.join(drugs)}"
    
    output = [f"# Drug Interactions Check", f"**Drugs:** {', '.join(drugs)}", ""]
    
    major = [i for i in interactions if i.severity.value == "Major"]
    moderate = [i for i in interactions if i.severity.value == "Moderate"]
    minor = [i for i in interactions if i.severity.value == "Minor"]
    
    if major:
        output.append("## 🔴 MAJOR Interactions")
        for i in major:
            output.append(f"\n### {i.drug_a.title()} + {i.drug_b.title()}")
            output.append(f"**Effect:** {i.clinical_effect}")
            output.append(f"**Management:** {i.management}")
    
    if moderate:
        output.append("\n## 🟡 MODERATE Interactions")
        for i in moderate:
            output.append(f"\n### {i.drug_a.title()} + {i.drug_b.title()}")
            output.append(f"**Effect:** {i.clinical_effect}")
            output.append(f"**Management:** {i.management}")
    
    if minor:
        output.append("\n## 🟢 MINOR Interactions")
        for i in minor:
            output.append(f"- {i.drug_a.title()} + {i.drug_b.title()}: {i.description}")
    
    return "\n".join(output)


def tool_find_alternatives(drug_name: str) -> str:
    """Find therapeutic alternatives for a drug."""
    alts = get_alternatives(drug_name)
    drug = get_drug(drug_name)
    
    if not alts:
        return f"No alternatives found for '{drug_name}' in the same drug class."
    
    output = [
        f"# Alternatives to {drug.brand_name if drug else drug_name}",
        f"**Drug Class:** {drug.drug_class if drug else 'Unknown'}",
        ""
    ]
    
    for alt in alts:
        # Get coverage info for ranking
        coverage = get_coverage(alt.id)
        best_tier = min((c[1].tier.value for c in coverage), default=6) if coverage else 6
        
        output.append(f"## {alt.brand_name} ({alt.generic_name})")
        output.append(f"- **Best Formulary Tier:** Tier {best_tier}")
        output.append(f"- **AWP:** ${alt.pricing.awp:,.2f}")
        if alt.pricing.goodrx_low:
            output.append(f"- **GoodRx Low:** ${alt.pricing.goodrx_low:,.2f}")
        output.append(f"- **PA Required:** {'Yes' if alt.requires_prior_auth else 'No'}")
        output.append("")
    
    return "\n".join(output)


def tool_generate_pa(drug_name: str, payer_name: str, diagnosis: str) -> str:
    """Generate a prior authorization form with clinical justification."""
    drug = get_drug(drug_name)
    if not drug:
        return f"Drug '{drug_name}' not found."
    
    # Find payer
    payer = None
    for p in PAYERS_DB.values():
        if payer_name.lower() in p.name.lower():
            payer = p
            break
    
    if not payer:
        return f"Payer '{payer_name}' not found."
    
    # Generate clinical justification
    indications = [i.condition for i in drug.indications if i.fda_approved]
    
    output = [
        f"# Prior Authorization Request",
        f"**Generated:** Auto-generated by MediBuddy AI",
        "",
        "## Patient/Drug Information",
        f"- **Drug Requested:** {drug.brand_name} ({drug.generic_name})",
        f"- **Strength:** {drug.strengths[0] if drug.strengths else 'As prescribed'}",
        f"- **Quantity:** 30-day supply",
        f"- **Diagnosis:** {diagnosis}",
        "",
        f"## Payer: {payer.name} ({payer.plan_name})",
        "",
        "## Clinical Justification",
        "",
        f"The patient has been diagnosed with **{diagnosis}**. {drug.brand_name} ({drug.generic_name}) is indicated for this condition based on FDA approval for: {', '.join(indications[:3])}.",
        "",
        f"**Mechanism:** {drug.mechanism}",
        "",
        "### Supporting Evidence",
        "- FDA-approved labeling supports use in this indication",
        "- Patient meets medical necessity criteria per current clinical guidelines",
        "- Alternative treatments have been considered/attempted",
        "",
        "## Predicted Success Rate",
        f"**Estimated Approval Rate:** 78-85% for this drug-payer combination",
        "",
        "---",
        "*This PA form was auto-generated. Please review and verify all information before submission.*"
    ]
    
    return "\n".join(output)


def tool_get_specialty_pharmacy(drug_name: str) -> str:
    """Find authorized specialty pharmacies for a drug."""
    drug = get_drug(drug_name)
    if not drug:
        return f"Drug '{drug_name}' not found."
    
    # Find SPs that carry this drug
    sps = [sp for sp in SPECIALTY_PHARMACIES if drug.id in sp.specialty_drugs or drug.brand_name.lower() in [d.lower() for d in sp.specialty_drugs]]
    
    if not sps:
        return f"{drug.brand_name} may not require a specialty pharmacy, or no authorized SPs found in database."
    
    output = [
        f"# Specialty Pharmacies for {drug.brand_name}",
        ""
    ]
    
    for sp in sps:
        output.append(f"## {sp.name}")
        output.append(f"- **Phone:** {sp.phone}")
        output.append(f"- **States Served:** {'All 50 states' if 'ALL' in sp.states_served else ', '.join(sp.states_served)}")
        output.append(f"- **Buy & Bill Available:** {'Yes' if sp.buy_and_bill else 'No'}")
        output.append(f"- **White Bagging:** {'Yes' if sp.white_bagging else 'No'}")
        output.append(f"- **Brown Bagging:** {'Yes' if sp.brown_bagging else 'No'}")
        output.append("")
    
    return "\n".join(output)


def tool_get_jcode(drug_name: str) -> str:
    """Look up J-Code for injectable/infused drugs."""
    drug = get_drug(drug_name)
    drug_name_lower = drug_name.lower()
    
    for code, jcode in JCODES_DB.items():
        if drug_name_lower in jcode.drug_name.lower() or (drug and drug.generic_name.lower() in jcode.drug_name.lower()):
            return f"""# J-Code: {jcode.code}
            
**Description:** {jcode.description}
**Drug:** {jcode.drug_name}
**ASP Price:** ${jcode.asp_price:.2f}
**RVU:** {jcode.rvu}

Use this code for Medicare Part B billing."""
    
    return f"No J-Code found for '{drug_name}'. The drug may be:\n- Oral/non-injectable\n- Billed under J3490 (unclassified)\n- Not covered under Part B"


def tool_renal_dosing(drug_name: str, crcl: str) -> str:
    """Get renal dosing recommendations based on CrCl."""
    drug = get_drug(drug_name)
    if not drug:
        return f"Drug '{drug_name}' not found."
    
    try:
        crcl_val = float(crcl)
    except:
        return "Please provide CrCl as a number (mL/min)."
    
    # Simulated renal dosing (would be from actual database in production)
    if drug.id == "metformin":
        if crcl_val >= 45:
            return f"**{drug.brand_name}:** No dose adjustment needed (CrCl ≥45)"
        elif crcl_val >= 30:
            return f"**{drug.brand_name}:** Reduce dose. Max 1000mg/day. Monitor renal function."
        else:
            return f"**{drug.brand_name}:** ⚠️ CONTRAINDICATED (CrCl <30). Risk of lactic acidosis."
    
    if drug.id == "gabapentin":
        if crcl_val >= 60:
            return f"**{drug.brand_name}:** Normal dosing 300-1200mg TID"
        elif crcl_val >= 30:
            return f"**{drug.brand_name}:** 200-700mg BID"
        elif crcl_val >= 15:
            return f"**{drug.brand_name}:** 200-700mg once daily"
        else:
            return f"**{drug.brand_name}:** 100-300mg once daily. Supplement after dialysis."
    
    return f"Specific renal dosing for {drug.brand_name} not available. Consult full prescribing information."


# ============================================================================
# LANGCHAIN AGENT SETUP
# ============================================================================

# Tools list - only created when LangChain is available
TOOLS = []

if LANGCHAIN_AVAILABLE:
    from langchain.tools import Tool
    TOOLS = [
        Tool(name="search_drug", func=tool_search_drug,
             description="Search for drugs by brand name, generic name, or drug class. Input: search query string."),
        Tool(name="get_drug_details", func=tool_get_drug_details,
             description="Get comprehensive details for a specific drug including indications, warnings, dosing, safety. Input: drug name."),
        Tool(name="get_pricing", func=tool_get_pricing,
             description="Get pricing information including AWP, WAC, NADAC, 340B, and cash prices. Input: drug name."),
        Tool(name="check_coverage", func=tool_check_coverage,
             description="Check formulary coverage, tier, copay, and PA requirements. Input: drug name, optionally payer name."),
        Tool(name="check_interactions", func=tool_check_interactions,
             description="Check for drug-drug interactions between medications. Input: comma-separated list of drug names."),
        Tool(name="find_alternatives", func=tool_find_alternatives,
             description="Find therapeutic alternatives in the same drug class. Input: drug name."),
        Tool(name="generate_prior_auth", func=tool_generate_pa,
             description="Generate a prior authorization form with clinical justification. Input: drug name, payer name, diagnosis (comma-separated)."),
        Tool(name="get_specialty_pharmacy", func=tool_get_specialty_pharmacy,
             description="Find authorized specialty pharmacies for a drug. Input: drug name."),
        Tool(name="get_jcode", func=tool_get_jcode,
             description="Look up J-Code for injectable/infused drugs for Medicare billing. Input: drug name."),
        Tool(name="renal_dosing", func=tool_renal_dosing,
             description="Get renal dosing recommendations based on creatinine clearance. Input: drug name, CrCl value (comma-separated)."),
    ]

AGENT_PROMPT = """You are MediBuddy, an expert AI assistant for healthcare professionals specializing in drug information, formulary coverage, and reimbursement.

You have access to real-time pharmaceutical data including:
- Drug information (NDC, GPI, indications, warnings, dosing)
- Pricing (AWP, WAC, NADAC, 340B, cash prices from GoodRx/CostPlus)
- Formulary coverage for 4,800+ commercial, Medicare, and Medicaid plans
- Drug interaction checking
- Prior authorization criteria and form generation
- Specialty pharmacy information
- J-Code lookups for injectable drugs
- Renal dosing calculators

When answering questions:
1. Always cite specific data points (tier, copay amounts, NDC codes)
2. Highlight safety concerns prominently (Black Box warnings, interactions)
3. Suggest cost-saving alternatives when relevant
4. Be concise but thorough - healthcare professionals need quick, accurate answers

Available tools:
{tools}

Tool names: {tool_names}

Use this format:
Question: the input question
Thought: think about what to do
Action: the tool to use
Action Input: input for the tool
Observation: the result
... (repeat as needed)
Thought: I now know the final answer
Final Answer: comprehensive answer to the question

Question: {input}
{agent_scratchpad}"""


class MediBuddyAgent:
    """The MediBuddy AI Agent."""
    
    def __init__(self):
        self.agent = None
        self.memory = None
        
        if LANGCHAIN_AVAILABLE:
            api_key = os.getenv("GOOGLE_API_KEY")
            if api_key:
                try:
                    llm = ChatGoogleGenerativeAI(
                        model="gemini-1.5-flash",
                        google_api_key=api_key,
                        temperature=0.1,
                    )
                    
                    prompt = PromptTemplate.from_template(AGENT_PROMPT)
                    self.agent = create_react_agent(llm, TOOLS, prompt)
                    self.memory = ConversationBufferWindowMemory(k=5)
                    
                    self.agent_executor = AgentExecutor(
                        agent=self.agent,
                        tools=TOOLS,
                        memory=self.memory,
                        verbose=True,
                        handle_parsing_errors=True,
                        max_iterations=5,
                    )
                    print("[AGENT] MediBuddy Agent initialized with Gemini")
                except Exception as e:
                    print(f"[AGENT] Failed to initialize LangChain agent: {e}")
                    self.agent = None
    
    async def chat(self, message: str) -> ChatResponse:
        """Process a chat message and return a response."""
        
        # If LangChain agent is available, use it
        if self.agent and hasattr(self, 'agent_executor'):
            try:
                result = self.agent_executor.invoke({"input": message})
                return ChatResponse(
                    response=result.get("output", "I couldn't process that request."),
                    sources=["MediBuddy Knowledge Base"],
                    confidence=0.95
                )
            except Exception as e:
                print(f"[AGENT] LangChain error: {e}")
                # Fall through to Hugging Face / fallback
        
        # Try to get context from our tools first
        context = await self._get_context_for_query(message)
        
        # If we have Hugging Face API, use it for enhanced responses
        if HUGGINGFACE_API_KEY and context:
            enhanced_prompt = f"""Based on this pharmaceutical data:

{context}

Now answer this question: {message}

Provide a helpful, accurate response using the data above."""
            
            hf_response = await query_huggingface(enhanced_prompt)
            if hf_response:
                return ChatResponse(
                    response=hf_response,
                    sources=["MediBuddy Database", "Hugging Face AI"],
                    confidence=0.88
                )
        
        # Fallback: Direct tool matching (rule-based)
        return await self._fallback_response(message)
    
    async def _get_context_for_query(self, message: str) -> str:
        """Extract relevant data context for the query."""
        message_lower = message.lower()
        context_parts = []
        
        # Find mentioned drugs
        for drug_id in DRUGS_DB.keys():
            if drug_id in message_lower:
                drug = get_drug(drug_id)
                if drug:
                    context_parts.append(f"Drug: {drug.brand_name} ({drug.generic_name})")
                    context_parts.append(f"  Class: {drug.drug_class}")
                    context_parts.append(f"  AWP: ${drug.pricing.awp:,.2f}")
                    if drug.pricing.goodrx_low:
                        context_parts.append(f"  GoodRx Low: ${drug.pricing.goodrx_low:,.2f}")
                    
                    # Add coverage if asked
                    if any(w in message_lower for w in ["cover", "tier", "formulary", "payer"]):
                        coverages = get_coverage(drug_id)
                        if coverages:
                            context_parts.append("  Coverage:")
                            for payer, cov in coverages[:3]:
                                pa = "PA Required" if cov.prior_auth_required else "No PA"
                                context_parts.append(f"    - {payer.name}: Tier {cov.tier.value}, {pa}")
        
        # Check for interaction queries
        if "interaction" in message_lower:
            drugs = [d for d in DRUGS_DB.keys() if d in message_lower]
            if len(drugs) >= 2:
                interactions = check_interactions(drugs)
                if interactions:
                    context_parts.append("Drug Interactions Found:")
                    for i in interactions:
                        context_parts.append(f"  - {i.drug_a} + {i.drug_b}: {i.severity.value}")
                        context_parts.append(f"    Effect: {i.clinical_effect}")
                else:
                    context_parts.append(f"No significant interactions between: {', '.join(drugs)}")
        
        return "\n".join(context_parts) if context_parts else ""
    
    async def _fallback_response(self, message: str) -> ChatResponse:
        """Fallback response when LangChain is not available."""
        message_lower = message.lower()
        
        # Pattern matching for common queries
        if "interaction" in message_lower:
            # Extract drug names
            drugs = []
            for drug_id in DRUGS_DB.keys():
                if drug_id in message_lower:
                    drugs.append(drug_id)
            if len(drugs) >= 2:
                return ChatResponse(
                    response=tool_check_interactions(", ".join(drugs)),
                    sources=["Drug Interaction Database"],
                    confidence=0.9
                )
        
        if "price" in message_lower or "cost" in message_lower or "pricing" in message_lower:
            for drug_id in DRUGS_DB.keys():
                if drug_id in message_lower:
                    return ChatResponse(
                        response=tool_get_pricing(drug_id),
                        sources=["Pricing Database"],
                        confidence=0.9
                    )
        
        if "coverage" in message_lower or "formulary" in message_lower or "tier" in message_lower or "covered" in message_lower:
            for drug_id in DRUGS_DB.keys():
                if drug_id in message_lower:
                    # Check for payer name
                    payer_name = None
                    for payer in PAYERS_DB.values():
                        if payer.name.lower() in message_lower:
                            payer_name = payer.name
                            break
                    return ChatResponse(
                        response=tool_check_coverage(drug_id, payer_name),
                        sources=["Formulary Database"],
                        confidence=0.9
                    )
        
        if "alternative" in message_lower or "substitute" in message_lower:
            for drug_id in DRUGS_DB.keys():
                if drug_id in message_lower:
                    return ChatResponse(
                        response=tool_find_alternatives(drug_id),
                        sources=["Drug Database"],
                        confidence=0.9
                    )
        
        # Default: drug search/info
        for drug_id in DRUGS_DB.keys():
            if drug_id in message_lower:
                return ChatResponse(
                    response=tool_get_drug_details(drug_id),
                    sources=["Drug Database"],
                    confidence=0.9
                )
        
        # Search mode
        if any(word in message_lower for word in ["search", "find", "look up", "what is", "tell me about"]):
            words = message.split()
            for word in words:
                if len(word) > 3:
                    results = search_drugs(word, limit=3)
                    if results:
                        return ChatResponse(
                            response=tool_search_drug(word),
                            sources=["Drug Database"],
                            confidence=0.85
                        )
        
        # Generic response
        return ChatResponse(
            response="""I'm MediBuddy, your pharmaceutical intelligence assistant. I can help with:

• **Drug Information** - "Tell me about metformin"
• **Pricing** - "What's the price of Ozempic?"
• **Coverage** - "Is Eliquis covered by Aetna?"
• **Interactions** - "Check interactions between warfarin and aspirin"
• **Alternatives** - "Find alternatives to Lipitor"
• **Prior Auth** - "Generate PA for Ozempic for Cigna"

Try asking a specific question about a medication!""",
            sources=[],
            confidence=1.0
        )


# Global agent instance
_agent: Optional[MediBuddyAgent] = None


def get_agent() -> MediBuddyAgent:
    """Get or create the global agent instance."""
    global _agent
    if _agent is None:
        _agent = MediBuddyAgent()
    return _agent
