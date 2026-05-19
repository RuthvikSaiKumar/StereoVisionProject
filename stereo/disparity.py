import cv2
import numpy as np
import os

LEFT_CAM_INDEX = 2
RIGHT_CAM_INDEX = 4
CAM_WIDTH = 640
CAM_HEIGHT = 480

# -----------------------------------
# Load Calibration
# -----------------------------------
calib_file = '../calibration/data/stereo_calib.npz'
if not os.path.exists(calib_file):
    print(f"Error: {calib_file} not found.")
    exit()

calib = np.load(calib_file)
K1, D1 = calib['K1'], calib['D1']
K2, D2 = calib['K2'], calib['D2']
R1, R2 = calib['R1'], calib['R2']
P1, P2 = calib['P1'], calib['P2']
Q      = calib['Q']

img_size = (CAM_WIDTH, CAM_HEIGHT)
map_l1, map_l2 = cv2.initUndistortRectifyMap(K1, D1, R1, P1, img_size, cv2.CV_16SC2)
map_r1, map_r2 = cv2.initUndistortRectifyMap(K2, D2, R2, P2, img_size, cv2.CV_16SC2)

# Derived from calibration output
FOCAL_LENGTH = P1[0, 0]   # ~1013.5 px
BASELINE     = abs(calib['T'][0, 0])  # ~0.099 m

print(f"Focal length: {FOCAL_LENGTH:.1f}px  |  Baseline: {BASELINE*100:.1f}cm")

# Disparity range mapped to real depth:
#   depth = f * B / disparity
disp_min_depth = 0.3   # meters — anything closer is noise
disp_max_depth = 4.0   # meters — anything further is unreliable
DISP_MIN = FOCAL_LENGTH * BASELINE / disp_max_depth   # ~25px
DISP_MAX = FOCAL_LENGTH * BASELINE / disp_min_depth   # ~334px

# -----------------------------------
# CLAHE for local contrast enhancement
# -----------------------------------
clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))

# -----------------------------------
# Stereo Matcher
# -----------------------------------
num_disp    = 16 * 14    # 224 — covers down to ~0.45m
window_size = 7

left_matcher = cv2.StereoSGBM_create(
    minDisparity=0,
    numDisparities=num_disp,
    blockSize=window_size,
    P1=8  * 3 * window_size**2,
    P2=32 * 3 * window_size**2,
    disp12MaxDiff=2,
    uniquenessRatio=10,
    speckleWindowSize=100,
    speckleRange=32,
    mode=cv2.STEREO_SGBM_MODE_SGBM_3WAY
)

right_matcher = cv2.ximgproc.createRightMatcher(left_matcher)

wls_filter = cv2.ximgproc.createDisparityWLSFilter(matcher_left=left_matcher)
wls_filter.setLambda(8000)
wls_filter.setSigmaColor(1.5)

# -----------------------------------
# Open Cameras
# -----------------------------------
left_cam  = cv2.VideoCapture(LEFT_CAM_INDEX, cv2.CAP_V4L2)
right_cam = cv2.VideoCapture(RIGHT_CAM_INDEX, cv2.CAP_V4L2)

for cam in [left_cam, right_cam]:
    cam.set(cv2.CAP_PROP_FRAME_WIDTH,  CAM_WIDTH)
    cam.set(cv2.CAP_PROP_FRAME_HEIGHT, CAM_HEIGHT)
    cam.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))

if not left_cam.isOpened() or not right_cam.isOpened():
    print("Failed to open cameras.")
    exit()

# -----------------------------------
# Display modes
# MODES:
#   0 — disparity (jet colormap)
#   1 — depth in meters (jet colormap, clipped to 0.3–4.0m)
#   2 — epipolar check (rectified side-by-side with horizontal lines)
#   3 — raw rectified side-by-side
# -----------------------------------
MODE       = 0
MODE_NAMES = {
    0: "Disparity (jet)",
    1: "Depth map (meters)",
    2: "Epipolar check",
    3: "Rectified raw"
}

