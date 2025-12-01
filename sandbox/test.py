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

def backward(durationMs):
    motorAB.value(0)
    motorAA.value(1)
    motorBB.value(1)
    motorBA.value(0)
    
    
def forward():
    motorAB.value(1)
    motorAA.value(0)
    motorBB.value(0)
    motorBA.value(1)
    
stop()