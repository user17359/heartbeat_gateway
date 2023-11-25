import pandas as pd
import requests
from rich import print

# API endpoint
url = "http://192.168.111.250:5000/new_measurement"


def send_measurement(df: pd.DataFrame, label: str, sensor: str):

    payload = []

    for index, row in df.iterrows():

        time = 0
        fields = {}

        for key in row.keys():
            if key == "timestamp":
                time = row[key]
            else:
                fields[key] = row[key]

        entry = {
            "measurement": label,
            "tags": {
                "sensor": sensor
            },
            "fields": fields,
            "time": time
        }

        payload.append(entry)

    response = requests.post(url, json=payload)
    print("Response", response.status_code)
