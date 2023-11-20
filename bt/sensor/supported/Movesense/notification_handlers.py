from bt.sensor.utils.data_view import DataView


async def notification_handler_imu(_, data, df, state, service, sensor):
    """Notification handler for one of IMU sensors"""
    d = DataView(data)
    # Dig data from the binary
    timestamp = d.get_uint_32(2)
    x = d.get_float_32(6)
    y = d.get_float_32(10)
    z = d.get_float_32(14)

    # Adding data to dataframe for later saving
    df.loc[len(df)] = [timestamp, x, y, z]

    service.update_progress({"state": "measuring", "info": sensor + str(timestamp)
                                                           + ',' + sensor + str(x)
                                                           + ',' + sensor + str(y)
                                                           + ',' + sensor + str(z)})

    if state["verbose"]:
        msg = "timestamp: {}, x: {}, y: {}, z: {}".format(timestamp, x, y, z)
        print(msg)


async def notification_handler_ecg(_, data, df, state, service):
    """Simple notification handler for ECG sensor"""
    d = DataView(data)
    val = []
    samples = 16

    # Dig data from the binary
    timestamp = d.get_uint_32(2)
    for i in range(0, samples):
        val.append(d.get_int_32(6 + 4 * i))

    # Adding data to dataframe for later saving
    for i in range(0, 16):
        df.loc[len(df)] = [timestamp, val[i]]

    info_string = "ecg" + str(timestamp)
    for i in range(0, samples):
        info_string += ',ecg'+str(val[i])

    service.update_progress({"state": "measuring", "info": info_string})

    service.update_progress({"state": "measuring", "info": ''})

    if state["verbose"]:
        msg = "timestamp: {}, val: {}".format(timestamp, val)
        print(msg)
