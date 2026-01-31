"""
MediBuddy - Real-Time Pharmaceutical Intelligence Engine
The 5-Layer Pharma Brain that never sleeps.
"""

import asyncio
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, field
from enum import Enum
import json
import hashlib


# ============================================================================
# LAYER 3: ATOMIC KNOWLEDGE GRAPH
# ============================================================================

class ChangeImportance(int, Enum):
    """Importance scoring for pharmaceutical changes (1-10 scale)"""
    TRIVIAL = 1          # Minor formatting change
    LOW = 2              # Copay change < $5
    MINOR = 3            # Small quantity limit change
    MODERATE = 4         # PA criteria minor update
    NOTABLE = 5          # New preferred alternative added
    SIGNIFICANT = 6      # Step therapy change
    HIGH = 7             # PA required/removed
    MAJOR = 8            # Tier change (e.g., 3→2)
    CRITICAL = 9         # New PA criteria, major coverage change
    URGENT = 10          # Drug removed from formulary, black box warning, shortage


@dataclass
class AtomicFact:
    """Single atomic fact in the knowledge graph with full provenance."""
    id: str
    entity_type: str       # "drug", "payer", "coverage", "price", "interaction"
    entity_id: str         # e.g., "ozempic", "aetna_comm"
    field: str             # e.g., "formulary_tier", "awp", "pa_required"
    value: Any
    previous_value: Optional[Any] = None
    source: str = ""       # e.g., "FDA API", "UHC Provider Portal PDF page 47"
    source_url: Optional[str] = None
    confidence: float = 1.0
    verified_by: Optional[str] = None  # e.g., "AI + Dr. Sarah Kim"
    effective_date: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    importance: ChangeImportance = ChangeImportance.MODERATE
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            "field": self.field,
            "value": self.value,
            "previous_value": self.previous_value,
            "source": self.source,
            "confidence": self.confidence,
            "verified_by": self.verified_by,
            "effective_date": self.effective_date.isoformat() if self.effective_date else None,
            "updated_at": self.updated_at.isoformat(),
            "importance": self.importance.value,
        }


class KnowledgeGraph:
    """Atomic Knowledge Graph - The Single Source of Truth"""
    
    def __init__(self):
        self.facts: Dict[str, AtomicFact] = {}
        self.change_history: List[AtomicFact] = []
        self.subscribers: List[Callable] = []
    
    def _generate_fact_id(self, entity_type: str, entity_id: str, field: str) -> str:
        """Generate unique fact ID."""
        key = f"{entity_type}:{entity_id}:{field}"
        return hashlib.md5(key.encode()).hexdigest()[:12]
    
    async def upsert_fact(self, fact: AtomicFact) -> bool:
        """Insert or update a fact. Returns True if changed."""
        fact_key = f"{fact.entity_type}:{fact.entity_id}:{fact.field}"
        
        if fact_key in self.facts:
            existing = self.facts[fact_key]
            if existing.value == fact.value:
                return False  # No real change (Layer 2 validation)
            
            # Record the change
            fact.previous_value = existing.value
            self.change_history.append(fact)
        
        fact.updated_at = datetime.now()
        self.facts[fact_key] = fact
        
        # Notify all subscribers (Layer 4: Real-Time Push)
        await self._notify_subscribers(fact)
        
        return True
    
    def get_fact(self, entity_type: str, entity_id: str, field: str) -> Optional[AtomicFact]:
        """Retrieve a specific fact."""
        fact_key = f"{entity_type}:{entity_id}:{field}"
        return self.facts.get(fact_key)
    
    def get_entity_facts(self, entity_type: str, entity_id: str) -> List[AtomicFact]:
        """Get all facts for an entity."""
        prefix = f"{entity_type}:{entity_id}:"
        return [f for k, f in self.facts.items() if k.startswith(prefix)]
    
    def get_recent_changes(self, hours: int = 24, min_importance: int = 5) -> List[AtomicFact]:
        """Get recent high-importance changes."""
        cutoff = datetime.now() - timedelta(hours=hours)
        return [
            f for f in self.change_history 
            if f.updated_at > cutoff and f.importance.value >= min_importance
        ]
    
    def subscribe(self, callback: Callable):
        """Subscribe to real-time updates."""
        self.subscribers.append(callback)
    
    async def _notify_subscribers(self, fact: AtomicFact):
        """Push updates to all subscribers."""
        for callback in self.subscribers:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(fact)
                else:
                    callback(fact)
            except Exception as e:
                print(f"Subscriber notification failed: {e}")


# ============================================================================
# LAYER 1: GLOBAL PHARMA FIREHOSE (Simulated)
# ============================================================================

