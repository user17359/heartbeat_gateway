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

timeout = 180

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
        try:
            response = requests.post(url, json=payload, timeout=timeout)
            response.raise_for_status()
            wifi_led.on()
            print("Response [blue]" + str(response.status_code) + "[/blue]")
            return True
        except requests.exceptions.HTTPError as errh:
            print("[red]Http Error:[/red]", errh)
            return False
        except requests.exceptions.ConnectionError as errc:
            print("[red]Error Connecting:[/red]", errc)
            return False
        except requests.exceptions.Timeout as errt:
            print("[red]Timeout Error:[/red]", errt)
            return False
        except requests.exceptions.RequestException as err:
            print("[red]OOps: Something Else[/red]", err)
            return False

    else:
        print("[red]Server can't be reached[/red]")
        wifi_led.off()
