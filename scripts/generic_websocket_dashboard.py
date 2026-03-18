"""Simple websocket client for manual communication protocol testing."""

import aiohttp
import asyncio
import json

# Example request payload for the communication protocol websocket. Adjust the
# execution_dag, target_exports, and kwargs to match the reducers you want to
# exercise.
REQUEST = {
    "docs_request": {
        "execution_dag": "writing_observer",
        "target_exports": ["docs_with_roster"],
        "kwargs": {
            "course_id": 12345678901
        },
    }
}


async def main():
    async with aiohttp.ClientSession() as session:
        async with session.ws_connect(
            "http://localhost:8888/wsapi/communication_protocol",
            timeout=5,
        ) as ws:
            await ws.send_json(REQUEST)
            async for msg in ws:
                if msg.type == aiohttp.WSMsgType.TEXT:
                    try:
                        parsed = json.loads(msg.data)
                    except json.JSONDecodeError:
                        parsed = msg.data
                    print(json.dumps(parsed, indent=2))
                elif msg.type == aiohttp.WSMsgType.ERROR:
                    print("Error received from websocket:", msg)
                    break


if __name__ == '__main__':
    asyncio.run(main())
