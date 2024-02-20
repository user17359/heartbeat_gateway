from bluez_peripheral.gatt.service import Service
from bluez_peripheral.gatt.characteristic import characteristic, CharacteristicFlags as CharFlags

from bt.app.data_classes.bt_device import BtDevice
from bt.sensor.scan_sensor import scan_sensor

import json


class ConnectivityService(Service):

    sensor_list = []

    def __init__(self):
        # Base 16 service UUID, This should be a primary service.
        super().__init__("6672b3e6-477e-4e52-a3fb-a440c57dc857", True)

    # Characteristic used to get list of remembered sensors
    @characteristic("9f03f5db-93ba-402b-951f-1c8e008b5adc", CharFlags.READ)
    def connected_sensors(self, options):
        json_list = json.dumps([item.to_json() for item in self.sensor_list])
        data = bytes(json_list, "utf-8")
        return data

    # Characteristic used to perform scan for BLE devices from gateway
    @characteristic("5fc4077d-e88f-4b5d-956b-955d30ec5899", CharFlags.READ)
    async def ble_scan(self, options):
        scan_results = await scan_sensor()
        json_list = json.dumps([item.to_json() for item in scan_results])
        data = bytes(json_list, "utf-8")
        return data

    # Characteristic used to add new remembered sensor
    @characteristic("1fe83b02-0788-4af7-9a69-af6b9e9782a7", CharFlags.WRITE_WITHOUT_RESPONSE)
    def new_sensor(self, options):
        pass

    @new_sensor.setter
    def new_sensor(self, value, options):
        data = json.loads(value)
        sensor = BtDevice(data["name"], data["mac"], "waiting")
        self.sensor_list.append(sensor)
