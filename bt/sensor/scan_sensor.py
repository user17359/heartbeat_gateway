from bleak import BleakScanner
from rich import print

name_key = "Movesense"


async def scan_sensor():
    """Scanning for BLE devices with appropriate name"""
    print("Scanning for :sparkles: BLE devices:sparkles: ")
    devices = await BleakScanner.discover(return_adv=True)
    for device, adv_data in devices.values():
        if adv_data.local_name is not None and name_key in adv_data.local_name:
            print("Found Movesense device :flushed:")
            return device.address
