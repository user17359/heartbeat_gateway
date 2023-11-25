from bluez_peripheral.gatt.service import Service
from bluez_peripheral.gatt.characteristic import characteristic, CharacteristicFlags as CharFlags

import json
from rich import print

from bt.app.data_classes.diary_entry import DiaryEntry
from server.send_entry import send_entry


class EventService(Service):
    entry_list = []

    def __init__(self):
        # Base 16 service UUID, This should be a primary service.
        super().__init__("4f8ef7bf-fe20-437b-9320-89e6108c82e0", True)

    # Characteristic called to add new event to diary
    @characteristic("27e571d9-53fa-4756-88da-07716d7ea633", CharFlags.WRITE_WITHOUT_RESPONSE)
    def new_entry(self, options):
        pass

    @new_entry.setter
    def new_entry(self, value, options):
        data = json.loads(value)
        entry = DiaryEntry(data["label"], data["hour"], data["minute"], data["description"])
        print("Registered entry :notebook:, label: " + entry.label \
              + " description: " + entry.description + " at time: " + str(entry.hour) + ":" + str(entry.minute))
        self.entry_list.append(entry)
        send_entry(entry)
