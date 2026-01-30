import json
import httpx
from websockets.asyncio.client import connect


class WebThingClient:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")
        self.ws_url = self.base_url.replace("http://", "ws://")

    async def get_properties(self) -> list | dict:
        """Fetch all current property values via HTTP."""
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.base_url}/properties")
            return response.json()

    async def set_property(self, name: str, value: any) -> bool:
        """Update a property value via HTTP PUT."""
        async with httpx.AsyncClient() as client:
            url = f"{self.base_url}/properties/{name}"
            response = await client.put(url, json={name: value})
            return response.status_code == 200

    async def monitor(self) -> None:
        """Subscribe to live updates via WebSockets.

        Keeps printing the received updated state.
        """
        async with connect(self.ws_url) as websocket:
            print(f"Connected to live stream: {self.ws_url}")
            async for message in websocket:
                data = json.loads(message)
                if data["messageType"] == "propertyStatus":
                    print(f"Update received: {data['data']}")
