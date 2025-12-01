import machine, time
 
# pines "echo" y "trigger" para la interfaz con el sensor
pinecho = machine.Pin(6, machine.Pin.IN)
pintrig = machine.Pin(7, machine.Pin.OUT)
 
# Definir una función que realiza la medición de distancia con el sensor ultrasónico
# y retorna el resultado al código que la llama.
def read_ultrasonic():
    # esperar un poco antes de enviar el pulso de disparo
    pintrig(0)
    time.sleep_us(10)
    # enviar pulso de disparo de 10 uS
    pintrig(1)
    time.sleep_us(10)
    pintrig(0)
    
    # a continuación mediremos el puso de eco
    # esperamos mientras comienza el pulso alto
    while pinecho() == 0:
        pass
    # almacenar en una variable el tiempo en el que inicia el pulso en el pin "echo"
    toff = time.ticks_us()
    
    # esperamos mientras el pulso está en nivel alto
    while pinecho() == 1:
        pass
    # almacenar en una variable el tiempo en el que termina el pulso en el pin "echo"
    ton = time.ticks_us()
        
    # calcular la duración del pulso de eco
    elapsedtime = ton - toff
    
    # calcular la distancia en centímetros
    dist = elapsedtime / 58
    
    # devolvemos la distancia que acabamos de calcular dentro de la función
    return dist
 
while True:
    # llamamos a la función de medición
    distance = read_ultrasonic()
    # imprimimos la distancia
    print(f'Distancia medida: {distance} cm')
    # esperamos un segundo
    time.sleep(1)