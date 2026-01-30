from functools import cached_property
import json
import httpx
from websockets.asyncio.client import connect


class WebThingClient:

    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")

    @property
    def available_things(self) -> list[dict[str, any]]:
        """Returns the list of thing descriptors available in the network"""
        self.base_url = self.base_url.rstrip("/")
        with httpx.Client() as client:
            response = client.get(f"{self.base_url}")
            things: dict[str, any] | list = response.json()
            if isinstance(response, dict):
                return [things]
            return things

    def lookup_thing_idx_by_id(self, thing_id: str) -> int | None:
        """Lookup the idx for the provided id.
        Inneficient, but addresses the dynamic changing scenario
        """
        index = None
        things = self.available_things
        for idx, thing in enumerate(things):
            if thing["id"] == thing_id:
                index = idx
                break
        return index

    async def get_properties(
        self, index: int | None = None, thing_id: str | None = None
    ) -> dict | None:
        """Fetch all current property values for a given thing via HTTP.

        It returns the Thing Description json.
        """
        assert (index is not None) or (id is not None)
        if not index and thing_id:
            index = self.lookup_thing_idx_by_id(thing_id)
        if index is None:
            return None

        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.base_url}/{index}/properties")
            return response.json()

    async def set_property(
        self,
        name: str,
        value: any,
        index: int | None = None,
        thing_id: str | None = None,
    ) -> bool:
        """Update a property value via HTTP PUT.

        Returns "True" if the operation was successful, "False" otherwise.
        """

        assert (index is not None) or (id is not None)
        if not index and thing_id:
            index = self.lookup_thing_idx_by_id(thing_id)
        if index is None:
            return False

        async with httpx.AsyncClient() as client:
            url = f"{self.base_url}/{index}/properties/{name}"
            response = await client.put(url, json={name: value})
            return response.status_code == 200

    async def monitor(
        self, index: int | None = None, thing_id: str | None = None
    ) -> None:
        """Subscribe to live updates via WebSockets.

        Keeps printing the received updated state.
        """

        assert (index is not None) or (id is not None)
        if not index and thing_id:
            index = self.lookup_thing_idx_by_id(thing_id)
        if not index:
            print("Unable to find thing to monitor")
            return

        ws_url = self.base_url.replace("http://", "ws://") + f"/{index}"
        async with connect(ws_url) as websocket:
            print(f"Connected to live stream: {ws_url}")
            async for message in websocket:
                data = json.loads(message)
                if data["messageType"] == "propertyStatus":
                    print(f"Update received: {data['data']}")
