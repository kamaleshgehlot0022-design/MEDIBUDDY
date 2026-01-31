"""
MediBuddy - FastAPI Main Application
Enterprise Healthcare Agent with Real-Time Pharmaceutical Intelligence.
"""

import os
import asyncio
from contextlib import asynccontextmanager
from typing import List, Optional
from datetime import datetime

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Local imports
from models import (
    ChatRequest, ChatResponse, 
    InteractionCheckRequest, InteractionCheckResponse,
    CoverageRequest, CoverageResponse,
    PriorAuthRequest, DrugSearchRequest,
    Drug, DrugInteraction, CoverageDetails
)
from database import (
    DRUGS_DB, PAYERS_DB, search_drugs, get_drug, 
    check_interactions, get_coverage, get_alternatives
)
from agent import get_agent, tool_check_interactions, tool_get_pricing, tool_check_coverage
from realtime_engine import get_pharma_brain, PharmaBrain


# ============================================================================
# LIFESPAN & APP SETUP
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    print("=" * 60)
    print("🏥 MEDIBUDDY - Enterprise Healthcare Agent")
    print("=" * 60)
    
    # Start the Pharma Brain (real-time intelligence engine)
    brain = await get_pharma_brain()
    
    print(f"✅ Drug Database: {len(DRUGS_DB)} medications loaded")
    print(f"✅ Payer Database: {len(PAYERS_DB)} plans loaded")
    print(f"✅ AI Agent: Initialized")
    print(f"✅ Real-Time Engine: Online")
    print("=" * 60)
    print("🌐 Server running at http://localhost:8000")
    print("=" * 60)
    
    yield
    
    # Shutdown
    await brain.stop()
    print("👋 MediBuddy shutting down...")


