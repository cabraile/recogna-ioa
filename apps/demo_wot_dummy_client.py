import asyncio
import sys
from recogna_ioa.web_thing_client import WebThingClient

DEFAULT_DEMO_THING = "lamp"  # 'lamp' or 'sensor'


async def lamp_client_manager():

    client = WebThingClient("http://localhost:8888")

    action = ""
    while True:
        print("Estado atual")
        print("=" * 8)
        props = await client.get_properties()
        print(props)
        print()

        print("Gostaria de [L]igar [D]esligar [Q]uit")
        action = input("> ").lower()
        if action == "q":
            break
        if action not in ["l", "d"]:
            continue
        set_on = action == "l"
        success = await client.set_property("on", set_on, index=0)
        print(f"Retorno da operação: {success}")
        print("=" * 8)


async def sensor_client_manager():
    client = WebThingClient("http://localhost:8888")
    print("Estado atual")
    print("=" * 8)
    props = await client.get_properties(index=1)
    print(props)
    print()

    # also works with the thing_id!
    await client.monitor(thing_id="urn:dev:ops:my-humidity-sensor-1234")


def main():
    target = (DEFAULT_DEMO_THING if len(sys.argv) == 1 else sys.argv[1]).lower()

    try:
        if target == "lamp":
            asyncio.run(lamp_client_manager())
        if target == "sensor":
            asyncio.run(sensor_client_manager())
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
