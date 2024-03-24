#!/usr/bin/env python3
from gpiozero import LED
from gpiozero import Button
import time
import sched
import typer
import asyncio
from rich import print

from bt.app.services.sensor_service import SensorService
from bt.app.services.event_service import EventService
from bt.app.services.connectivity_service import ConnectivityService

from bluez_peripheral.util import *
from bluez_peripheral.agent import NoIoAgent
from bluez_peripheral.gatt.service import ServiceCollection

from utils.advertiser import Advertiser

typer_app = typer.Typer()

bt_led = LED(17)
wifi_led = LED(27)
button = Button(22)

state = {"verbose": False}

is_advertisement_running = False


@typer_app.command()
def timed():
    print("Timed blank")


@typer_app.command()
def startup():
    asyncio.run(async_startup())


async def async_startup():
    asyncio.get_event_loop()

    scheduler = sched.scheduler(time.time, time.sleep)
    bus = await get_message_bus()
    adapter = await Adapter.get_first(bus)

    advertiser = Advertiser(bt_led, bus, adapter, scheduler)

    service_collection = ServiceCollection()

    event_service = EventService()
    service_collection.add_service(event_service)

    connectivity_service = ConnectivityService()
    service_collection.add_service(connectivity_service)

    sensor_service = SensorService(scheduler, bus, adapter, (bt_led, wifi_led))
    service_collection.add_service(sensor_service)

    await service_collection.register(bus)

    agent = NoIoAgent()
    await agent.register(bus)

    bt_led.on()
    wifi_led.on()
    button.when_released = advertiser.setup_connection

    await asyncio.sleep(0.5)
    bt_led.off()
    wifi_led.off()

    time_elapsed = 0
    try:
        while True:
            # Check if any scheduled event is due
            scheduler.run(False)
            await asyncio.sleep(5)
            time_elapsed = time_elapsed + 5

    except KeyboardInterrupt:
        print("Exiting :wave:")
        raise


if __name__ == '__main__':
    typer_app()