app = FastAPI(
    title="MediBuddy",
    description="Intelligent Drug & Reimbursement Assistant for Healthcare Professionals",
    version="1.0.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# WEBSOCKET - REAL-TIME UPDATES (LAYER 4)
# ============================================================================

class ConnectionManager:
    """Manage WebSocket connections for real-time updates."""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        
        # Subscribe to Pharma Brain updates
        brain = await get_pharma_brain()
        brain.subscribe_websocket(websocket)
        
        # Send welcome message
        await websocket.send_json({
            "type": "connected",
            "message": "Connected to MediBuddy Real-Time Intelligence Engine",
            "timestamp": datetime.now().isoformat()
        })
    
    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
    
    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except:
                self.disconnect(connection)


manager = ConnectionManager()


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time pharmaceutical updates."""
    await manager.connect(websocket)
    try:
        while True:
            # Receive messages from client (for chat)
            data = await websocket.receive_json()
            
            if data.get("type") == "chat":
                # Process chat through agent
                agent = get_agent()
                response = await agent.chat(data.get("message", ""))
                
                await websocket.send_json({
                    "type": "chat_response",
                    "response": response.response,
                    "sources": response.sources,
                    "confidence": response.confidence,
                    "timestamp": datetime.now().isoformat()
                })
            
            elif data.get("type") == "subscribe":
                # Subscribe to specific drug/payer updates
                await websocket.send_json({
                    "type": "subscribed",
                    "entity": data.get("entity"),
                    "timestamp": datetime.now().isoformat()
                })
    
    except WebSocketDisconnect:
        manager.disconnect(websocket)


# ============================================================================
# REST API ENDPOINTS
# ============================================================================

# --- Chat / AI Agent ---

@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Chat with MediBuddy AI agent."""
    agent = get_agent()
    response = await agent.chat(request.message)
    return response


# --- Drug Information ---

@app.get("/api/drugs", response_model=List[dict])
async def list_drugs(
    search: Optional[str] = Query(None, description="Search query"),
    limit: int = Query(20, le=100)
):
    """List or search drugs."""
    if search:
        results = search_drugs(search, limit=limit)
    else:
        results = list(DRUGS_DB.values())[:limit]
    
    return [
        {
            "id": d.id,
            "brand_name": d.brand_name,
            "generic_name": d.generic_name,
            "drug_class": d.drug_class,
            "schedule": d.schedule.value,
            "has_black_box": any(w.type == "Black Box" for w in d.warnings)
        }
        for d in results
    ]


@app.get("/api/drugs/{drug_name}")
async def get_drug_info(drug_name: str):
    """Get detailed drug information."""
    drug = get_drug(drug_name)
    if not drug:
        raise HTTPException(status_code=404, detail=f"Drug '{drug_name}' not found")
    
    return {
        "drug": drug.model_dump(),
        "alternatives": [
            {"id": a.id, "brand_name": a.brand_name, "generic_name": a.generic_name}
            for a in get_alternatives(drug_name)[:5]
        ]
    }


@app.get("/api/drugs/{drug_name}/pricing")
async def get_drug_pricing(
    drug_name: str,
    location: Optional[str] = Query(None, description="Location code (State or Country, e.g., NY, UK, CA, IN)")
):
    """Get pricing information for a drug, adjusted by geological location (State or Country)."""
    drug = get_drug(drug_name)
    if not drug:
        raise HTTPException(status_code=404, detail=f"Drug '{drug_name}' not found")
    
    pricing = drug.pricing.model_dump()
    
    # Base currency
    currency = "USD"
    symbol = "$"
    
    # Geological/Location-based adjustments
    if location:
        location = location.upper().strip()
        
        # International Country Data
        countries = {
            "UK": {"mult": 0.45, "curr": "GBP", "sym": "£", "name": "United Kingdom (NHS)"},
            "IN": {"mult": 0.12, "curr": "INR", "sym": "₹", "name": "India (Local Generic)"},
            "CA": {"mult": 0.65, "curr": "CAD", "sym": "CA$", "name": "Canada (Public)"},
            "DE": {"mult": 0.55, "curr": "EUR", "sym": "€", "name": "Germany (GKV)"},
            "AU": {"mult": 0.60, "curr": "AUD", "sym": "A$", "name": "Australia (PBS)"},
            "AE": {"mult": 1.10, "curr": "AED", "sym": "dh", "name": "United Arab Emirates"},
        }
        
        # US State Data
        states = {
            "NY": 1.15, "CA": 1.18, "WA": 1.10, "MA": 1.12, "NJ": 1.14,
            "TX": 1.00, "FL": 0.98, "IL": 1.02, "GA": 0.97, "PA": 0.99,
            "AL": 0.88, "MS": 0.85, "KY": 0.90, "WV": 0.87, "AR": 0.89
        }
        
        if location in countries:
            c_data = countries[location]
            multiplier = c_data["mult"]
            currency = c_data["curr"]
            symbol = c_data["sym"]
            location_name = c_data["name"]
        else:
            multiplier = states.get(location, 1.0)
            location_name = f"United States ({location})" if location in states else location
        
        # Adjust all price points
        for key in ["awp", "wac", "nadac", "asp", "price_340b", "goodrx_low", "costplus_price"]:
            if pricing.get(key) is not None:
                pricing[key] = round(pricing[key] * multiplier, 2)
        
        pricing["location_adjustment"] = {
            "name": location_name,
            "code": location,
            "multiplier": multiplier,
            "currency": currency,
            "symbol": symbol
        }
    
    return {
        "drug_name": drug.brand_name,
        "generic_name": drug.generic_name,
        "location": location,
        "pricing": pricing
    }


# --- Drug Interactions ---

@app.post("/api/interactions/check")
async def check_drug_interactions(request: InteractionCheckRequest):
    """Check for drug-drug interactions."""
    if len(request.drugs) < 2:
        raise HTTPException(status_code=400, detail="At least 2 drugs required")
    
    interactions = check_interactions(request.drugs)
    
    return InteractionCheckResponse(
        interactions=interactions,
        has_major_interaction=any(i.severity.value == "Major" for i in interactions),
        summary=f"Found {len(interactions)} interaction(s) between {len(request.drugs)} drugs"
    )


# --- Coverage / Formulary ---

@app.get("/api/coverage/{drug_name}")
async def get_drug_coverage(
    drug_name: str,
    payer: Optional[str] = Query(None, description="Filter by payer name")
):
    """Get formulary coverage for a drug."""
    coverages = get_coverage(drug_name, payer_name=payer)
    
    if not coverages:
        raise HTTPException(status_code=404, detail=f"No coverage found for '{drug_name}'")
    
    return [
        {
            "payer": {
                "id": p.id,
                "name": p.name,
                "type": p.type.value,
                "plan_name": p.plan_name,
                "state": p.state
            },
            "coverage": c.model_dump()
        }
        for p, c in coverages
    ]


@app.get("/api/payers")
async def list_payers():
    """List all payers."""
    return [
        {
            "id": p.id,
            "name": p.name,
            "type": p.type.value,
            "plan_name": p.plan_name,
            "state": p.state,
            "drugs_covered": len(p.covered_drugs)
        }
        for p in PAYERS_DB.values()
    ]


# --- Prior Authorization ---

@app.post("/api/prior-auth/generate")
async def generate_prior_auth(request: PriorAuthRequest):
    """Generate a prior authorization form."""
    from agent import tool_generate_pa
    
    result = tool_generate_pa(
        request.drug_name,
        request.payer_name,
        request.diagnosis
    )
    
    return {
        "form": result,
        "generated_at": datetime.now().isoformat()
    }


# --- System Status ---

@app.get("/api/status")
async def get_status():
    """Get system status including real-time engine stats."""
    brain = await get_pharma_brain()
    return {
        "status": "online",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat(),
        "database": {
            "drugs": len(DRUGS_DB),
            "payers": len(PAYERS_DB)
        },
        "realtime_engine": brain.get_system_status()
    }


@app.get("/api/updates/recent")
async def get_recent_updates(hours: int = Query(24, le=168)):
    """Get recent pharmaceutical updates from the real-time engine."""
    brain = await get_pharma_brain()
    changes = brain.knowledge_graph.get_recent_changes(hours=hours, min_importance=3)
    
    return {
        "count": len(changes),
        "hours": hours,
        "updates": [c.to_dict() for c in changes[:50]]
    }


# ============================================================================
# STATIC FILES & FRONTEND
# ============================================================================

# Create static directory if it doesn't exist
import os
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
static_dir = os.path.join(BASE_DIR, "static")
os.makedirs(static_dir, exist_ok=True)

# Mount static files
app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the main application."""
    index_path = os.path.join(static_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    
    # Fallback if index.html doesn't exist yet
    return HTMLResponse("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>MediBuddy - Loading...</title>
        <style>
            body { 
                font-family: system-ui; 
                display: flex; 
                justify-content: center; 
                align-items: center; 
                height: 100vh; 
                margin: 0;
                background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
                color: white;
            }
            .loader {
                text-align: center;
            }
            .spinner {
                width: 50px;
                height: 50px;
                border: 4px solid rgba(255,255,255,0.3);
                border-top: 4px solid #00d9ff;
                border-radius: 50%;
                animation: spin 1s linear infinite;
                margin: 0 auto 20px;
            }
            @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }
        </style>
    </head>
    <body>
        <div class="loader">
            <div class="spinner"></div>
            <h2>🏥 MediBuddy</h2>
            <p>Loading application...</p>
            <p style="opacity: 0.7; font-size: 14px;">If this persists, run the frontend build.</p>
        </div>
    </body>
    </html>
    """)


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
