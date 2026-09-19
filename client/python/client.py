import os
import time
import requests
import secrets
import datetime

SERVER_HOSTNAME = os.environ["SERVER_HOSTNAME"]
SCORE_KEY_BYTES = 16
SYNC_INTERVAL = datetime.timedelta(seconds=10)
sync_key = ""
while True:
    score_key = secrets.token_urlsafe(SCORE_KEY_BYTES)
    response = requests.get(f"http://{SERVER_HOSTNAME}/sync?sync_key={sync_key}&score_key={score_key}")
    sync_key = response.text
    with open("/tmp/d-point", "w") as f:
        f.write(score_key)
    time.sleep(SYNC_INTERVAL.total_seconds())
