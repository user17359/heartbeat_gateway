from bt.sensor.supported.Movesense.notification_handlers import NotificationHandler
from bt.sensor.supported.Movesense.translations import probing_to_diff
from bt.sensor.supported.connection import Connection

from rich import print
from bleak.uuids import normalize_uuid_16

from bt.sensor.utils.data_view import DataView

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
        elif unit == "imu":
            return ["timestamp", "accX", "accY", "accZ", "gyroX", "gyroY", "gyroZ", "magX", "magY", "magZ"]
        else:
            raise Exception()

    async def start_connection(self, data_storage, state, client, service, units):
        try:
            for unit in units:
                if unit["name"] == "ecg":
                    await client.write_gatt_char(ECG_PROBING_UUID, probing_to_diff[unit["probing"]])
                    diff = int.from_bytes((await client.read_gatt_char(ECG_PROBING_UUID))[:1], byteorder='little')

                    async def ecg_handler(_, data):
                        d = DataView(data)
                        await self.notification_handler.notification_handler_ecg(_, d, data_storage["ecg"], state,
                                                                                 service, diff)
                    await client.start_notify(ECG_VOLTAGE_UUID, ecg_handler)
                    self.subscriptions.append(ECG_VOLTAGE_UUID)
                elif unit["name"] == "hr":
                    async def hr_handler(_, data):
                        d = DataView(data)
                        await self.notification_handler.notification_handler_hr(_, d, data_storage["hr"], state,
                                                                                service)
                    await client.start_notify(HR_UUID, hr_handler)
                    self.subscriptions.append(HR_UUID)
                elif unit["name"] == "imu":
                    await client.write_gatt_char(MOVEMENT_PROBING_UUID, probing_to_diff[unit["probing"]])
                    diff = int.from_bytes((await client.read_gatt_char(MOVEMENT_PROBING_UUID))[:1], byteorder='little')

                    async def imu_handler(_, data):
                        d = DataView(data)
                        await self.notification_handler.notification_handler_imu(_, d, data_storage["imu"], state,
                                                                                 service, diff)
                    await client.start_notify(MOVEMENT_UUID, imu_handler)
                    self.subscriptions.append(MOVEMENT_UUID)
                else:
                    raise Exception()

            if state["verbose"]:
                print("Subscribing datastream")

        except Exception as e:
            print('[red]' + repr(e) + '[red]')

    async def stop_connection(self, client):
        for sub in self.subscriptions:
            print('Cancelling' + str(sub))
            await client.stop_notify(sub)
        print("Unsubscribing")
        self.subscriptions.clear()
