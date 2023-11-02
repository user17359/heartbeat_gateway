from datetime import datetime

from bluez_peripheral.gatt.service import Service
from bluez_peripheral.gatt.characteristic import characteristic, CharacteristicFlags as CharFlags

import json


class SensorService(Service):

    current_sensor = ""
    start_event = None
    end_event = None

    def __init__(self, scheduler):
        # Base 16 service UUID, This should be a primary service.
        super().__init__("a56f5e06-fd24-4ffe-906f-f82e916262bc", True)
        self.scheduler = scheduler

    def start_measurement(self):
        print("Measuring...")

    def end_measurement(self):
        print("End of measurement")

    @characteristic("18c7e933-73cf-4d47-9973-51a53f0fec4e", CharFlags.WRITE_WITHOUT_RESPONSE)
    def new_measurement(self, options):
        pass

    @new_measurement.setter
    def new_measurement(self, value, options):
        data = json.loads(value)
        self.current_sensor = data["mac"]
        now = datetime.now()
        run_at = datetime(now.year,
                          now.month,
                          now.day,
                          data["startHour"],
                          data["startMinute"])
        stop_at = datetime(now.year,
                           now.month,
                           now.day,
                           data["endHour"],
                           data["endMinute"])

        self.start_event = self.scheduler.enterabs(run_at.timestamp(),
                                                   10,
                                                   self.start_measurement())
        self.end_event = self.scheduler.enterabs(stop_at.timestamp(),
                                                 10,
                                                 self.end_measurement())

