import typer
import asyncio
from bleak import BleakScanner, BleakClient
from rich import print

from data_view import DataView

app = typer.Typer()
name_key = "Movesense"

WRITE_CHARACTERISTIC_UUID = (
    "34800001-7185-4d5d-b431-630e7050e8f0"
)

NOTIFY_CHARACTERISTIC_UUID = (
    "34800002-7185-4d5d-b431-630e7050e8f0"
)


@app.command()
def app():
    print("Scanning for :sparkles:BLE devices:sparkles:")
    asyncio.run(scan_app())


"""
def load_uuid():
    file = open("uuid.txt", "r")
    uuid.append(file.read())
    file.close()
"""


async def notification_handler(sender, data):
    """Simple notification handler which prints the data received."""
    d = DataView(data)
    # Dig data from the binary
    msg = "Data: ts: {}, ax: {}, ay: {}, az: {}".format(d.get_uint_32(2),
                                                        d.get_float_32(6),
                                                        d.get_float_32(10),
                                                        d.get_float_32(14))
    # queue message for later consumption
    print(msg)


async def scan_app():
    devices = await BleakScanner.discover(return_adv=True)
    for device, adv_data in devices.values():
        if adv_data.local_name is not None and name_key in adv_data.local_name:
            print("Found Movesense device :flushed:")
            # TODO: connection with mobile app
            async with BleakClient(device.address) as client:
                svcs = client.services
                print("Services :eyes:")
                for service in svcs:
                    print(service)
                    print("with characteristics :open_mouth::")
                    for char in service.characteristics:
                        print(char)
                    print("")
                print("Enabling notifications")
                await client.start_notify(NOTIFY_CHARACTERISTIC_UUID, notification_handler)
                print("Subscribing datastream")
                await client.write_gatt_char(WRITE_CHARACTERISTIC_UUID,
                                             bytearray([1, 99]) + bytearray("/Meas/Acc/13", "utf-8"), response=True)

                await asyncio.sleep(15.0)


if __name__ == '__main__':
    app()
