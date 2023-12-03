import pandas as pd
import numpy as np
import requests
from rich import print
from gpiozero import LED
import os

dirname = os.path.dirname(__file__)
filename = os.path.join(dirname, 'token.txt')
f = open(filename, "r")
post_token = f.read()
f.close()
# API endpoint
url = "http://192.168.111.250:5000/new_measurement?token=" + post_token


def send_measurement(df: pd.DataFrame, label: str, sensor: str, wifi_led: LED):

    wifi_led.blink()
    payload = []

    for index, row in df.iterrows():

        time = 0
        fields = {}

        for key in row.keys():
            if key == "timestamp":
                time = row[key]
            else:
                if row[key].dtype == np.int64 or row[key].dtype == np.int32:
                    fields[key] = int(row[key])
                else:
                    fields[key] = row[key]

        entry = {
            "measurement": label,
            "tags": {
                "sensor": sensor
            },
            "fields": fields,
            "time": int(time)
        }

        payload.append(entry)

    response = requests.post(url, json=payload)
    print("Response", response.status_code)
    wifi_led.off()
