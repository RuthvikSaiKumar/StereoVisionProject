import cv2

LEFT_CAM_INDEX = 2
RIGHT_CAM_INDEX = 4

# Capture resolution from camera
CAM_WIDTH = 1280
CAM_HEIGHT = 720

# Display scale factor for preview window
DISPLAY_SCALE = 0.7  # change to 0.4 or 0.3 if still too big

left_cam = cv2.VideoCapture(LEFT_CAM_INDEX, cv2.CAP_V4L2)
right_cam = cv2.VideoCapture(RIGHT_CAM_INDEX, cv2.CAP_V4L2)

for cam in [left_cam, right_cam]:
    cam.set(cv2.CAP_PROP_FRAME_WIDTH, CAM_WIDTH)
    cam.set(cv2.CAP_PROP_FRAME_HEIGHT, CAM_HEIGHT)
    cam.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))

if not left_cam.isOpened():
    print("Failed to open LEFT camera")
    exit()

if not right_cam.isOpened():
    print("Failed to open RIGHT camera")
    exit()

print("Press Q to quit")

while True:
    ret_left, frame_left = left_cam.read()
    ret_right, frame_right = right_cam.read()

    if not ret_left or not ret_right:
        print("Failed to grab frames")
        break

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

    combined = cv2.hconcat([frame_left, frame_right])

    # Resize only for display, not capture
    display = cv2.resize(
        combined,
        None,
        fx=DISPLAY_SCALE,
        fy=DISPLAY_SCALE
    )

    cv2.imshow("Stereo Live View", display)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

left_cam.release()
right_cam.release()
cv2.destroyAllWindows()