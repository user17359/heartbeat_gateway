import asyncio

from bleak import BleakClient
from rich import print
from rich.progress import track

from data.avaiable_sensors import options_dict
from data.notification_handlers import notification_handler_ecg, notification_handler_imu

from bluez_peripheral.advert import Advertisement

WRITE_CHARACTERISTIC_UUID = (
    "34800001-7185-4d5d-b431-630e7050e8f0"
)

NOTIFY_CHARACTERISTIC_UUID = (
    "34800002-7185-4d5d-b431-630e7050e8f0"
)


def launch_timed(sensor, df, state, client):
    asyncio.create_task(timed_connection(sensor, df, state, client))


def launch_stop(client):
    asyncio.create_task(stop_connection(client))


async def start_connection(address, bus, adapter):
    await asyncio.sleep(2)
    client = BleakClient(address)
    try:
        await client.connect()

        advert = Advertisement("Heartbeat gateway 2809", ["180D"], 0x008D, 15)
        await advert.register(bus, adapter)

    except Exception as e:
        print('[red]' + repr(e) + '[red]')
    return client


async def timed_connection(sensor, df, state, client):
    """Connecting to chosen sensor for a fixed amount of seconds"""
    try:
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
    except Exception as e:
        print('[red]' + repr(e) + '[red]')


async def stop_connection(client):
    await client.write_gatt_char(WRITE_CHARACTERISTIC_UUID, bytearray([2, 99]), response=True)
    print("Unsubscribing")
    await client.stop_notify(NOTIFY_CHARACTERISTIC_UUID)
    print("Stopping notifications")
    await client.disconnect()
    print("Disconnected")