print()
print("Controls:")
print("  M — cycle display mode")
print("  Q — quit")
print()
print(f"Current mode: {MODE_NAMES[MODE]}")

while True:
    ret_l, frame_l = left_cam.read()
    ret_r, frame_r = right_cam.read()

    if not ret_l or not ret_r:
        print("Frame grab failed.")
        break

    # 1. Rectify
    rect_l = cv2.remap(frame_l, map_l1, map_l2, cv2.INTER_LINEAR)
    rect_r = cv2.remap(frame_r, map_r1, map_r2, cv2.INTER_LINEAR)

    # 2. Grayscale + CLAHE
    gray_l = clahe.apply(cv2.cvtColor(rect_l, cv2.COLOR_BGR2GRAY))
    gray_r = clahe.apply(cv2.cvtColor(rect_r, cv2.COLOR_BGR2GRAY))

    # 3. Slight blur to reduce noise before matching
    gray_l = cv2.GaussianBlur(gray_l, (3, 3), 0)
    gray_r = cv2.GaussianBlur(gray_r, (3, 3), 0)

    # 4. Compute disparities + WLS filter
    disp_l = np.int16(left_matcher.compute(gray_l, gray_r))
    disp_r = np.int16(right_matcher.compute(gray_r, gray_l))
    filtered = wls_filter.filter(disp_l, rect_l, None, disp_r).astype(np.float32) / 16.0

    # -----------------------------------
    # Build display frame based on mode
    # -----------------------------------
    if MODE == 0:
        # Disparity — normalize full range to 0-255
        valid = filtered > DISP_MIN
        disp_vis = np.zeros_like(filtered, dtype=np.uint8)
        disp_vis[valid] = np.clip(
            (filtered[valid] - DISP_MIN) / (DISP_MAX - DISP_MIN) * 255, 0, 255
        ).astype(np.uint8)
        output = cv2.applyColorMap(disp_vis, cv2.COLORMAP_JET)

    elif MODE == 1:
        # Depth map in meters
        depth = np.zeros_like(filtered)
        valid = filtered > DISP_MIN
        depth[valid] = FOCAL_LENGTH * BASELINE / filtered[valid]
        depth = np.clip(depth, disp_min_depth, disp_max_depth)

        # Normalize to 0-255 (near=hot, far=cool)
        depth_vis = ((depth - disp_min_depth) / (disp_max_depth - disp_min_depth) * 255).astype(np.uint8)
        depth_vis[~valid] = 0
        output = cv2.applyColorMap(depth_vis, cv2.COLORMAP_JET)

        # Overlay depth value at center pixel
        cx, cy = CAM_WIDTH // 2, CAM_HEIGHT // 2
        center_depth = depth[cy, cx]
        if center_depth > 0:
            cv2.circle(output, (cx, cy), 4, (255, 255, 255), -1)
            cv2.putText(output, f"{center_depth:.2f}m", (cx + 8, cy),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

    elif MODE == 2:
        # Epipolar check — side by side with horizontal lines
        output = np.hstack([rect_l, rect_r])
        for y in range(0, CAM_HEIGHT, 30):
            cv2.line(output, (0, y), (CAM_WIDTH * 2, y), (0, 255, 0), 1)

    elif MODE == 3:
        # Raw rectified side by side
        output = np.hstack([rect_l, rect_r])

    # Mode label
    cv2.putText(output, f"[M] {MODE_NAMES[MODE]}",
                (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

    cv2.imshow("Stereo Vision", output)

    key = cv2.waitKey(1) & 0xFF

    if key == ord('m'):
        MODE = (MODE + 1) % len(MODE_NAMES)
        print(f"Mode: {MODE_NAMES[MODE]}")

    elif key == ord('q'):
        break

left_cam.release()
right_cam.release()
cv2.destroyAllWindows()