from bt.sensor.supported.Movesense.timestamp_to_utf import TimestampConverter
from bt.sensor.utils.data_view import DataView

import asyncio


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
            msg = "timestamp: {}, x: {}, y: {}, z: {}".format(converted_timestamp, x, y, z)
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
            msg = "timestamp: {}, val: {}".format(converted_timestamp, val)
            print(msg)
