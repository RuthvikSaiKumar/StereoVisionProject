import cv2
import os

LEFT_CAM_INDEX = 2
RIGHT_CAM_INDEX = 4
CAM_WIDTH = 640
CAM_HEIGHT = 480
SAVE_DIR = "./calib_images"

os.makedirs(f"{SAVE_DIR}/left", exist_ok=True)
os.makedirs(f"{SAVE_DIR}/right", exist_ok=True)

left_cam = cv2.VideoCapture(LEFT_CAM_INDEX, cv2.CAP_V4L2)
right_cam = cv2.VideoCapture(RIGHT_CAM_INDEX, cv2.CAP_V4L2)

for cam in [left_cam, right_cam]:
    cam.set(cv2.CAP_PROP_FRAME_WIDTH, CAM_WIDTH)
    cam.set(cv2.CAP_PROP_FRAME_HEIGHT, CAM_HEIGHT)
    cam.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))

if not left_cam.isOpened() or not right_cam.isOpened():
    print("Failed to open cameras.")
    exit()

# Count existing images so we don't overwrite
existing = len([f for f in os.listdir(f"{SAVE_DIR}/left") if f.endswith('.png')])
frame_count = existing
print(f"Found {existing} existing pairs. New captures will start from pair_{frame_count:03d}")
print()
print("Controls:")
print("  SPACE → capture pair")
print("  D     → delete last captured pair")
print("  Q     → quit")

last_saved = None

while True:
    ret_l, frame_l = left_cam.read()
    ret_r, frame_r = right_cam.read()

    if not ret_l or not ret_r:
        continue

    # Side-by-side preview
    preview = cv2.resize(
        cv2.hconcat([frame_l, frame_r]),
        (CAM_WIDTH * 2 // 2, CAM_HEIGHT // 2)  # half size for display
    )
    cv2.putText(preview, f"Pairs saved: {frame_count}  |  SPACE=capture  D=delete last  Q=quit",
                (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
    cv2.imshow("Stereo Capture (Left | Right)", preview)

    key = cv2.waitKey(1) & 0xFF

    if key == 32:  # SPACE — capture pair
        path_l = f"{SAVE_DIR}/left/pair_{frame_count:03d}.png"
        path_r = f"{SAVE_DIR}/right/pair_{frame_count:03d}.png"
        cv2.imwrite(path_l, frame_l)
        cv2.imwrite(path_r, frame_r)
        last_saved = frame_count
        frame_count += 1
        print(f"Saved pair_{(frame_count-1):03d}  (total: {frame_count})")

    elif key == ord('d'):  # D — delete last pair
        if last_saved is not None:
            path_l = f"{SAVE_DIR}/left/pair_{last_saved:03d}.png"
            path_r = f"{SAVE_DIR}/right/pair_{last_saved:03d}.png"
            for p in [path_l, path_r]:
                if os.path.exists(p):
                    os.remove(p)
            print(f"Deleted pair_{last_saved:03d}")
            frame_count -= 1
            last_saved = None
        else:
            print("Nothing to delete.")

    elif key == ord('q'):
        break

left_cam.release()
right_cam.release()
cv2.destroyAllWindows()
print(f"\nDone. {frame_count} pairs saved to {SAVE_DIR}/")