import bluetooth
import time
from ble_advertising import advertising_payload

# Create a BLE instance
ble = bluetooth.BLE()
ble.active(True)

# Prepare advertising payload
payload = advertising_payload(name="pico-smars", services=[])

# Start advertising (interval in microseconds)
ble.gap_advertise(100_000, adv_data=payload)

print("Pico W is now advertising over BLE...")

while True:
    time.sleep(1)