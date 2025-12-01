from machine import Pin
import time
import utime

lineInfra = Pin(16, Pin.IN)
trigger =   Pin(7, Pin.OUT)
echo =      Pin(6, Pin.IN)
distance =  0.0
process_distance = False
distance_time_start = 0

def echo_callback(pin):
    now = utime.ticks_us()
    duration = utime.ticks_diff(now, distance_time_start)
    distance = (duration / 2) / 29.1
    echo.irq(handler=None)
    process_distance = False

print("Line Infra Status")
while True:
    print(f"Infra: {lineInfra.value()}, distance: {distance}", end="\r")
    if not True:
        process_distance = True
        
        trigger.value(0)
        utime.sleep_us(2)
        trigger.value(1)
        utime.sleep_us(10)
        trigger.value(0)
        
        while echo.value() == 0:
            start = utime.ticks_us()
        
        while echo.value() == 1:
            end = utime.ticks_us()
        
        duration = utime.ticks_diff(end, start)
        distance = (duration / 2) / 29.1  # convert to cm
        
        
        #distance_time_start = utime.ticks_us()
        #echo.irq(trigger=machine.Pin.IRQ_FALLING, handler=echo_callback)
    #else:
        #now = utime.ticks_us()
        #duration = utime.ticks_diff(now, distance_time_start)
        #if duration > 24000:
         #   distance = 100000
         #   echo.irq(handler=None)
         #   process_distance = False
            
    time.sleep(0.1)

