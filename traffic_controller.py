#!/usr/bin/env python3
import time
import os
import Jetson.GPIO as GPIO

# Pin config
PIN_MAIN_R = 15
PIN_MAIN_Y = 16
PIN_MAIN_G = 13

PIN_SIDE_R = 7
PIN_SIDE_Y = 11  
PIN_SIDE_G = 12 

PIN_BUTTON = 22

# Timing parameters
MIN_MAIN_GREEN   = 5.0  # Minimum time main stays green before it can change
MAIN_YELLOW_TIME = 2.0
ALL_RED_TIME     = 2.0  # Safety barrier: reg-green delay

# Side street timings
SIDE_PED_TIME    = 8.0  # Fixed duration if button pressed
SIDE_MIN_GREEN   = 4.0  # Minimum green for cars
SIDE_MAX_GREEN   = 15.0 # Absolute max time for side street

# Detection Tuning
SIDE_GAP_TIME    = 2.5  # How long car must be gone before light turns yellow
DETECTION_DELAY  = 1.0  # How long car must be seen before requesting light

# temporary file location for reading state of vehicles
YOLO_FLAG_PATH = "/tmp/side_detected.txt"

# gpio setup
GPIO.setmode(GPIO.BOARD)
GPIO.setwarnings(False)

output_pins = [PIN_MAIN_R, PIN_MAIN_Y, PIN_MAIN_G, PIN_SIDE_R, PIN_SIDE_Y, PIN_SIDE_G]
for p in output_pins:
    GPIO.setup(p, GPIO.OUT)
    GPIO.output(p, GPIO.LOW)

# Button setup
GPIO.setup(PIN_BUTTON, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

# Global flags
req_pedestrian = False 
req_car = False        

# Function to set all lights at once
def set_lights(mr, my, mg, sr, sy, sg):
    GPIO.output(PIN_MAIN_R, mr)
    GPIO.output(PIN_MAIN_Y, my)
    GPIO.output(PIN_MAIN_G, mg)
    GPIO.output(PIN_SIDE_R, sr)
    GPIO.output(PIN_SIDE_Y, sy)
    GPIO.output(PIN_SIDE_G, sg)

# Reads the shared file to see if object is currently visible
def read_yolo_car_present():
    if not os.path.exists(YOLO_FLAG_PATH):
        return False
    try:
        with open(YOLO_FLAG_PATH, "r") as f:
            val = f.read().strip()
            return val == "1"
    except (IOError, ValueError):
        return False

# Main loop
def main():
    global req_pedestrian, req_car
    
    state = "MAIN_GREEN"
    state_start_time = time.time()
    
    # Tracking variables for detection filtering
    car_first_seen_time = None 
    last_car_seen_time = 0.0   
    
    print("[INFO] Controller Started. Waiting for triggers...")
    set_lights(0, 0, 1, 1, 0, 0) # Start Main Green

    try:
        while True:
            now = time.time()
            time_in_state = now - state_start_time
            
            # Input processing
            
            # 1. Check Button
            if GPIO.input(PIN_BUTTON) == GPIO.HIGH:
                if not req_pedestrian:
                    print("[EVENT] Pedestrian Button Pressed")
                    req_pedestrian = True

            # 2. Check YOLO
            is_car_present = read_yolo_car_present()
            
            if is_car_present:
                # Always record the last time we saw it
                last_car_seen_time = now
                
                # Logic to trigger initial request
                if car_first_seen_time is None:
                    car_first_seen_time = now # Start confirm timer
                elif (now - car_first_seen_time) >= DETECTION_DELAY:
                    # Object has been stable for > DETECTION_DELAY
                    if not req_car and state == "MAIN_GREEN":
                        print("[EVENT] Object Confirmed (Stable Detection)")
                        req_car = True
            else:
                # Object lost, reset initial detection timer
                car_first_seen_time = None

            # State machine

            if state == "MAIN_GREEN":
                # Change if Request Exists and min green time satisfied
                if (req_pedestrian or req_car) and time_in_state >= MIN_MAIN_GREEN:
                    print(f"[STATE] Switching to MAIN_YELLOW. (Ped: {req_pedestrian}, Car: {req_car})")
                    state = "MAIN_YELLOW"
                    state_start_time = now
                    set_lights(0, 1, 0, 1, 0, 0)

            elif state == "MAIN_YELLOW":
                if time_in_state >= MAIN_YELLOW_TIME:
                    state = "ALL_RED_1"
                    state_start_time = now
                    set_lights(1, 0, 0, 1, 0, 0) # All Red

            elif state == "ALL_RED_1":
                # Safety barrier before side turns Green
                if time_in_state >= ALL_RED_TIME:
                    state = "SIDE_GREEN"
                    state_start_time = now
                    set_lights(1, 0, 0, 0, 0, 1)
                    print("[STATE] SIDE_GREEN")

            elif state == "SIDE_GREEN":
                time_to_close = False
                
                # Determine base minimum duration
                min_duration = SIDE_PED_TIME if req_pedestrian else SIDE_MIN_GREEN
                
                # Calculate gap logic
                time_since_last_car = now - last_car_seen_time
                
                # Hold the light if min time not met, or saw a car less than GAP_TIME ago
                hold_for_min_time = (time_in_state < min_duration)
                hold_for_car_gap  = (time_since_last_car < SIDE_GAP_TIME)
                
                # If neither hold condition is true, we can close
                if not hold_for_min_time and not hold_for_car_gap:
                    time_to_close = True

                # Max green safety override
                if time_in_state >= SIDE_MAX_GREEN:
                    print("[INFO] Max Green Reached - Forcing Change")
                    time_to_close = True

                if time_to_close:
                    print(f"[STATE] Switching to SIDE_YELLOW (Gap: {time_since_last_car:.1f}s)")
                    state = "SIDE_YELLOW"
                    state_start_time = now
                    set_lights(1, 0, 0, 0, 1, 0)
                    
                    # Reset requests
                    req_pedestrian = False
                    req_car = False

            elif state == "SIDE_YELLOW":
                if time_in_state >= MAIN_YELLOW_TIME:
                    state = "ALL_RED_2"
                    state_start_time = now
                    set_lights(1, 0, 0, 1, 0, 0) # All Red

            elif state == "ALL_RED_2":
                # Safety barrier before main turns green
                if time_in_state >= ALL_RED_TIME:
                    state = "MAIN_GREEN"
                    state_start_time = now
                    set_lights(0, 0, 1, 1, 0, 0)
                    print("[STATE] MAIN_GREEN (Idle)")

            time.sleep(0.05) 

    except KeyboardInterrupt:
        print("\n[INFO] Shutdown requested")
    finally:
        set_lights(0, 0, 0, 0, 0, 0)
        GPIO.cleanup()
        print("[INFO] Cleanup Complete")

if __name__ == "__main__":
    main()
