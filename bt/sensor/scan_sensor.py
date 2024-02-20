from bleak import BleakScanner
from rich import print

from bt.app.data_classes.bt_device import BtDevice

name_key = "Movesense"


async def scan_sensor():
    bt_list = []
    """Scanning for BLE devices with appropriate name"""
    print("Scanning for :sparkles: BLE devices:sparkles: ")
    devices = await BleakScanner.discover(return_adv=True, timeout=3)
    for device, adv_data in devices.values():
        if adv_data.local_name is not None:
            print(adv_data.local_name, device.address)
            bt_list.append(BtDevice(adv_data.local_name, device.address, "waiting"))
    return bt_list
