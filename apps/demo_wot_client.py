import asyncio
import json
import sys
import httpx
from websockets.asyncio.client import connect

DEFAULT_DEMO_THING = "lamp"  # 'lamp' or 'sensor'


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


async def lamp_client_manager():

    lamp_client = WebThingClient("http://localhost:8888/0")

    action = ""
    while True:
        print("Estado atual")
        print("=" * 8)
        props = await lamp_client.get_properties()
        print(props)
        print()

        print("Gostaria de [L]igar [D]esligar [Q]uit")
        action = input("> ").lower()
        if action == "q":
            break
        if action not in ["l", "d"]:
            continue
        set_on = action == "l"
        success = await lamp_client.set_property("on", set_on)
        print(f"Retorno da operação: {success}")
        print("=" * 8)


async def sensor_client_manager():
    sensor_client = WebThingClient("http://localhost:8888/1")
    print("Estado atual")
    print("=" * 8)
    props = await sensor_client.get_properties()
    print(props)
    print()

    await sensor_client.monitor()


def main():
    target = (DEFAULT_DEMO_THING if len(sys.argv == 1) else sys.argv[1]).lower()

    try:
        if target == "lamp":
            asyncio.run(lamp_client_manager())
        if target == "sensor":
            asyncio.run(sensor_client_manager())
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
