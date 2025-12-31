#!/usr/bin/env python3
"""
Runs YOLOv8 object detection on webcam. Detects vehicles. Writes '1' to a shared file if detected, '0' otherwise.
Uses file writing to prevent read-errors in the main controller.
"""

import cv2
import time
import os
import tempfile
from ultralytics import YOLO

# Config
MODEL_PATH = "yolov8n.onnx"
SHARED_FILE_PATH = "/tmp/side_detected.txt"
CONFIDENCE_THRESHOLD = 0.45

# Class IDs for vehicles: 2=car, 3=motorcycle, 5=bus, 7=truck
VEHICLE_CLASSES = [2, 3, 5, 7, 46]

def write_status(detected):
    """
    Writes status to a temp file then moves it to final destination
    to ensure the main script never reads a half-written file.
    """
    content = "1" if detected else "0"

    # Write to a temp file first
    with tempfile.NamedTemporaryFile(mode='w', delete=False, dir='/tmp') as tmp:
        tmp.write(content)
        tmp.flush()
        os.fsync(tmp.fileno())
        tmp_name = tmp.name

    # Atomic move
    os.replace(tmp_name, SHARED_FILE_PATH)

def main():
    print(f"Loading model: {MODEL_PATH}...")
    try:
        model = YOLO(MODEL_PATH, task='detect')
    except Exception as e:
        print(f"Error loading model: {e}")
        print("Ensure yolov8n.onnx or yolov8n.pt exists.")
        return

    # Open webcam
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Error: Could not open webcam.")
        return

    cv2.namedWindow("YOLOv8 Detection", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("YOLOv8 Detection", 1280, 720)

    print("Starting detection loop. Press 'q' to quit.")

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                print("Failed to grab frame")
                break

            # Run inference
            results = model(frame, verbose=False, conf=CONFIDENCE_THRESHOLD)

            car_detected = False

            # Check results
            for result in results:
                for box in result.boxes:
                    cls_id = int(box.cls[0])
                    if cls_id in VEHICLE_CLASSES:
                        car_detected = True
                        break # Found at least one car

            # Update the shared file
            write_status(car_detected)

            # Visualize
            annotated_frame = results[0].plot()
            cv2.imshow("YOLOv8 Detection", annotated_frame)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

            # Small sleep to save resources
            time.sleep(0.1)

    except KeyboardInterrupt:
        print("\nStopping...")
    finally:
        cap.release()
        cv2.destroyAllWindows()
        # Clean up file on exit so lights don't get stuck
        write_status(False)

if __name__ == "__main__":
    main()