@dataclass
class DataSource:
    """Configuration for a pharmaceutical data source."""
    id: str
    name: str
    source_type: str  # "api", "scraper", "feed", "portal"
    update_frequency: str  # "realtime", "hourly", "daily", "weekly"
    enabled: bool = True
    last_check: Optional[datetime] = None
    last_update: Optional[datetime] = None
    records_processed: int = 0


class PharmaFirehose:
    """
    Layer 1: Global Pharma Firehose
    Monitors 40,000+ sources in real-time (simulated for demo).
    """
    
    SOURCES = [
        DataSource("fda_orange_book", "FDA Orange Book", "api", "daily"),
        DataSource("fda_ndc", "FDA NDC Directory", "api", "daily"),
        DataSource("fda_labels", "FDA Drug Labels", "api", "realtime"),
        DataSource("cms_nadac", "CMS NADAC", "sftp", "weekly"),
        DataSource("cms_asp", "CMS ASP Drug Pricing", "api", "quarterly"),
        DataSource("cms_340b", "340B Ceiling Prices", "api", "daily"),
        DataSource("goodrx", "GoodRx Prices", "scraper", "5min"),
        DataSource("costplus", "Cost Plus Drugs", "scraper", "5min"),
        DataSource("amazon_pharmacy", "Amazon Pharmacy", "scraper", "5min"),
        DataSource("clinicaltrials", "ClinicalTrials.gov", "api", "hourly"),
        DataSource("pubmed", "PubMed/NCBI", "api", "hourly"),
        DataSource("ema", "European Medicines Agency", "api", "daily"),
        DataSource("health_canada", "Health Canada", "api", "daily"),
        # Payer portals (simulated - would have 4,800+ in production)
        DataSource("aetna_portal", "Aetna Formulary Portal", "portal", "daily"),
        DataSource("bcbs_portal", "BCBS Formulary Portal", "portal", "daily"),
        DataSource("uhc_portal", "UnitedHealthcare Portal", "portal", "daily"),
        DataSource("cigna_portal", "Cigna Formulary Portal", "portal", "daily"),
        DataSource("humana_portal", "Humana Medicare Portal", "portal", "daily"),
        # Medicaid (simulated - would have all 50 states)
        DataSource("medicaid_tx", "Texas Medicaid Portal", "portal", "daily"),
        DataSource("medicaid_ca", "Medi-Cal Portal", "portal", "daily"),
        DataSource("medicaid_ny", "NY Medicaid Portal", "portal", "daily"),
        DataSource("medicaid_fl", "Florida Medicaid Portal", "portal", "daily"),
    ]
    
    def __init__(self, knowledge_graph: KnowledgeGraph):
        self.kg = knowledge_graph
        self.sources = {s.id: s for s in self.SOURCES}
        self.running = False
        self._update_queue: asyncio.Queue = asyncio.Queue()
    
    async def start(self):
        """Start the firehose ingestion."""
        self.running = True
        asyncio.create_task(self._simulation_loop())
    
    async def stop(self):
        """Stop the firehose."""
        self.running = False
    
    async def _simulation_loop(self):
        """Simulate real-time data updates for demo purposes."""
        
        # Simulated updates that could happen
        possible_updates = [
            # Tier changes
            ("coverage", "ozempic:aetna_comm", "formulary_tier", 2, "Tier 3 → Tier 2", ChangeImportance.MAJOR, "Aetna Provider Portal"),
            ("coverage", "jardiance:united_comm", "formulary_tier", 1, "Tier 2 → Tier 1", ChangeImportance.MAJOR, "UHC Formulary Update"),
            
            # PA changes
            ("coverage", "ozempic:cigna_comm", "pa_required", False, "PA Removed!", ChangeImportance.HIGH, "Cigna Policy Update"),
            ("coverage", "wegovy:bcbs_comm", "pa_required", True, "PA Now Required", ChangeImportance.HIGH, "BCBS Policy Alert"),
            
            # Price changes
            ("price", "ozempic", "goodrx_low", 842.00, "Price dropped $50", ChangeImportance.NOTABLE, "GoodRx Scraper"),
            ("price", "humira", "costplus_price", 1250.00, "Cost Plus now carries Humira", ChangeImportance.SIGNIFICANT, "CostPlus API"),
            ("price", "eliquis", "nadac", 485.50, "NADAC updated", ChangeImportance.MODERATE, "CMS NADAC Feed"),
            
            # New warnings
            ("drug", "semaglutide", "new_warning", "Thyroid monitoring recommended", "New Safety Alert", ChangeImportance.CRITICAL, "FDA MedWatch"),
            
            # Shortage alerts
            ("drug", "amoxicillin", "shortage_status", "Limited Supply", "Shortage Alert!", ChangeImportance.URGENT, "FDA Drug Shortages"),
            
            # Copay changes
            ("coverage", "metformin:humana_ma", "copay", 0, "Copay reduced to $0", ChangeImportance.NOTABLE, "Humana Formulary"),
        ]
        
        while self.running:
            # Random delay between 10-60 seconds for demo
            await asyncio.sleep(random.uniform(10, 60))
            
            if not self.running:
                break
            
            # Pick a random update
            update = random.choice(possible_updates)
            entity_type, entity_id, field, value, description, importance, source = update
            
            # Create atomic fact
            fact = AtomicFact(
                id=self.kg._generate_fact_id(entity_type, entity_id, field),
                entity_type=entity_type,
                entity_id=entity_id,
                field=field,
                value=value,
                source=source,
                confidence=0.95 + random.uniform(0, 0.05),
                verified_by="AI Validation Engine",
                effective_date=datetime.now(),
                importance=importance,
            )
            
            # Push to knowledge graph
            changed = await self.kg.upsert_fact(fact)
            
            if changed:
                print(f"[FIREHOSE] {description} | Source: {source} | Importance: {importance.value}/10")


