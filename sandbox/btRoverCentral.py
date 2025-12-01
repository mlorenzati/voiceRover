import bluetooth
import time
from micropython import const
from machine import Pin

motorAB = Pin(10, Pin.OUT)
motorAA = Pin(11, Pin.OUT)
motorBB = Pin(12, Pin.OUT)
motorBA = Pin(13, Pin.OUT)

def stop():
    motorAB.value(0)
    motorAA.value(0)
    motorBB.value(0)
    motorBA.value(0)

def backward(duration):
    motorAB.value(0)
    motorAA.value(1)
    motorBB.value(1)
    motorBA.value(0)
    time.sleep(duration)
    stop()
     
def forward(duration):
    motorAB.value(1)
    motorAA.value(0)
    motorBB.value(0)
    motorBA.value(1)
    time.sleep(duration)
    stop()

def right(duration):
    motorAB.value(1)
    motorAA.value(0)
    motorBB.value(1)
    motorBA.value(0)
    time.sleep(duration)
    stop()
    
def left(duration):
    motorAB.value(0)
    motorAA.value(1)
    motorBB.value(0)
    motorBA.value(1)
    time.sleep(duration)
    stop()

stop()

# --- UUIDs ---
CTRL_SERVICE_UUID = bluetooth.UUID("12345678-1234-5678-1234-56789abcdef0")
CTRL_CHAR_UUID    = bluetooth.UUID("12345678-1234-5678-1234-56789abcdef1")

# Characteristic flags
FLAG = bluetooth.FLAG_READ | bluetooth.FLAG_WRITE | bluetooth.FLAG_NOTIFY

# --- Initialize BLE ---
ble = bluetooth.BLE()
ble.active(True)

# --- Register service ---
handles = ble.gatts_register_services((
    (CTRL_SERVICE_UUID, ((CTRL_CHAR_UUID, FLAG),)),
))
ctrl_handle = handles[0][0]

_IRQ_CENTRAL_CONNECT    = const(1)
_IRQ_CENTRAL_DISCONNECT = const(2)
_IRQ_GATTS_WRITE        = const(3)
_IRQ_GATTC_NOTIFY       = const(27)

# --- BLE IRQ callback ---
def bt_irq(event, data):
    if event == _IRQ_CENTRAL_CONNECT:
        conn_handle, addr_type, addr = data
        print("Central connected:", bytes(addr))
    elif event == _IRQ_CENTRAL_DISCONNECT:
        conn_handle, addr_type, addr = data
        print("Central disconnected")
        # Restart advertising so a new central can connect
        ble.gap_advertise(100_000, adv_data)
    elif event == _IRQ_GATTS_WRITE:
        conn_handle, attr_handle = data
        if attr_handle == ctrl_handle:
            value = ble.gatts_read(ctrl_handle)
            print("Received command:", value)
            value_str = value.decode('utf-8')
            if value_str=="fw":
                forward(1)
            elif value_str=="bw":
                backward(1)
            elif value_str=="le":
                left(1)
            elif value_str=="rt":
                right(1)
            else:
                print("Command unknown")
                stop()
                
    elif event == _IRQ_GATTC_NOTIFY:
        print("Notify:", data)
    else:
        print("Unknown event:", event)

ble.irq(bt_irq)

# --- Advertising ---
adv_name = b"PicoW-Peripheral"
adv_data = bytes([len(adv_name)+1, 0x09]) + adv_name  # Complete Local Name

ble.gap_advertise(100_000, adv_data)
print("Advertising as BLE Peripheral (GATT Server)...")

# --- Main loop ---
while True:
    time.sleep(1)


