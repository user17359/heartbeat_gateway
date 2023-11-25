import requests

from datetime import datetime
from rich import print

from bt.app.data_classes.diary_entry import DiaryEntry

# API endpoint
url = "192.168.111.250:5000/new_entry"


def send_entry(entry: DiaryEntry):
    now = datetime.now()
    entry_time = datetime(now.year,
                         now.month,
                         now.day,
                         entry.hour,
                         entry.minute)
    payload = {"label": entry.label, "description": entry.description, "time": entry_time.timestamp()}
    response = requests.post(url, json=payload)
    print(response.status_code)
