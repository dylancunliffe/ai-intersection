import Jetson.GPIO as GPIO
import time

PIN = 37  # jetson board pin number

GPIO.setmode(GPIO.BOARD)
GPIO.setup(PIN, GPIO.IN)

print("Press the button repeatedly\n")

try:
    while True:
        raw = GPIO.input(PIN)
        print("Raw:", raw)
        time.sleep(0.1)
except KeyboardInterrupt:
    GPIO.cleanup()
