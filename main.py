#!/usr/bin/env python3
import numpy
import pandas as pd
import typer
import asyncio
from rich import print
from typing_extensions import Annotated

from bt.sensor.scan_sensor import scan_sensor
from bt.sensor.timed_connection import timed_connection
from bt.gateway.services.test_service import HeartRateService
from data.avaiable_sensors import sensor_options

from bluez_peripheral.util import *
from bluez_peripheral.advert import Advertisement
from bluez_peripheral.agent import NoIoAgent
from bluez_peripheral.gatt.service import ServiceCollection

typer_app = typer.Typer()

df = pd.DataFrame

state = {"verbose": False}


def bad_sensor_callback(value: str):
    if value not in sensor_options:
        raise typer.BadParameter("Invalid sensor")
    return value


@typer_app.command()
def timed(
        connection_time: float,
        sensor: Annotated[
            str, typer.Option(help="Sensor from which data will be registered.",
                              prompt="Choose sensor (acc/gyro/mag/ecg)",
                              callback=bad_sensor_callback)
        ],
        verbose: bool = False
):
    if verbose:
        state["verbose"] = True
    global df
    if sensor == "ecg":
        df = pd.DataFrame(columns=["timestamp", "val"])
    else:
        df = pd.DataFrame(columns=["timestamp", "x", "y", "z"])
    asyncio.run(async_timed(connection_time, sensor))
    df.to_csv('result.csv', index=False)
    print("Data saved to [blue]results.csv[blue] :floppy_disk:")


async def async_timed(time, sensor):
    address = await scan_sensor()
    if address is not None:
        await timed_connection(address, time, sensor, df, state)


@typer_app.command()
def startup():
    asyncio.run(async_startup())


async def async_startup():
    bus = await get_message_bus()

    service = HeartRateService()
    await service.register(bus)

    agent = NoIoAgent()
    await agent.register(bus)

    adapter = await Adapter.get_first(bus)

    print("Start of advertisement :loudspeaker:")
    advert = Advertisement("Heartbeat gateway 2809", ["180D"], 0x0000, 30)
    await advert.register(bus, adapter)

    for i in range(6):
        # Update the heart rate.
        service.update_heart_rate(120)
        # Handle dbus requests.
        await asyncio.sleep(5)


if __name__ == '__main__':
    typer_app()
