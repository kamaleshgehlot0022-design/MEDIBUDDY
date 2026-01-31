"""
MediBuddy - Comprehensive Test Suite
Tests all API endpoints and core functionality.
"""

import asyncio
import httpx
import json
import sys

BASE_URL = "http://localhost:8000"

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'

def success(msg):
    print(f"{Colors.GREEN}✅ PASS{Colors.END} - {msg}")

def fail(msg, error=None):
    print(f"{Colors.RED}❌ FAIL{Colors.END} - {msg}")
    if error:
        print(f"   Error: {error}")

def info(msg):
    print(f"{Colors.BLUE}ℹ️  INFO{Colors.END} - {msg}")

async def test_api():
    """Test all API endpoints."""
    
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=30.0) as client:
        print("\n" + "="*60)
        print("🧪 MEDIBUDDY API TEST SUITE")
        print("="*60 + "\n")
        
        passed = 0
        failed = 0
        
        # ============================================
        # 1. System Status
        # ============================================
        print("📊 SYSTEM STATUS TESTS")
        print("-" * 40)
        
        try:
            r = await client.get("/api/status")
            data = r.json()
            
            if r.status_code == 200 and data.get("status") == "online":
                success(f"GET /api/status - System online, version {data.get('version')}")
                passed += 1
            else:
                fail("GET /api/status - Unexpected response")
                failed += 1
                
            # Check realtime_engine stats
            if "realtime_engine" in data:
                info(f"  Knowledge Graph facts: {data['realtime_engine']['knowledge_graph']['total_facts']}")
                info(f"  Active sources: {data['realtime_engine']['firehose']['sources_active']}")
        except Exception as e:
            fail("GET /api/status", str(e))
            failed += 1
        
        print()
        
        # ============================================
        # 2. Drug Endpoints
        # ============================================
        print("💊 DRUG LOOKUP TESTS")
        print("-" * 40)
        
        # Test drug list
        try:
            r = await client.get("/api/drugs?limit=5")
            data = r.json()
            
            if r.status_code == 200 and len(data) > 0:
                success(f"GET /api/drugs - Retrieved {len(data)} drugs")
                passed += 1
            else:
                fail("GET /api/drugs - No drugs returned")
                failed += 1
        except Exception as e:
            fail("GET /api/drugs", str(e))
            failed += 1
        
        # Test drug search
        try:
            r = await client.get("/api/drugs?search=metformin")
            data = r.json()
            
            if r.status_code == 200 and any(d.get("id") == "metformin" for d in data):
                success("GET /api/drugs?search=metformin - Found metformin")
                passed += 1
            else:
                fail("GET /api/drugs?search=metformin - Drug not found")
                failed += 1
        except Exception as e:
            fail("GET /api/drugs?search=metformin", str(e))
            failed += 1
        
        # Test drug details
        try:
            r = await client.get("/api/drugs/ozempic")
            data = r.json()
            
            if r.status_code == 200 and "drug" in data:
                drug = data["drug"]
                success(f"GET /api/drugs/ozempic - Brand: {drug.get('brand_name')}, Generic: {drug.get('generic_name')}")
                passed += 1
                
                # Verify structure
                if drug.get("identifiers") and drug.get("pricing"):
                    info(f"  NDC: {drug['identifiers']['ndc']}")
                    info(f"  AWP: ${drug['pricing']['awp']}")
            else:
                fail("GET /api/drugs/ozempic - Invalid response structure")
                failed += 1
        except Exception as e:
            fail("GET /api/drugs/ozempic", str(e))
            failed += 1
        
        # Test drug pricing
        try:
            r = await client.get("/api/drugs/eliquis/pricing")
            data = r.json()
            
            if r.status_code == 200 and "pricing" in data:
                p = data["pricing"]
                success(f"GET /api/drugs/eliquis/pricing - AWP: ${p.get('awp')}, WAC: ${p.get('wac')}")
                passed += 1
            else:
                fail("GET /api/drugs/eliquis/pricing - Invalid response")
                failed += 1
        except Exception as e:
            fail("GET /api/drugs/eliquis/pricing", str(e))
            failed += 1
        
        # Test 404 for nonexistent drug
        try:
            r = await client.get("/api/drugs/nonexistent_drug_xyz")
            if r.status_code == 404:
                success("GET /api/drugs/nonexistent - Correctly returns 404")
                passed += 1
            else:
                fail(f"GET /api/drugs/nonexistent - Expected 404, got {r.status_code}")
                failed += 1
        except Exception as e:
            fail("GET /api/drugs/nonexistent", str(e))
            failed += 1
        
        print()
        
        # ============================================
        # 3. Coverage Endpoints
        # ============================================
        print("🏥 PAYER COVERAGE TESTS")
        print("-" * 40)
        
        # Test payers list
        try:
            r = await client.get("/api/payers")
            data = r.json()
            
            if r.status_code == 200 and len(data) > 0:
                success(f"GET /api/payers - Found {len(data)} payers")
                passed += 1
                info(f"  Payers: {', '.join(p['name'] for p in data[:3])}...")
            else:
                fail("GET /api/payers - No payers returned")
                failed += 1
        except Exception as e:
            fail("GET /api/payers", str(e))
            failed += 1
        
        # Test coverage lookup
        try:
            r = await client.get("/api/coverage/ozempic")
            data = r.json()
            
            if r.status_code == 200 and len(data) > 0:
                success(f"GET /api/coverage/ozempic - Found coverage from {len(data)} payers")
                passed += 1
                
                # Check structure
                first = data[0]
                if "payer" in first and "coverage" in first:
                    info(f"  {first['payer']['name']}: Tier {first['coverage']['tier']}, PA: {first['coverage']['prior_auth_required']}")
            else:
                fail("GET /api/coverage/ozempic - No coverage returned")
                failed += 1
        except Exception as e:
            fail("GET /api/coverage/ozempic", str(e))
            failed += 1
        
        # Test coverage with payer filter
        try:
            r = await client.get("/api/coverage/metformin?payer=Aetna")
            data = r.json()
            
            if r.status_code == 200:
                success(f"GET /api/coverage/metformin?payer=Aetna - Filtered by payer")
                passed += 1
            else:
                fail("GET /api/coverage/metformin?payer=Aetna - Failed")
                failed += 1
        except Exception as e:
            fail("GET /api/coverage/metformin?payer=Aetna", str(e))
            failed += 1
        
        print()
        
        # ============================================
        # 4. Drug Interactions
        # ============================================
        print("⚠️ DRUG INTERACTION TESTS")
        print("-" * 40)
        
        # Test interaction check
        try:
            r = await client.post("/api/interactions/check", json={"drugs": ["warfarin", "aspirin"]})
            data = r.json()
            
            if r.status_code == 200:
                success(f"POST /api/interactions/check - Found {len(data.get('interactions', []))} interactions")
                passed += 1
                
                if data.get("has_major_interaction"):
                    info(f"  ⚠️ Major interaction detected!")
            else:
                fail(f"POST /api/interactions/check - Status {r.status_code}")
                failed += 1
        except Exception as e:
            fail("POST /api/interactions/check", str(e))
            failed += 1
        
        # Test with no interactions
        try:
            r = await client.post("/api/interactions/check", json={"drugs": ["metformin", "lisinopril"]})
            data = r.json()
            
            if r.status_code == 200:
                success(f"POST /api/interactions/check (safe combo) - {data.get('summary', 'OK')}")
                passed += 1
            else:
                fail("POST /api/interactions/check (safe combo)")
                failed += 1
        except Exception as e:
            fail("POST /api/interactions/check (safe combo)", str(e))
            failed += 1
        
        # Test validation error
        try:
            r = await client.post("/api/interactions/check", json={"drugs": ["only_one_drug"]})
            if r.status_code == 400:
                success("POST /api/interactions/check (1 drug) - Correctly rejects invalid input")
                passed += 1
            else:
                fail(f"POST /api/interactions/check (1 drug) - Expected 400, got {r.status_code}")
                failed += 1
        except Exception as e:
            fail("POST /api/interactions/check (1 drug)", str(e))
            failed += 1
        
        print()
        
        # ============================================
        # 5. Prior Authorization
        # ============================================
        print("📋 PRIOR AUTH TESTS")
        print("-" * 40)
        
        try:
            r = await client.post("/api/prior-auth/generate", json={
                "drug_name": "Ozempic",
                "payer_name": "Aetna",
                "diagnosis": "Type 2 Diabetes Mellitus"
            })
            data = r.json()
            
            if r.status_code == 200 and "form" in data:
                success("POST /api/prior-auth/generate - PA form generated!")
                passed += 1
                
                form = data["form"]
                if "Clinical Justification" in form:
                    info("  Contains clinical justification section")
            else:
                fail(f"POST /api/prior-auth/generate - Status {r.status_code}")
                failed += 1
        except Exception as e:
            fail("POST /api/prior-auth/generate", str(e))
            failed += 1
        
        print()
        
        # ============================================
        # 6. AI Chat
        # ============================================
        print("🤖 AI CHAT TESTS")
        print("-" * 40)
        
        try:
            r = await client.post("/api/chat", json={
                "message": "What is the price of Ozempic?"
            })
            data = r.json()
            
            if r.status_code == 200 and "response" in data:
                success("POST /api/chat - AI responded!")
                passed += 1
                
                # Show snippet
                response = data["response"][:100] + "..." if len(data["response"]) > 100 else data["response"]
                info(f"  Response: {response}")
            else:
                fail(f"POST /api/chat - Status {r.status_code}")
                failed += 1
        except Exception as e:
            fail("POST /api/chat", str(e))
            failed += 1
        
        try:
            r = await client.post("/api/chat", json={
                "message": "Is Eliquis covered by UnitedHealthcare?"
            })
            data = r.json()
            
            if r.status_code == 200 and "response" in data:
                success("POST /api/chat (coverage query) - AI responded!")
                passed += 1
            else:
                fail("POST /api/chat (coverage query)")
                failed += 1
        except Exception as e:
            fail("POST /api/chat (coverage query)", str(e))
            failed += 1
        
        print()
        
        # ============================================
        # 7. Recent Updates
        # ============================================
        print("🔄 REAL-TIME UPDATE TESTS")
        print("-" * 40)
        
        try:
            r = await client.get("/api/updates/recent?hours=24")
            data = r.json()
            
            if r.status_code == 200:
                success(f"GET /api/updates/recent - {data.get('count', 0)} updates in last 24h")
                passed += 1
            else:
                fail("GET /api/updates/recent")
                failed += 1
        except Exception as e:
            fail("GET /api/updates/recent", str(e))
            failed += 1
        
        print()
        
        # ============================================
        # 8. Static Files
        # ============================================
        print("🌐 FRONTEND TESTS")
        print("-" * 40)
        
        try:
            r = await client.get("/")
            if r.status_code == 200 and "MediBuddy" in r.text:
                success("GET / - Frontend HTML loaded")
                passed += 1
            else:
                fail("GET / - Frontend not found")
                failed += 1
        except Exception as e:
            fail("GET /", str(e))
            failed += 1
        
        try:
            r = await client.get("/static/styles.css")
            if r.status_code == 200 and len(r.text) > 1000:
                success(f"GET /static/styles.css - CSS loaded ({len(r.text)} bytes)")
                passed += 1
            else:
                fail("GET /static/styles.css")
                failed += 1
        except Exception as e:
            fail("GET /static/styles.css", str(e))
            failed += 1
        
        try:
            r = await client.get("/static/app.js")
            if r.status_code == 200 and len(r.text) > 1000:
                success(f"GET /static/app.js - JS loaded ({len(r.text)} bytes)")
                passed += 1
            else:
                fail("GET /static/app.js")
                failed += 1
        except Exception as e:
            fail("GET /static/app.js", str(e))
            failed += 1
        
        print()
        
        # ============================================
        # SUMMARY
        # ============================================
        print("="*60)
        total = passed + failed
        print(f"📊 TEST RESULTS: {passed}/{total} passed ({100*passed//total}%)")
        
        if failed == 0:
            print(f"{Colors.GREEN}🎉 ALL TESTS PASSED!{Colors.END}")
        else:
            print(f"{Colors.RED}⚠️ {failed} tests failed{Colors.END}")
        
        print("="*60)
        
        return failed == 0


if __name__ == "__main__":
    try:
        result = asyncio.run(test_api())
        sys.exit(0 if result else 1)
    except Exception as e:
        print(f"{Colors.RED}❌ Test suite failed: {e}{Colors.END}")
        sys.exit(1)
