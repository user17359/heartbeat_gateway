from bt.sensor.supported.Movesense.notification_handlers import NotificationHandler
from bt.sensor.supported.connection import Connection

from rich import print

ECG_VOLTAGE_UUID = (
    "2BDD"
)

MOVEMENT_UUID = (
    "2BE2"
)

HR_UUID = (
    "180D"
)


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
            # choosing handler appropriate to received data
            async def handler(_, data):
                await self.notification_handler.notification_handler_picker(_, data, data_storage, state, service, units[0]["name"])

            if units[0]["name"] == "ecg":
                await client.start_notify(ECG_VOLTAGE_UUID, handler)
                self.subscriptions.append(ECG_VOLTAGE_UUID)
            elif units[0]["name"] == "hr":
                await client.start_notify(HR_UUID, handler)
                self.subscriptions.append(HR_UUID)
            else:
                await client.start_notify(MOVEMENT_UUID, handler)
                self.subscriptions.append(MOVEMENT_UUID)

            if state["verbose"]:
                print("Subscribing datastream")

        except Exception as e:
            print('[red]' + repr(e) + '[red]')

    async def stop_connection(self, client):
        for sub in self.subscriptions:
            await client.stop_notify(sub)
        print("Unsubscribing")
