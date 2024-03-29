import pandas as pd
import numpy as np
import requests
from rich import print
from gpiozero import LED
import os
import socket

from server.address import server_address

dirname = os.path.dirname(__file__)
filename = os.path.join(dirname, 'token.txt')
f = open(filename, "r")
post_token = f.read()
f.close()
# API endpoint
url = "http://" + server_address + ":5000/new_measurement?token=" + post_token

timeout = 15

def send_measurement(df: list, header: list, label: str, sensor: str, wifi_led: LED):

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex((server_address, 5000))

    print("Finished connection checking")

    if result == 0:
        wifi_led.blink()
        payload = []

        for data_point in df:

            time = 0
            fields = {}

            i = 0
            for key in header:
                if key == "timestamp":
                    time = data_point[i]
                else:
                    fields[key] = data_point[i]
                i = i + 1

            entry = {
                "measurement": label,
                "tags": {
                    "sensor": sensor
                },
                "fields": fields,
                "time": int(time)
            }

            payload.append(entry)

        print("Posting data...")
        response = requests.post(url, json=payload, timeout=timeout)
        print("Response [blue]" + str(response.status_code) + "[/blue]")

        wifi_led.on()
    else:
        print("[red]Server can't be reached[/red]")
        wifi_led.off()
