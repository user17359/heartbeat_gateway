import asyncio

from bleak import BleakClient
from rich.progress import track

from data.avaiable_sensors import options_dict
from data.notification_handlers import notification_handler_ecg, notification_handler_imu

WRITE_CHARACTERISTIC_UUID = (
    "34800001-7185-4d5d-b431-630e7050e8f0"
)

NOTIFY_CHARACTERISTIC_UUID = (
    "34800002-7185-4d5d-b431-630e7050e8f0"
)


async def timed_connection(address, time, sensor, df, state):
    """Connecting to chosen sensor for a fixed amount of seconds"""
    client = BleakClient(address)
    try:
        await client.connect()
        if state["verbose"]:
            print("Enabling notifications")

        # choosing handler appropriate to received data
        if sensor == "ecg":
            async def handler(_, data): await notification_handler_ecg(_, data, df, state)
            await client.start_notify(NOTIFY_CHARACTERISTIC_UUID, handler)
        else:
            async def handler(_, data): await notification_handler_imu(_, data, df, state)
            await client.start_notify(NOTIFY_CHARACTERISTIC_UUID, handler)

        # sending message via GATT that we want to subscribe to chosen sensor
        if state["verbose"]:
            print("Subscribing datastream")
        await client.write_gatt_char(WRITE_CHARACTERISTIC_UUID,
                                     bytearray([1, 99]) + bytearray(options_dict[sensor], "utf-8"), response=True)

        # waiting for fixed time while data is received
        if state["verbose"]:
            await asyncio.sleep(time)
        else:
            for _ in track(range(100), description="Listening... "):
                await asyncio.sleep(time / 100)

        # ending subscription to leave clean state
        if state["verbose"]:
            print("Unsubscribe")
        await client.write_gatt_char(WRITE_CHARACTERISTIC_UUID, bytearray([2, 99]), response=True)
        if state["verbose"]:
            print("Stop notifications")
        await client.stop_notify(NOTIFY_CHARACTERISTIC_UUID)
    except Exception as e:
        print(e)
    finally:
        await client.disconnect()