# ============================================================================
# LAYER 2: AI CHANGE DETECTION & VALIDATION ENGINE
# ============================================================================

class ChangeValidator:
    """
    Layer 2: AI Change Detection & Validation
    Triple-validation pipeline: LLM + Rules + Human-in-loop
    """
    
    def __init__(self):
        self.pending_validation: List[AtomicFact] = []
    
    async def validate(self, fact: AtomicFact) -> tuple[bool, float, str]:
        """
        Validate a change. Returns (is_valid, confidence, reason).
        """
        # Rule-based validation
        rule_result = await self._apply_rules(fact)
        
        # LLM validation (simulated)
        llm_result = await self._llm_validate(fact)
        
        # Combine scores
        combined_confidence = (rule_result[1] * 0.4 + llm_result[1] * 0.6)
        
        # High-importance changes need human verification
        if fact.importance.value >= 8:
            return (True, combined_confidence * 0.95, "Pending pharmacist verification")
        
        return (True, combined_confidence, "Auto-validated")
    
    async def _apply_rules(self, fact: AtomicFact) -> tuple[bool, float]:
        """Apply rule-based validation."""
        # Check for duplicate/fake changes
        if fact.value == fact.previous_value:
            return (False, 0.0)  # Not a real change
        
        # Basic sanity checks
        if fact.entity_type == "price" and isinstance(fact.value, (int, float)):
            if fact.value < 0:
                return (False, 0.0)
            if fact.value > 100000:  # Sanity check for drug price
                return (True, 0.7)  # Might be valid for specialty drugs
        
        return (True, 0.9)
    
    async def _llm_validate(self, fact: AtomicFact) -> tuple[bool, float]:
        """LLM-based validation (simulated for demo)."""
        # In production, this would call the LLM to verify the change makes sense
        await asyncio.sleep(0.1)  # Simulate API call
        return (True, 0.92)
    
    def score_importance(self, fact: AtomicFact) -> ChangeImportance:
        """Score the importance of a change."""
        if "tier" in fact.field.lower() and fact.previous_value != fact.value:
            return ChangeImportance.MAJOR
        if "pa_required" in fact.field.lower():
            return ChangeImportance.HIGH
        if "shortage" in fact.field.lower():
            return ChangeImportance.URGENT
        if "warning" in fact.field.lower():
            return ChangeImportance.CRITICAL
        if "copay" in fact.field.lower():
            diff = abs((fact.value or 0) - (fact.previous_value or 0))
            if diff >= 20:
                return ChangeImportance.SIGNIFICANT
            elif diff >= 5:
                return ChangeImportance.MODERATE
            return ChangeImportance.LOW
        
        return ChangeImportance.MODERATE


# ============================================================================
# LAYER 5: AUTONOMOUS UPDATE AGENTS
# ============================================================================

class AutonomousAgent:
    """Base class for autonomous monitoring agents."""
    
    def __init__(self, name: str, kg: KnowledgeGraph):
        self.name = name
        self.kg = kg
        self.running = False
        self.stats = {"checks": 0, "updates_found": 0}
    
    async def start(self):
        self.running = True
        asyncio.create_task(self._run_loop())
    
    async def stop(self):
        self.running = False
    
    async def _run_loop(self):
        """Override in subclasses."""
        pass


class PACriteriaWatcher(AutonomousAgent):
    """Watches for PA criteria changes across all payers."""
    
    async def _run_loop(self):
        while self.running:
            await asyncio.sleep(3600)  # Check hourly
            self.stats["checks"] += 1
            # In production: Download and parse payer policy PDFs with multimodal LLM


