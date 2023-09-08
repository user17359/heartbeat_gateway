import pandas as pd
import typer
import asyncio
from bleak import BleakScanner, BleakClient
from rich import print
from typing_extensions import Annotated
from rich.progress import track

from data_view import DataView

app = typer.Typer()
name_key = "Movesense"

WRITE_CHARACTERISTIC_UUID = (
    "34800001-7185-4d5d-b431-630e7050e8f0"
)

NOTIFY_CHARACTERISTIC_UUID = (
    "34800002-7185-4d5d-b431-630e7050e8f0"
)

sensor_options = ["acc", "gyro", "mag"]

options_dict = {
    "acc": "/Meas/Acc/13",
    "gyro": "/Meas/Gyro/13",
    "mag": "/Meas/Magn/13"
}

df = pd.DataFrame(columns=["timestamp", "x", "y", "z"])

state = {"verbose": False}


def sensor_callback(value: str):
    if value not in sensor_options:
        raise typer.BadParameter("Invalid sensor")
    return value


@app.command()
def app(
        connection_time: float,
        sensor: Annotated[
            str, typer.Option(help="Sensor from which data will be registered.", prompt="Choose sensor (acc/gyro/mag)",
                              callback=sensor_callback)
        ],
        verbose: bool = False
):
    if verbose:
        state["verbose"] = True
    asyncio.run(async_app(connection_time, options_dict[sensor]))
    df.to_csv('result.csv', index=False)
    print("Data saved to [blue]results.csv[blue] :floppy_disk:")


async def async_app(time, sensor):
    address = await scan_sensor()
    if address is not None:
        await timed_connection(address, time, sensor)


async def notification_handler(sender, data):
    """Simple notification handler which prints the data received."""
    d = DataView(data)
    # Dig data from the binary
    timestamp = d.get_uint_32(2)
    x = d.get_float_32(6)
    y = d.get_float_32(10)
    z = d.get_float_32(14)

    df.loc[len(df)] = [timestamp, x, y, z]
    msg = "timestamp: {}, x: {}, y: {}, z: {}".format(timestamp, x, y, z)
    if state["verbose"]:
        print(msg)


async def scan_sensor():
    print("Scanning for :sparkles: BLE devices:sparkles: ")
    devices = await BleakScanner.discover(return_adv=True)
    for device, adv_data in devices.values():
        if adv_data.local_name is not None and name_key in adv_data.local_name:
            print("Found Movesense device :flushed:")
            return device.address


async def timed_connection(address, time, sensor):
    client = BleakClient(address)
    try:
        await client.connect()
        if state["verbose"]:
            print("Enabling notifications")
        await client.start_notify(NOTIFY_CHARACTERISTIC_UUID, notification_handler)
        if state["verbose"]:
            print("Subscribing datastream")
        await client.write_gatt_char(WRITE_CHARACTERISTIC_UUID,
                                     bytearray([1, 99]) + bytearray(sensor, "utf-8"), response=True)
        if state["verbose"]:
            await asyncio.sleep(time)
        else:
            for value in track(range(100), description="Listening... "):
                await asyncio.sleep(time / 100)

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


if __name__ == '__main__':
    typer.run(app)
