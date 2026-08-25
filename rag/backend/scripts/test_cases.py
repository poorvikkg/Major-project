import asyncio
import httpx
import os
import time

BASE_URL = "http://localhost:8000"

async def test_health():
    print("\n--- Testing /health ---")
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/health")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")

async def test_chat_statistics():
    print("\n--- Testing /chat (Statistics Query) ---")
    async with httpx.AsyncClient(timeout=30.0) as client:
        payload = {
            "query": "What are the general statistics for Property stolen and recovered? Give me a brief summary."
        }
        response = await client.post(f"{BASE_URL}/chat", json=payload)
        print(f"Status: {response.status_code}")
        try:
            data = response.json()
            print(f"Confidence: {data.get('confidence')}")
            print(f"Sources: {data.get('sources')}")
            print(f"Answer: {data.get('answer')}")
        except Exception as e:
            print(f"Error parsing response: {response.text}")

async def test_chat_general():
    print("\n--- Testing /chat (General Query) ---")
    async with httpx.AsyncClient(timeout=30.0) as client:
        payload = {
            "query": "What is the procedure for filing an FIR?"
        }
        response = await client.post(f"{BASE_URL}/chat", json=payload)
        print(f"Status: {response.status_code}")
        try:
            data = response.json()
            print(f"Confidence: {data.get('confidence')}")
            print(f"Answer: {data.get('answer')}")
        except Exception as e:
            print(f"Error parsing response: {response.text}")

async def main():
    print("Starting PCIA Test Cases...")
    
    # Ensure backend is up by retrying
    connected = False
    for i in range(10):
        try:
            async with httpx.AsyncClient() as client:
                await client.get(f"{BASE_URL}/health")
                connected = True
                break
        except Exception:
            print(f"Waiting for backend... ({i+1}/10)")
            await asyncio.sleep(3)
            
    if not connected:
        print(f"Backend is not reachable at {BASE_URL}. Please start the server.")
        return

    await test_health()
    await test_chat_statistics()
    await test_chat_general()
    
    print("\nTesting complete.")

if __name__ == "__main__":
    asyncio.run(main())
