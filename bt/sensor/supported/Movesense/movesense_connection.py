from bt.sensor.supported.Movesense.notification_handlers import NotificationHandler
from bt.sensor.supported.connection import Connection

from rich import print
from bleak.uuids import normalize_uuid_16

ECG_VOLTAGE_UUID = normalize_uuid_16(0x2BDD)
ECG_PROBING_UUID = normalize_uuid_16(0x2BE3)

MOVEMENT_UUID = normalize_uuid_16(0x2BE2)
MOVEMENT_PROBING_UUID = normalize_uuid_16(0x2BE4)

HR_UUID = normalize_uuid_16(0x2A37)


class MovesenseConnection(Connection):
    encoded_name = "Movesense"
    notification_handler = NotificationHandler()
    subscriptions = []

    def get_df_header(self, unit):
        if unit == "ecg":
            return ["timestamp", "value"]
        elif unit == "hr":
            return ["timestamp", "hr", "rr"]
        else:
            return ["timestamp", "accX", "accY", "accZ", "gyroX", "gyroY", "gyroZ", "magX", "magY", "magZ"]

    async def start_connection(self, data_storage, state, client, service, units):
        try:
            if units[0]["name"] == "ecg":

                diff = int.from_bytes((await client.read_gatt_char(ECG_PROBING_UUID))[:1], byteorder='little')

                async def handler(_, data):
                    await self.notification_handler.notification_handler_ecg(_, data, data_storage, state, service,
                                                                             diff)
                await client.start_notify(ECG_VOLTAGE_UUID, handler)
                self.subscriptions.append(ECG_VOLTAGE_UUID)
            elif units[0]["name"] == "hr":
                async def handler(_, data):
                    await self.notification_handler.notification_handler_hr(_, data, data_storage, state, service)
                await client.start_notify(HR_UUID, handler)
                self.subscriptions.append(HR_UUID)
            else:
                diff = int.from_bytes((await client.read_gatt_char(MOVEMENT_PROBING_UUID))[:1], byteorder='little')

                async def handler(_, data):
                    await self.notification_handler.notification_handler_imu(_, data, data_storage, state, service,
                                                                             units[0], diff)
                await client.start_notify(MOVEMENT_UUID, handler)
                self.subscriptions.append(MOVEMENT_UUID)

            if state["verbose"]:
                print("Subscribing datastream")

        except Exception as e:
            print('[red]' + repr(e) + '[red]')

    async def stop_connection(self, client):
        for sub in self.subscriptions:
            print('Cancelling' + str(sub))
            await client.stop_notify(sub)
        print("Unsubscribing")
