from bt.sensor.supported.Movesense.avaiable_sensors import options_dict
from bt.sensor.supported.Movesense.notification_handlers import NotificationHandler
from bt.sensor.supported.connection import Connection
import pandas as pd

from rich import print

WRITE_CHARACTERISTIC_UUID = (
    "34800001-7185-4d5d-b431-630e7050e8f0"
)

NOTIFY_CHARACTERISTIC_UUID = (
    "34800002-7185-4d5d-b431-630e7050e8f0"
)


class MovesenseConnection(Connection):
    encoded_name = "Movesense"
    notification_handler = NotificationHandler()

    def get_df_header(self, unit):
        if unit == "ecg":
            return ["timestamp", "value"]
        elif unit == "hr":
            return ["timestamp", "hr", "rr"]
        else:
            return ["timestamp", "x", "y", "z"]

    async def start_connection(self, data_storage, state, client, service, units):
        try:
            # choosing handler appropriate to received data
            async def handler(_, data):
                await self.notification_handler.notification_handler_picker(_, data, data_storage, state, service, units[0]["name"])

            await client.start_notify(NOTIFY_CHARACTERISTIC_UUID, handler)

            # sending message via GATT that we want to subscribe to chosen sensor
            if state["verbose"]:
                print("Subscribing datastream")
            if "probing" in units[0]:
                await client.write_gatt_char(WRITE_CHARACTERISTIC_UUID,
                                             bytearray([1, 99]) + bytearray(options_dict[units[0]["name"]], "utf-8")
                                             + bytearray(units[0]["probing"], "utf-8"), response=True)
            else:
                await client.write_gatt_char(WRITE_CHARACTERISTIC_UUID,
                                             bytearray([1, 99]) + bytearray(options_dict[units[0]["name"]], "utf-8")
                                             , response=True)
        except Exception as e:
            print('[red]' + repr(e) + '[red]')

    async def stop_connection(self, client):
        await client.write_gatt_char(WRITE_CHARACTERISTIC_UUID, bytearray([2, 99]), response=True)
        print("Unsubscribing")
        await client.stop_notify(NOTIFY_CHARACTERISTIC_UUID)
        print("Stopping notifications")