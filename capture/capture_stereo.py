import cv2
import os

# =========================
# CONFIG
# =========================

LEFT_CAM_INDEX = 4
RIGHT_CAM_INDEX = 2

SAVE_PATH_LEFT = "images/left"
SAVE_PATH_RIGHT = "images/right"

WIDTH = 1280
HEIGHT = 720

# =========================
# SETUP
# =========================

os.makedirs(SAVE_PATH_LEFT, exist_ok=True)
os.makedirs(SAVE_PATH_RIGHT, exist_ok=True)

left_cam = cv2.VideoCapture(LEFT_CAM_INDEX)
right_cam = cv2.VideoCapture(RIGHT_CAM_INDEX)

if not left_cam.isOpened():
    print("Failed to open LEFT camera")
    exit()

if not right_cam.isOpened():
    print("Failed to open RIGHT camera")
    exit()

# Set resolution
left_cam.set(cv2.CAP_PROP_FRAME_WIDTH, WIDTH)
left_cam.set(cv2.CAP_PROP_FRAME_HEIGHT, HEIGHT)

right_cam.set(cv2.CAP_PROP_FRAME_WIDTH, WIDTH)
right_cam.set(cv2.CAP_PROP_FRAME_HEIGHT, HEIGHT)

print("===================================")
print("Stereo Capture Started")
print("SPACE  -> Save stereo pair")
print("Q      -> Quit")
print("===================================")

img_id = 0

# =========================
# MAIN LOOP
# =========================

while True:
    ret_left, frame_left = left_cam.read()
    ret_right, frame_right = right_cam.read()

    if not ret_left or not ret_right:
        print("Failed to grab frames")
        break

    # Add labels
    cv2.putText(
        frame_left,
        "LEFT CAMERA",
        (30, 50),
        cv2.FONT_HERSHEY_SIMPLEX,
        1,
        (0, 255, 0),
        2
    )

    cv2.putText(
        frame_right,
        "RIGHT CAMERA",
        (30, 50),
        cv2.FONT_HERSHEY_SIMPLEX,
        1,
        (0, 255, 0),
        2
    )

    # Show side by side preview
    combined = cv2.hconcat([frame_left, frame_right])

    cv2.imshow("Stereo Capture", combined)

    key = cv2.waitKey(1) & 0xFF

    # SPACE = save pair
    if key == 32:
        left_filename = os.path.join(
            SAVE_PATH_LEFT,
            f"left_{img_id:03d}.jpg"
        )

        right_filename = os.path.join(
            SAVE_PATH_RIGHT,
            f"right_{img_id:03d}.jpg"
        )

        cv2.imwrite(left_filename, frame_left)
        cv2.imwrite(right_filename, frame_right)

        print(f"Saved pair {img_id:03d}")

        img_id += 1

    # Q = quit
    elif key == ord("q"):
        print("Exiting...")
        break

# =========================
# CLEANUP
# =========================

left_cam.release()
right_cam.release()
cv2.destroyAllWindows()