#!/usr/bin/env python3
import time
import sched
# import pandas as pd
import typer
import asyncio
from rich import print
from typing_extensions import Annotated

from bt.gateway.services.sensor_service import SensorService
from bt.sensor.scan_sensor import scan_sensor
from bt.sensor.timed_connection import timed_connection, launch_timed
from bt.gateway.services.test_service import HeartRateService
from bt.gateway.services.connectivity_service import ConnectivityService
from data.avaiable_sensors import sensor_options

from bluez_peripheral.util import *
from bluez_peripheral.advert import Advertisement
from bluez_peripheral.agent import NoIoAgent
from bluez_peripheral.gatt.service import ServiceCollection

typer_app = typer.Typer()

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
    asyncio.run(async_timed(connection_time, sensor))
    print("Data saved to [blue]results.csv[blue] :floppy_disk:")


async def async_timed(duration, sensor):
    launch_timed("0C:8C:DC:39:F4:F0", duration, sensor, None, state)

    time_elapsed = 0

    while time_elapsed < 30:
        print("Current seconds " + str(time_elapsed))
        await asyncio.sleep(5)
        time_elapsed = time_elapsed + 5

@typer_app.command()
def debug():
    print("nyong")
    launch_timed("0C:8C:DC:39:F4:F0", 10.0, "acc", None, {"verbose": True})

@typer_app.command()
def startup():
    asyncio.run(async_startup())


async def async_startup():
    bus = await get_message_bus()
    adapter = await Adapter.get_first(bus)
    scheduler = sched.scheduler(time.time, time.sleep)

    service_collection = ServiceCollection()

    heart_rate_service = HeartRateService()
    service_collection.add_service(heart_rate_service)

    connectivity_service = ConnectivityService()
    service_collection.add_service(connectivity_service)

    sensor_service = SensorService(scheduler, bus, adapter)
    service_collection.add_service(sensor_service)

    await service_collection.register(bus)

    agent = NoIoAgent()
    await agent.register(bus)

    adv_time = 30

    print("Start of advertisement :loudspeaker:")
    advert = Advertisement("Heartbeat gateway 2809", ["180D"], 0x008D, adv_time)
    await advert.register(bus, adapter)
    time_elapsed = 0

    while True:
        # Update the heart rate.
        print("Current seconds " + str(time_elapsed))
        # Check if any scheduled event is due
        scheduler.run(False)
        # Handle dbus requests.
        await asyncio.sleep(5)
        time_elapsed = time_elapsed + 5
        if time_elapsed == adv_time:
            print("End of advertisement :no_entry_sign:")


if __name__ == '__main__':
    typer_app()
