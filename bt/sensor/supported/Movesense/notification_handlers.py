from datetime import datetime

from bt.sensor.supported.Movesense.timestamp_to_utf import TimestampConverter
from bt.sensor.utils.data_view import DataView

from rich import print


class NotificationHandler:
    timestamp_converter = TimestampConverter()

    async def notification_handler_imu(self, _, data, data_storage, state, service, sensor):
        """Notification handler for one of IMU sensors"""
        d = DataView(data)
        # Dig data from the binary
        timestamp = d.get_uint_32(2)
        x = d.get_float_32(6)
        y = d.get_float_32(10)
        z = d.get_float_32(14)

        converted_timestamp = self.timestamp_converter.convert_timestamp(timestamp)

        # Adding data to dataframe for later saving
        data_storage.append([converted_timestamp, x, y, z])

        service.update_progress({"state": "measuring", "info": sensor + str(converted_timestamp)
                                                               + ',' + sensor + str(x)
                                                               + ',' + sensor + str(y)
                                                               + ',' + sensor + str(z)})

        if state["verbose"]:
            msg = ("timestamp: [bright_cyan]{}[/bright_cyan], x: [blue]{}[/blue], y: [blue]{}[/blue], z: [blue]{}[/blue]"
                   .format(converted_timestamp, x, y, z))
            print(msg)

    async def notification_handler_ecg(self, _, data, data_storage, state, service):
        """Simple notification handler for ECG sensor"""
        d = DataView(data)
        val = []
        samples = 16
        probing_frequency = 128
        diff = (probing_frequency // samples)

        # Dig data from the binary
        timestamp = d.get_uint_32(2)
        converted_timestamp = self.timestamp_converter.convert_timestamp(timestamp)

        info_string = "ecg" + str(converted_timestamp)

        for i in range(0, samples):
            val.append(d.get_int_32(6 + 4 * i))
            # Adding data to dataframe for later saving
            data_storage.append([converted_timestamp + (diff * i), val[i]])
            info_string += ',ecg' + str(val[i])

        service.update_progress({"state": "measuring", "info": info_string})

        if state["verbose"]:
            msg = "timestamp: [bright_cyan]{}[/bright_cyan], val: [blue]{}[/blue]".format(converted_timestamp, val)
            print(msg)

    async def notification_handler_hr(self, _, data, data_storage, state, service):
        """Simple notification handler for heartrate"""
        d = DataView(data)

        # Dig data from the binary
        hr = d.get_float_32(2)
        rr = d.get_uint_16(6)

        timestamp = datetime.now().timestamp() * 1000

        service.update_progress({"state": "measuring", "info": "hr" + str(timestamp)
                                                               + ',' + "hr" + str(hr)
                                                               + ',' + "hr" + str(rr)})

        data_storage.append([timestamp, hr, rr])

        if state["verbose"]:
            msg = "timestamp: [bright_cyan]{}[/bright_cyan], hr: [blue]{}[/blue], rr: [blue]{}[/blue]".format(timestamp, hr, rr)
            print(msg)
