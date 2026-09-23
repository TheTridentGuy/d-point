import os
import time
import requests
from datetime import timedelta
from ykman.device import list_all_devices
from yubikit.core.smartcard import SmartCardConnection
from yubikit.oath import OathSession


SERVER_HOSTNAME = os.environ["SERVER_HOSTNAME"]
OATH_CREDENTIAL_ID = b"d-point:d-point"
UPDATE_INTERVAL = timedelta(minutes=5)


device, info = list_all_devices([SmartCardConnection])[0]
print(f"Found YubiKey {info.version_name}: {info.serial}")
with device.open_connection(SmartCardConnection) as connection:
    oath = OathSession(connection)
    while True:
        with open("/tmp/d-point", "w") as f:
            response = requests.get(f"http://{SERVER_HOSTNAME}/nonce")
            assert response.status_code == 200
            f.write(oath.calculate(OATH_CREDENTIAL_ID, bytes.fromhex(response.text)).hex())
        time.sleep(UPDATE_INTERVAL.total_seconds())
