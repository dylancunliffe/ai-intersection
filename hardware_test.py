import gpiod
import time
# pin setup

#gpio chip for jetson orin nano super
CHIP = "/dev/gpiochip4"

#led pins
SIDE_R = 100
SIDE_Y = 79
SIDE_G = 78

MAIN_R = 102
MAIN_Y = 103
MAIN_G = 105

# button pin
BUTTON = 77

LED_LINES = [SIDE_R, SIDE_Y, SIDE_G, MAIN_R, MAIN_Y, MAIN_G]

# init gpio
chip = gpiod.Chip(CHIP)


#outputs
leds = [chip.get_line(pin) for pin in LED_LINES]
for line in leds:
	line.request(consumer="led_test", type=gpiod.LINE_REQ_DIR_OUT, default_vals=[0])

# input with internal pull down disabled
btn = chip.get_line(BUTTON)
btn.request(consumer="button_test", type=gpiod.LINE_REQ_DIR_IN)


print("Starting LED Test...")
time.sleep(1)

# led test
for pin in zip(LED_LINES, leds):
	print(f"Testing LED on pin {pin} - ON")
	line.set_value(1)
	time.sleep(1)

	print(f"Testing LED on pin {pin} = OFF")
	line.set_value(0)
	time.sleep(0.3)

print("\nLED test complete.\n")

# button test
print("Starting button test.")
print("Press the button to see state changes...")
print("CTRL+C to exit.\n")

try:
	while True:
		val = btn.get_value()
		if val == 1:
			print("Button: Pressed")
		else:
			print("Button: not pressed")

		time.sleep(0.2)

except KeyboardInterrupt:
	print("\nExiting...")
