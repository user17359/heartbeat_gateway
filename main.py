import typer
import asyncio
from bleak import BleakScanner

app = typer.Typer()


@app.command()
def startup():
    print("Scanning for BLE devices...")
    asyncio.run(scan())


async def scan():
    devices = await BleakScanner.discover()
    for d in devices:
        print(d.details)

if __name__ == '__main__':
    app()
