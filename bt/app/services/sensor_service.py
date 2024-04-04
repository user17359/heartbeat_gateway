import pandas as pd
from datetime import datetime, timedelta

from rich import print

from bluez_peripheral.gatt.service import Service
from bluez_peripheral.gatt.characteristic import characteristic, CharacteristicFlags as CharFlags

import json

from bt.sensor.supported.connection import Connection
from bt.sensor.supported.connections_dict import possible_connections
from bt.sensor.timed_connection import launch_timed, start_connection, launch_stop, launch_disconnect
from server.send_measurement import send_measurement


class SensorService(Service):
    sensors = {}
    current_mac = ""
    transfer_interval = 60

    def __init__(self, scheduler, bus, adapter, leds):
        # Base 16 service UUID, This should be a primary service.
        super().__init__("a56f5e06-fd24-4ffe-906f-f82e916262bc", True)
        self.scheduler = scheduler
        self.bus = bus
        self.adapter = adapter
        self.bt_led = leds[0]
        self.wifi_led = leds[1]
        self.transfer_event = None

    # Function called to create connection with sensor
    async def start_connection(self, mac):
        print("Connecting with " + mac)
        self.update_progress({"state": "scheduled", "info": str(self.sensors[mac]["run_at"].hour) + ":" +
                                                            str(self.sensors[mac]["run_at"].minute)})
        return await start_connection(mac, self.bus, self.adapter)

    # Function called on time set as start of measurement
    def start_measurement(self, mac):
        print("Measuring for " + mac + "...")

        self.transfer_event = self.scheduler.enter(self.transfer_interval,
                                                   5,
                                                   self.data_transfer,
                                                   argument=(mac,))

        self.bt_led.on()

        launch_timed(
            connection_type=self.sensors[mac]["type"],
            units=self.sensors[mac]["units"],
            df=self.sensors[mac]["data_storage"],
            state={"verbose": False},
            client=self.sensors[mac]["client"],
            service=self)

    def data_transfer(self, mac):
        for unit in self.sensors[mac]["units"]:
            timestamp = datetime.now()
            print("TIMESTAMP", timestamp)
            print("Reading data")
            label = self.sensors[mac]["label"].replace(" ", "_") + '_' + unit["name"]
            data = self.sensors[mac]["data_storage"][unit["name"]]
            header = self.sensors[mac]["type"].get_df_header(unit["name"])
            print("Creating dataframe")
            # appending data to .csv file
            df = pd.DataFrame(data, columns=header)
            print("Saving to .csv")
            df.to_csv(label + '.csv', mode='a', header=False)
            print("Sending data to server")
            # sending measurement to server
            result = send_measurement(data, header, label, self.sensors[mac]["type"].encoded_name, self.wifi_led)
            if result:
                print("Cleaning data storage: [orange]" + str(len(self.sensors[mac]["data_storage"][unit["name"]])) + "[/orange] rows")
                self.sensors[mac]["data_storage"][unit["name"]].clear()
            else:
                print("Saving data for retry: [orange]" + str(len(self.sensors[mac]["data_storage"][unit["name"]])) + "[/orange] rows")

        self.transfer_event = self.scheduler.enter(self.transfer_interval,
                                                   5,
                                                   self.data_transfer,
                                                   argument=(mac,))

    # Function called on time set as end of measurement
    def end_measurement(self, mac):
        print("End of measurement for " + mac)
        self.bt_led.off()

        if self.transfer_event is not None:
            self.scheduler.cancel(self.transfer_event)

        launch_stop(
            self.sensors[mac]["type"],
            self.sensors[mac]["client"],
            self
        )

    # Characteristic called to set up a new measurement at given time
    @characteristic("18c7e933-73cf-4d47-9973-51a53f0fec4e", CharFlags.WRITE_WITHOUT_RESPONSE)
    async def new_measurement(self, options):
        pass

    @new_measurement.setter
    async def new_measurement(self, value, options):
        data = json.loads(value)

        mac = data["mac"]
        self.current_mac = mac

        units = data["sensors"]

        connection_type: Connection = possible_connections[data["type"]]

        run_at = datetime.fromtimestamp(data["startMilliseconds"] / 1000.0)

        end_at = datetime.fromtimestamp(data["endMilliseconds"] / 1000.0)

        print("Start and end timestamps: ")
        print(data["startMilliseconds"])
        print(data["endMilliseconds"])
        print("Start and end time: ")
        print(run_at)
        print(end_at)

        self.sensors[mac] = {"run_at": run_at,
                             "end_at": end_at,
                             "type": connection_type,
                             "start_event": None,
                             "end_event": None,
                             "data_storage": None,
                             "client": None,
                             "units": units,
                             "label": data['label'],
                             "state": "empty"}

        # Preparing connection with sensor
        client = await self.start_connection(mac)
        self.sensors[mac]["client"] = client

        # Scheduling start and end events
        start_event = self.scheduler.enterabs(run_at.timestamp(),
                                              10,
                                              self.start_measurement,
                                              argument=(mac,))
        end_event = self.scheduler.enterabs(end_at.timestamp(),
                                            10,
                                            self.end_measurement,
                                            argument=(mac,))

        # TODO: more than one connection
        data_storage = {}

        # creating empty .csv with appropriate names
        for unit in self.sensors[mac]["units"]:

            data_storage[unit["name"]] = []

            df = pd.DataFrame([], columns=self.sensors[mac]["type"].get_df_header(unit["name"]))
            label = self.sensors[mac]["label"].replace(" ", "_") + '_' + unit["name"]
            df.to_csv(label + '.csv', index=False)

        self.sensors[mac]["data_storage"] = data_storage

        self.sensors[mac]["start_event"] = start_event
        self.sensors[mac]["end_event"] = end_event

    # Called from this app to send notifications about changing measurement state and data (if present)
    @characteristic("46dff0ae-21e2-4e55-8b38-3ae249e23884", CharFlags.NOTIFY)
    def measurement_progress(self, options):
        pass

    def update_progress(self, state):
        json_string = json.dumps(state)
        self.sensors[self.current_mac]["state"] = state["state"]
        data = bytes(json_string, "utf-8")
        self.measurement_progress.changed(data)

    # Characteristic called by app to require data about sensor with certain MAC address
    @characteristic("2fd2ac39-1f6b-4d55-aa2b-3dd049420235", CharFlags.WRITE_WITHOUT_RESPONSE)
    def measurement_info_write(self, options):
        pass

    @measurement_info_write.setter
    async def measurement_info_write(self, value, options):
        string_value = value.decode("utf-8")
        print("Writing current mac: " + string_value)
        self.current_mac = string_value

    # TODO: figure out if it will be needed anymore

    # Characteristic called to get current measurement state (empty/scheduled/measuring)
    # @characteristic("e946c454-6083-44d1-a726-076cecfc3744", CharFlags.READ)
    # def measurement_info(self, options):
    #     print("Sending [bold green]measurement info[/bold green]")
    #     if self.current_mac in self.sensors:
    #         start_time = self.sensors[self.current_mac]["run_at"]
    #         print("MAC is set")
    #         info = {
    #             "state": self.sensors[self.current_mac]["state"],
    #             "label": self.sensors[self.current_mac]["label"],
    #             "startTime": "{:02d}:{:02d}".format(start_time.hour, start_time.minute),
    #             "units": self.sensors[self.current_mac]["units"]
    #         }
    #     else:
    #         print("MAC is not set")
    #         info = {
    #             "state": "empty",
    #             "label": "",
    #             "startTime": "",
    #             "units": []
    #         }
    #     json_list = json.dumps(info)
    #     data = bytes(json_list, "utf-8")
    #     return data

    # Characteristic called when user forces stopping measurement
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
