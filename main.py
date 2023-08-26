import typer
import asyncio
from bleak import BleakScanner, BleakClient
from rich import print

app = typer.Typer()
uuid = []


@app.command()
def app():
    load_uuid()
    print("Scanning for :sparkles:BLE devices:sparkles:")
    asyncio.run(scan_app())


def load_uuid():
    file = open("uuid.txt", "r")
    uuid.append(file.read())
    file.close()


async def scan_app():
    devices = await BleakScanner.discover(return_adv=True)
    for device, adv_data in devices.values():
        if adv_data.service_uuids == uuid:
            print("Found mobile app :flushed:")
            # TODO: connection with mobile app
            async with BleakClient(device.address) as client:
                svcs = client.services
                print("Services :eyes:")
                for service in svcs:
                    print(service)



if __name__ == '__main__':
    app()
