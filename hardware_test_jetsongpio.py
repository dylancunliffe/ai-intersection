import os
os.environ["JETSON_MODEL_OVERRIDE"] = "JETSON_ORIN_NANO"

import Jetson.GPIO as GPIO
import time
# pin setup

#led pins
SIDE_R = 7
SIDE_Y = 11
SIDE_G = 12

MAIN_R = 15
MAIN_Y = 16
MAIN_G = 13

# button pin
BUTTON = 22

LED_PINS = [SIDE_R, SIDE_Y, SIDE_G, MAIN_R, MAIN_Y, MAIN_G]

# init gpio
GPIO.setmode(GPIO.BOARD)

#outputs
for pin in LED_PINS:
	GPIO.setup(pin, GPIO.OUT)
	GPIO.output(pin, GPIO.LOW)

# input with internal pull down disabled
GPIO.setup(BUTTON, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

print("Starting LED Test...")
time.sleep(1)

# led test
for pin in LED_PINS:
	print(f"Testing LED on pin {pin} - ON")
	GPIO.output(pin, GPIO.HIGH)
	time.sleep(1)

	print(f"Testing LED on pin {pin} = OFF")
	GPIO.output(pin, GPIO.LOW)
	time.sleep(0.3)

print("\nLED test complete.\n")

# button test
print("Starting button test.")
print("Press the button to see state changes...")
print("CTRL+C to exit.\n")

try:
	while True:
		state = GPIO.input(BUTTON)
		if state == GPIO.HIGH:
			print("Button: Pressed")
		else:
			print("Button: not pressed")

		time.sleep(0.2)

except KeyboardInterrupt:
	print("\nExiting...")

finally:
	GPIO.cleanup()
	print("GPIO cleaned up.")
