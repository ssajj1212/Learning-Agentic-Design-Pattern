import asyncio
import httpx
import json

async def test_sse():
    server_url = "http://localhost:8001"
    payload = {
        "capability": "analyze_sentiment",
        "parameters": {"ticker": "AAPL"}
    }
    
    async with httpx.AsyncClient() as client:
        # 1. Submit
        resp = await client.post(f"{server_url}/tasks", json=payload)
        task_id = resp.json()["task_id"]
        print(f"Task {task_id} submitted.")
        
        # 2. Stream
        print(f"Connecting to events for {task_id}...")
        try:
            async with client.stream("GET", f"{server_url}/tasks/{task_id}/events", timeout=10.0) as response:
                print(f"Status: {response.status_code}")
                async for line in response.aiter_lines():
                    print(f"RAW LINE: {line}")
                    if line.startswith("data: "):
                        data = json.loads(line[6:])
                        print(f"Parsed Event: {data['event']} -> {data['data']}")
                        if data['event'] == 'result':
                            print("Success!")
                            return
        except Exception as e:
            print(f"Error: {type(e).__name__}: {e}")

if __name__ == "__main__":
    asyncio.run(test_sse())
