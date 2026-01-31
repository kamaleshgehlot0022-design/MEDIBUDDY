"""Quick test for Hugging Face AI integration."""
import asyncio
import httpx

async def test_chat():
    async with httpx.AsyncClient(timeout=60.0) as client:
        print("Testing AI Chat with Hugging Face...")
        
        # Test 1: Price query
        r = await client.post(
            "http://localhost:8000/api/chat",
            json={"message": "What is the price of Ozempic?"}
        )
        print(f"\nStatus: {r.status_code}")
        data = r.json()
        print(f"Response: {data.get('response', '')[:300]}...")
        print(f"Sources: {data.get('sources', [])}")
        print(f"Confidence: {data.get('confidence', 0)}")
        
        # Test 2: Coverage query  
        print("\n" + "="*50)
        r = await client.post(
            "http://localhost:8000/api/chat",
            json={"message": "Is Eliquis covered by Aetna?"}
        )
        print(f"\nStatus: {r.status_code}")
        data = r.json()
        print(f"Response: {data.get('response', '')[:300]}...")
        print(f"Sources: {data.get('sources', [])}")

if __name__ == "__main__":
    asyncio.run(test_chat())
