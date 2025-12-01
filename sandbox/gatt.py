import bluetooth
from micropython import const

ble = bluetooth.BLE()
ble.active(True)

CTRL_CHAR_UUID = bluetooth.UUID("12345678-1234-5678-1234-56789abcdef1")
CTRL_SERVICE_UUID = bluetooth.UUID("12345678-1234-5678-1234-56789abcdef0")
FLAG = bluetooth.FLAG_READ | bluetooth.FLAG_WRITE | bluetooth.FLAG_NOTIFY

# Register service
handles = ble.gatts_register_services((
    (CTRL_SERVICE_UUID, ((CTRL_CHAR_UUID, FLAG),)),
))
ctrl_handle = handles[0][0]

_IRQ_GATTC_NOTIFY = const(27)
_IRQ_GATTC_WRITE  = const(3)

# IRQ callback
def bt_irq(event, data):
    if event == _IRQ_GATTC_NOTIFY:  # MicroPython BLE constant
        print("Notify:", data)
    elif event == _IRQ_GATTC_WRITE:  # MicroPython BLE constant
        conn_handle, attr_handle = data  # unpack
        if attr_handle == ctrl_handle:
            value = ble.gatts_read(ctrl_handle)
            print("Received:", value)
    else:
        print("Unknown event type:", event)
    

ble.irq(bt_irq)

# Advertise
adv_name = b"PicoW-Controllee"
adv_data = bytes([len(adv_name)+1, 0x09]) + adv_name
ble.gap_advertise(100_000, adv_data)

print("Advertising...")