from bt.sensor.supported.Movesense.avaiable_sensors import options_dict
from bt.sensor.supported.Movesense.notification_handlers import notification_handler_ecg, notification_handler_imu
from bt.sensor.supported.connection import Connection
import pandas as pd

WRITE_CHARACTERISTIC_UUID = (
    "34800001-7185-4d5d-b431-630e7050e8f0"
)

NOTIFY_CHARACTERISTIC_UUID = (
    "34800002-7185-4d5d-b431-630e7050e8f0"
)


class MovesenseConnection(Connection):
    def get_df_header(self, unit):
        if unit == "ecg":
            return pd.DataFrame(columns=["timestamp", "value"])
        else:
            return pd.DataFrame(columns=["timestamp", "x", "y", "z"])

    async def start_connection(self, df, state, client, service, units):
        try:
            # choosing handler appropriate to received data
            if units[0] == "ecg":
                async def handler(_, data):
                    await notification_handler_ecg(_, data, df, state, service)

                await client.start_notify(NOTIFY_CHARACTERISTIC_UUID, handler)
            else:
                async def handler(_, data):
                    await notification_handler_imu(_, data, df, state, service, units[0])

                await client.start_notify(NOTIFY_CHARACTERISTIC_UUID, handler)

            # sending message via GATT that we want to subscribe to chosen sensor
            if state["verbose"]:
                print("Subscribing datastream")
            await client.write_gatt_char(WRITE_CHARACTERISTIC_UUID,
                                         bytearray([1, 99]) + bytearray(options_dict[units[0]], "utf-8"), response=True)
        except Exception as e:
            print('[red]' + repr(e) + '[red]')

    async def stop_connection(self, client):
        await client.write_gatt_char(WRITE_CHARACTERISTIC_UUID, bytearray([2, 99]), response=True)
        print("Unsubscribing")
        await client.stop_notify(NOTIFY_CHARACTERISTIC_UUID)
        print("Stopping notifications")