class PriceHunter(AutonomousAgent):
    """Hunts for best cash prices across platforms."""
    
    async def _run_loop(self):
        while self.running:
            await asyncio.sleep(300)  # Check every 5 minutes
            self.stats["checks"] += 1
            # In production: Query GoodRx, CostPlus, Amazon, etc.


class ShortageMonitor(AutonomousAgent):
    """Monitors FDA, ASHP, and wholesalers for shortage alerts."""
    
    async def _run_loop(self):
        while self.running:
            await asyncio.sleep(1800)  # Check every 30 minutes
            self.stats["checks"] += 1
            # In production: Check FDA Drug Shortages database, ASHP


class LabelWatcher(AutonomousAgent):
    """Monitors FDA for new/updated drug labels."""
    
    async def _run_loop(self):
        while self.running:
            await asyncio.sleep(3600)  # Check hourly
            self.stats["checks"] += 1
            # In production: Download new FDA labels, extract warnings with LLM


class MedicaidSpider(AutonomousAgent):
    """Crawls all 50 state Medicaid portals."""
    
    async def _run_loop(self):
        while self.running:
            await asyncio.sleep(86400)  # Check daily
            self.stats["checks"] += 1
            # In production: Log into each state portal with RPA


# ============================================================================
# UNIFIED PHARMA BRAIN
# ============================================================================

class PharmaBrain:
    """
    The unified Real-Time Pharmaceutical Intelligence Engine.
    Combines all 5 layers into a single cohesive system.
    """
    
    def __init__(self):
        # Layer 3: Knowledge Graph
        self.knowledge_graph = KnowledgeGraph()
        
        # Layer 2: Validator
        self.validator = ChangeValidator()
        
        # Layer 1: Firehose
        self.firehose = PharmaFirehose(self.knowledge_graph)
        
        # Layer 5: Autonomous Agents
        self.agents = [
            PACriteriaWatcher("PA Criteria Watcher", self.knowledge_graph),
            PriceHunter("Price Hunter", self.knowledge_graph),
            ShortageMonitor("Shortage Stalker", self.knowledge_graph),
            LabelWatcher("Label Ninja", self.knowledge_graph),
            MedicaidSpider("Medicaid Spider", self.knowledge_graph),
        ]
        
        # Layer 4: WebSocket connections for real-time push
        self.websocket_clients: List[Any] = []
        
        self.running = False
    
    async def start(self):
        """Start the Pharma Brain."""
        self.running = True
        
        # Start firehose
        await self.firehose.start()
        
        # Start autonomous agents
        for agent in self.agents:
            await agent.start()
        
        print("[PHARMA BRAIN] 🧠 Real-Time Pharmaceutical Intelligence Engine ONLINE")
        print(f"[PHARMA BRAIN] Monitoring {len(self.firehose.sources)} data sources")
        print(f"[PHARMA BRAIN] {len(self.agents)} autonomous agents deployed")
    
    async def stop(self):
        """Stop the Pharma Brain."""
        self.running = False
        await self.firehose.stop()
        for agent in self.agents:
            await agent.stop()
        print("[PHARMA BRAIN] Shutting down...")
    
    def subscribe_websocket(self, ws):
        """Subscribe a WebSocket client to real-time updates."""
        self.websocket_clients.append(ws)
        
        async def push_to_ws(fact: AtomicFact):
            try:
                await ws.send_json({
                    "type": "pharma_update",
                    "data": fact.to_dict()
                })
            except:
                if ws in self.websocket_clients:
                    self.websocket_clients.remove(ws)
        
        self.knowledge_graph.subscribe(push_to_ws)
    
    def get_system_status(self) -> dict:
        """Get current system status."""
        return {
            "status": "online" if self.running else "offline",
            "knowledge_graph": {
                "total_facts": len(self.knowledge_graph.facts),
                "recent_changes_24h": len(self.knowledge_graph.get_recent_changes(24, 1)),
            },
            "firehose": {
                "sources_active": len([s for s in self.firehose.sources.values() if s.enabled]),
            },
            "agents": [
                {"name": a.name, "checks": a.stats["checks"], "updates": a.stats["updates_found"]}
                for a in self.agents
            ],
            "websocket_clients": len(self.websocket_clients),
        }


# Global instance
pharma_brain: Optional[PharmaBrain] = None


async def get_pharma_brain() -> PharmaBrain:
    """Get or create the global Pharma Brain instance."""
    global pharma_brain
    if pharma_brain is None:
        pharma_brain = PharmaBrain()
        await pharma_brain.start()
    return pharma_brain
