import pandas as pd
import typer
import asyncio
from rich import print
from typing_extensions import Annotated

from bluetooth.sensor.scan_sensor import scan_sensor
from bluetooth.sensor.timed_connection import timed_connection
from data.avaiable_sensors import sensor_options

app = typer.Typer()

df = pd.DataFrame

state = {"verbose": False}


def bad_sensor_callback(value: str):
    if value not in sensor_options:
        raise typer.BadParameter("Invalid sensor")
    return value


@app.command()
def app(
        connection_time: float,
        sensor: Annotated[
            str, typer.Option(help="Sensor from which data will be registered.", prompt="Choose sensor (acc/gyro/mag/ecg)",
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
    asyncio.run(async_app(connection_time, sensor))
    df.to_csv('result.csv', index=False)
    print("Data saved to [blue]results.csv[blue] :floppy_disk:")


async def async_app(time, sensor):
    address = await scan_sensor()
    if address is not None:
        await timed_connection(address, time, sensor, df, state)


if __name__ == '__main__':
    typer.run(app)
