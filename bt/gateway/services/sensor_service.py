import asyncio
# import pandas as pd
from threading import Thread
from datetime import datetime
from rich import print

from bluez_peripheral.gatt.service import Service
from bluez_peripheral.gatt.characteristic import characteristic, CharacteristicFlags as CharFlags

import json

from bt.sensor.timed_connection import launch_timed, start_connection, launch_stop, launch_disconnect


class SensorService(Service):
    sensors = {}
    current_mac = ""

    def __init__(self, scheduler, bus, adapter):
        # Base 16 service UUID, This should be a primary service.
        super().__init__("a56f5e06-fd24-4ffe-906f-f82e916262bc", True)
        self.scheduler = scheduler
        self.bus = bus
        self.adapter = adapter

    async def start_connection(self, mac):
        print("Connecting with " + mac)
        self.update_progress({"state": "scheduled", "info": str(self.sensors[mac]["run_at"].hour) + ":" +
                                                            str(self.sensors[mac]["run_at"].minute)})
        return await start_connection(mac, self.bus, self.adapter)

    def start_measurement(self, mac):
        print("Measuring for " + mac + "...")

        launch_timed(
            self.sensors[mac]["units"][0],
            self.sensors[mac]["df"],
            {"verbose": True},
            self.sensors[mac]["client"],
            self)

    def end_measurement(self, mac):
        print("End of measurement for " + mac)
        launch_stop(
            self.sensors[mac]["client"],
            self
        )
        # self.sensors[mac]["df"].to_csv(label + '.csv', index=False)
        # self.update_progress({"state": "empty", "info": ""})
        print("Data saved to [blue]" + self.sensors[mac]["label"] + ".csv[blue] :floppy_disk:")

    @characteristic("18c7e933-73cf-4d47-9973-51a53f0fec4e", CharFlags.WRITE_WITHOUT_RESPONSE)
    async def new_measurement(self, options):
        pass

    @new_measurement.setter
    async def new_measurement(self, value, options):
        data = json.loads(value)

        now = datetime.now()

        mac = data["mac"]
        self.current_mac = mac

        units = []
        for unit in data["sensors"]:
            units.append(unit["name"])

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

        self.sensors[mac] = {"run_at": run_at,
                             "end_at": end_at,
                             "start_event": None,
                             "end_event": None,
                             "df": None,
                             "client": None,
                             "units": units,
                             "label": data['label'],
                             "state": "empty"}

        client = await self.start_connection(mac)

        self.sensors[mac]["client"] = client

        start_event = self.scheduler.enterabs(run_at.timestamp(),
                                              10,
                                              self.start_measurement,
                                              argument=(mac,))
        end_event = self.scheduler.enterabs(end_at.timestamp(),
                                            10,
                                            self.end_measurement,
                                            argument=(mac,))

        # df = pd.DataFrame(columns=["timestamp", "x", "y", "z"])

        self.sensors[mac]["start_event"] = start_event
        self.sensors[mac]["end_event"] = end_event

    @characteristic("46dff0ae-21e2-4e55-8b38-3ae249e23884", CharFlags.NOTIFY)
    def measurement_progress(self, options):
        pass

    def update_progress(self, state):
        print("Updating progress")
        json_string = json.dumps(state)
        self.sensors[self.current_mac]["state"] = state["state"]
        data = bytes(json_string, "utf-8")
        self.measurement_progress.changed(data)

    @characteristic("2fd2ac39-1f6b-4d55-aa2b-3dd049420235", CharFlags.WRITE_WITHOUT_RESPONSE)
    def measurement_info_write(self, options):
        pass

    @measurement_info_write.setter
    async def measurement_info_write(self, value, options):
        string_value = value.decode("utf-8")
        print("Writing current mac: " + string_value)
        self.current_mac = string_value

    @characteristic("e946c454-6083-44d1-a726-076cecfc3744", CharFlags.READ)
    def measurement_info(self, options):
        if self.current_mac in self.sensors:
            start_time = self.sensors[self.current_mac]["run_at"]

            info = {
                "state": self.sensors[self.current_mac]["state"],
                "label": self.sensors[self.current_mac]["label"],
                "startTime": str(start_time.hour) + ":" + str(start_time.minute),
                "units": self.sensors[self.current_mac]["units"]
            }
        else:
            info = {
                "state": "empty",
                "label": "",
                "startTime": "",
                "units": []
            }
        json_list = json.dumps(info)
        data = bytes(json_list, "utf-8")
        return data

    @characteristic("1fbbda31-a97a-4d1d-a4dd-a7c17b853dcd", CharFlags.READ)
    def stop_measurement(self, options):
        mac = self.current_mac
        start = self.sensors[mac]["start_event"]
        end = self.sensors[mac]["end_event"]

        if self.sensors[mac]["state"] == "scheduled":
            self.scheduler.cancel(start)
            launch_disconnect(self.sensors[mac]["client"], self)

        self.scheduler.cancel(end)

        if self.sensors[mac]["state"] == "measuring":
            self.end_measurement(mac)

        return bytes("success", "utf-8")

