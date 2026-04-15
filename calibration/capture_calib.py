import cv2
import os
from utils.camera import StereoCamera

SAVE_PATH = "calibration/data/"
os.makedirs(SAVE_PATH, exist_ok=True)

cam = StereoCamera(0, 1)

count = 0

print("Press SPACE to capture, ESC to exit")

while True:
    frameL, frameR = cam.read()

    combined = cv2.hconcat([frameL, frameR])
    cv2.imshow("Stereo Capture", combined)

    key = cv2.waitKey(1)

    if key == 27:  # ESC
        break

    elif key == 32:  # SPACE
        # Save images
        cv2.imwrite(f"{SAVE_PATH}/left_{count:03d}.png", frameL)
        cv2.imwrite(f"{SAVE_PATH}/right_{count:03d}.png", frameR)

        print(f"Captured pair {count}")
        count += 1

cam.release()
cv2.destroyAllWindows()