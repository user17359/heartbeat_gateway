import asyncio

from bleak import BleakClient
from rich import print

from bluez_peripheral.advert import Advertisement

from bt.sensor.supported.connection import Connection


def launch_timed(connection_type: Connection, df, state, client, service, units):
    asyncio.create_task(timed_connection(connection_type, df, state, client, service, units))


def launch_stop(connection_type: Connection, client, service):
    asyncio.create_task(stop_connection(connection_type, client, service))


def launch_disconnect(client, service):
    asyncio.create_task(disconnect_peripheral(client, service))


async def start_connection(address, bus, adapter):
    await asyncio.sleep(2)
    client = BleakClient(address)
    try:
        await client.connect()

        advert = Advertisement("Heartbeat 2809", ["180D"], 0x008D, 15)
        await advert.register(bus, adapter)

    except Exception as e:
        print('[red]' + repr(e) + '[red]')
    return client


async def timed_connection(connection_type: Connection, df, state, client, service, units):
    await connection_type.start_connection(df, state, client, service, units)


async def stop_connection(connection_type: Connection, client, service):
    await connection_type.stop_connection(client)
    await disconnect_peripheral(client, service)


async def disconnect_peripheral(client, service):
    await client.disconnect()
    print("Disconnected")
    service.update_progress({"state": "empty", "info": ""})
