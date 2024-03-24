from datetime import datetime

from bt.sensor.supported.Movesense.timestamp_to_utf import TimestampConverter
from bt.sensor.utils.data_view import DataView

from rich import print


class NotificationHandler:
    timestamp_converter = TimestampConverter()

    async def notification_handler_picker(self, _, data, data_storage, state, service, sensor):
        """Notification handler for one of IMU sensors"""
        d = DataView(data)
        if sensor == "ecg":
            await self.notification_handler_ecg(_, d, data_storage, state, service)
        elif sensor == "hr":
            await self.notification_handler_hr(_, d, data_storage, state, service)
        else:
            await self.notification_handler_imu(_, d, data_storage, state, service, sensor)

    async def notification_handler_imu(self, _, dv, data_storage, state, service, sensor):
        """Notification handler for one of IMU sensors"""
        samples = 8
        probing_frequency = 52
        diff = (probing_frequency // samples)

        val = []

        # Dig data from the binary
        timestamp = dv.get_uint_32(0)
        converted_timestamp = self.timestamp_converter.convert_timestamp(timestamp)

        for i in range(0, samples):
            imu_val = []
            for j in range(0, 9):
                imu_val.append(dv.get_int_16(4 + i * 18 + (j * 2)))
            # Adding data to dataframe for later saving
            val.append(imu_val)
            data_storage.append([converted_timestamp + (diff * i), val[i]])

        service.update_progress({"state": "measuring", "info": "test"})

        if state["verbose"]:
            msg = ("timestamp: [bright_cyan]{}[/bright_cyan], xyz [blue]{}[/blue]"
                   .format(converted_timestamp, imu_val[0][0:3]))
            print(msg)

    async def notification_handler_ecg(self, _, dv, data_storage, state, service):
        """Simple notification handler for ECG sensor"""
        val = []
        samples = 16
        probing_frequency = 250
        diff = (probing_frequency // samples)

        # Dig data from the binary
        timestamp = dv.get_uint_32(0)
        converted_timestamp = self.timestamp_converter.convert_timestamp(timestamp)

        info_string = "ecg" + str(converted_timestamp)

        for i in range(0, samples):
            val.append(dv.get_int_16(4 + 2 * i))
            # Adding data to dataframe for later saving
            data_storage.append([converted_timestamp + (diff * i), val[i]])
            info_string += ',ecg' + str(val[i])

        service.update_progress({"state": "measuring", "info": info_string})

        if state["verbose"]:
            msg = "timestamp: [bright_cyan]{}[/bright_cyan], val: [blue]{}[/blue]".format(converted_timestamp, val)
            print(msg)

    async def notification_handler_hr(self, _, dv, data_storage, state, service):
        """Simple notification handler for heartrate"""

        # Dig data from the binary
        hr = dv.get_uint_8(0)
        rr = dv.get_uint_16(1)

        timestamp = datetime.now().timestamp() * 1000

        service.update_progress({"state": "measuring", "info": "hr" + str(timestamp)
                                                               + ',' + "hr" + str(rr)})

        data_storage.append([timestamp, hr, rr])

        if state["verbose"]:
            msg = "timestamp: [bright_cyan]{}[/bright_cyan], rr: [blue]{}[/blue]".format(timestamp, rr)
            print(msg)
