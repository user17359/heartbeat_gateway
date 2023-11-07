import asyncio
# import pandas as pd
from threading import Thread
from datetime import datetime
from rich import print

from bluez_peripheral.gatt.service import Service
from bluez_peripheral.gatt.characteristic import characteristic, CharacteristicFlags as CharFlags

import json

from bt.sensor.timed_connection import launch_timed, start_connection, launch_stop


class SensorService(Service):
    sensors = {}

    def __init__(self, scheduler, bus, adapter):
        # Base 16 service UUID, This should be a primary service.
        super().__init__("a56f5e06-fd24-4ffe-906f-f82e916262bc", True)
        self.scheduler = scheduler
        self.bus = bus
        self.adapter = adapter

    async def start_connection(self, mac):
        print("Connecting with " + mac)
        return await start_connection(mac, self.bus, self.adapter)

    def start_measurement(self, mac):
        print("Measuring for " + mac + "...")

        launch_timed(
            "acc",
            self.sensors[mac]["df"],
            {"verbose": True},
            self.sensors[mac]["client"])

    def end_measurement(self, mac, label):
        print("End of measurement for " + mac)
        launch_stop(
            self.sensors[mac]["client"]
        )
        # self.sensors[mac]["df"].to_csv(label + '.csv', index=False)
        print("Data saved to [blue]" + label + ".csv[blue] :floppy_disk:")

    @characteristic("18c7e933-73cf-4d47-9973-51a53f0fec4e", CharFlags.WRITE_WITHOUT_RESPONSE)
    async def new_measurement(self, options):
        pass

    @new_measurement.setter
    async def new_measurement(self, value, options):
        data = json.loads(value)

        now = datetime.now()

        mac = data["mac"]

        run_at = datetime(now.year,
                          now.month,
                          now.day,
                          data["startHour"],
                          data["startMinute"])
        end_at = datetime(now.year,
                          now.month,
                          now.day,
                          data["endHour"],
                          data["endMinute"])

        print(run_at)
        print(end_at)

        client = await self.start_connection(mac)

        self.sensors[mac] = {"run_at": run_at,
                             "end_at": end_at,
                             "start_event": None,
                             "end_event": None,
                             "df": None,
                             "client": client}

        start_event = self.scheduler.enterabs(run_at.timestamp(),
                                              10,
                                              self.start_measurement,
                                              argument=(mac,))
        end_event = self.scheduler.enterabs(end_at.timestamp(),
                                            10,
                                            self.end_measurement,
                                            argument=(mac, data['label'],))

        # df = pd.DataFrame(columns=["timestamp", "x", "y", "z"])

        self.sensors[mac]["start_event"] = start_event
        self.sensors[mac]["end_event"] = end_event


