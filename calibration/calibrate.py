# import cv2
# import numpy as np

# LEFT_CAM_INDEX = 2
# RIGHT_CAM_INDEX = 4

# CAM_WIDTH = 640
# CAM_HEIGHT = 480

# # --- Board Parameters ---
# SQUARES_X = 9
# SQUARES_Y = 7
# SQUARE_LENGTH = 0.015  # 15mm in meters
# MARKER_LENGTH = 0.011  # 11mm in meters
# DICT_ID = cv2.aruco.DICT_4X4_250 # Using 250 as it contains the 50 subset

# # Setup ArUco Dictionary and Board
# aruco_dict = cv2.aruco.getPredefinedDictionary(DICT_ID)
# board = cv2.aruco.CharucoBoard((SQUARES_X, SQUARES_Y), SQUARE_LENGTH, MARKER_LENGTH, aruco_dict)

# # Modern OpenCV (4.7+) detector setup
# charuco_detector = cv2.aruco.CharucoDetector(board)

# # Open Cameras
# left_cam = cv2.VideoCapture(LEFT_CAM_INDEX, cv2.CAP_V4L2)
# right_cam = cv2.VideoCapture(RIGHT_CAM_INDEX, cv2.CAP_V4L2)

# for cam in [left_cam, right_cam]:
#     cam.set(cv2.CAP_PROP_FRAME_WIDTH, CAM_WIDTH)
#     cam.set(cv2.CAP_PROP_FRAME_HEIGHT, CAM_HEIGHT)
#     cam.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))

# if not left_cam.isOpened() or not right_cam.isOpened():
#     print("Failed to open cameras.")
#     exit()

# # Arrays to hold object points and image points for calibration
# objpoints = []  
# imgpoints_left = [] 
# imgpoints_right = []

# # Get the 3D coordinates of the board corners
# board_obj_points = board.getChessboardCorners()

# print("Press SPACE to capture a calibration frame.")
# print("Press ENTER to compute calibration and save.")
# print("Press Q to quit.")

# captured_frames = 0

# while True:
#     ret_l, frame_l = left_cam.read()
#     ret_r, frame_r = right_cam.read()

#     if not ret_l or not ret_r:
#         continue

#     gray_l = cv2.cvtColor(frame_l, cv2.COLOR_BGR2GRAY)
#     gray_r = cv2.cvtColor(frame_r, cv2.COLOR_BGR2GRAY)

#     # Detect ChArUco corners
#     charuco_corners_l, charuco_ids_l, _, _ = charuco_detector.detectBoard(gray_l)
#     charuco_corners_r, charuco_ids_r, _, _ = charuco_detector.detectBoard(gray_r)

#     display_l = frame_l.copy()
#     display_r = frame_r.copy()

#     # Draw detected corners for visual feedback
#     if charuco_ids_l is not None:
#         cv2.aruco.drawDetectedCornersCharuco(display_l, charuco_corners_l, charuco_ids_l)
#     if charuco_ids_r is not None:
#         cv2.aruco.drawDetectedCornersCharuco(display_r, charuco_corners_r, charuco_ids_r)

#     cv2.imshow("Left Camera Calibration", display_l)
#     cv2.imshow("Right Camera Calibration", display_r)

#     key = cv2.waitKey(1) & 0xFF

#     if key == 32: # SPACE
#         # Ensure we found corners in both images
#         if charuco_ids_l is not None and charuco_ids_r is not None:
#             # Find common corners seen by both cameras
#             common_ids, idx_l, idx_r = np.intersect1d(charuco_ids_l, charuco_ids_r, return_indices=True)
            
#             if len(common_ids) > 8: # Minimum threshold of shared corners
#                 frame_obj_points = []
#                 frame_img_points_l = []
#                 frame_img_points_r = []

#                 for i, cid in enumerate(common_ids):
#                     # Get the 3D point of this specific corner ID
#                     frame_obj_points.append(board_obj_points[cid])
#                     frame_img_points_l.append(charuco_corners_l[idx_l[i]])
#                     frame_img_points_r.append(charuco_corners_r[idx_r[i]])

#                 objpoints.append(np.array(frame_obj_points, dtype=np.float32))
#                 imgpoints_left.append(np.array(frame_img_points_l, dtype=np.float32))
#                 imgpoints_right.append(np.array(frame_img_points_r, dtype=np.float32))
                
#                 captured_frames += 1
#                 print(f"Captured frame {captured_frames}. Shared corners: {len(common_ids)}")
#             else:
#                 print("Not enough shared corners in this frame.")

#     # elif key == 13: # ENTER
#     #     if captured_frames < 5:
#     #         print("Not enough frames captured. Capture more before calibrating.")
#     #         continue
            
#     #     print("Calibrating... this may take a moment.")
        
#     #     # 1. Calibrate single cameras to get intrinsic guesses
#     #     img_size = gray_l.shape[::-1]
#     #     _, mtx_l, dist_l, _, _ = cv2.calibrateCamera(objpoints, imgpoints_left, img_size, None, None)
#     #     _, mtx_r, dist_r, _, _ = cv2.calibrateCamera(objpoints, imgpoints_right, img_size, None, None)

#     #     # 2. Stereo calibrate
#     #     flags = cv2.CALIB_FIX_INTRINSIC
#     #     criteria_stereo = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 100, 1e-5)
        
#     #     ret_stereo, K1, D1, K2, D2, R, T, E, F = cv2.stereoCalibrate(
#     #         objpoints, imgpoints_left, imgpoints_right,
#     #         mtx_l, dist_l, mtx_r, dist_r,
#     #         img_size, criteria=criteria_stereo, flags=flags)

#     #     # 3. Stereo Rectify to get Q matrix
#     #     R1, R2, P1, P2, Q, roi_left, roi_right = cv2.stereoRectify(
#     #         K1, D1, K2, D2, img_size, R, T, alpha=0)

#     #     # 4. Save data
#     #     np.savez('./data/stereo_calib.npz', 
#     #              K1=K1, D1=D1, K2=K2, D2=D2, 
#     #              R=R, T=T, R1=R1, R2=R2, P1=P1, P2=P2, Q=Q)
                 
#     #     print(f"Calibration saved to stereo_calib.npz! RMS Error: {ret_stereo:.4f}")
#     #     break

#     # Replace your ENTER key block with this:

#     elif key == 13:
#         if captured_frames < 15:
#             print("Need more frames.")
#             continue

#         print("Calibrating...")
#         img_size = (CAM_WIDTH, CAM_HEIGHT)

#         # Use rational model to better handle lens distortion,
#         # but CONSTRAIN k3 to prevent it going wild
#         single_flags = (
#             cv2.CALIB_RATIONAL_MODEL |
#             cv2.CALIB_FIX_K3 |      # ← prevents the huge k3 you got
#             cv2.CALIB_FIX_K4 |
#             cv2.CALIB_FIX_K5
#         )

#         ret_l, mtx_l, dist_l, _, _ = cv2.calibrateCamera(
#             objpoints, imgpoints_left, img_size, None, None,
#             flags=single_flags
#         )
#         ret_r, mtx_r, dist_r, _, _ = cv2.calibrateCamera(
#             objpoints, imgpoints_right, img_size, None, None,
#             flags=single_flags
#         )

#         print(f"Left RMS: {ret_l:.4f}, Right RMS: {ret_r:.4f}")

#         # Stereo calibrate — let it refine intrinsics jointly
#         stereo_flags = (
#             cv2.CALIB_USE_INTRINSIC_GUESS |  # start from single-cam results
#             cv2.CALIB_FIX_K3 |               # still constrain k3
#             cv2.CALIB_FIX_K4 |
#             cv2.CALIB_FIX_K5
#         )

#         criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 200, 1e-6)

#         ret, K1, D1, K2, D2, R, T, E, F = cv2.stereoCalibrate(
#             objpoints, imgpoints_left, imgpoints_right,
#             mtx_l, dist_l, mtx_r, dist_r,
#             img_size,
#             criteria=criteria,
#             flags=stereo_flags
#         )

#         print(f"Stereo RMS: {ret:.4f}")  # aim for < 0.5, anything > 1.0 is bad

#         if ret > 1.0:
#             print("WARNING: RMS too high. Recapture more/better frames before using this.")

#         # alpha=0 crops to valid pixels only — cleaner for disparity
#         R1, R2, P1, P2, Q, roi_l, roi_r = cv2.stereoRectify(
#             K1, D1, K2, D2, img_size, R, T,
#             alpha=0,
#             flags=cv2.CALIB_ZERO_DISPARITY  # aligns principal points horizontally
#         )

#         np.savez('./data/stereo_calib.npz',
#                 K1=K1, D1=D1, K2=K2, D2=D2,
#                 R=R, T=T, R1=R1, R2=R2, P1=P1, P2=P2, Q=Q)

#         print(f"Saved! RMS={ret:.4f}")
#         break

#     elif key == ord('q'):
#         print("Exiting without saving.")
#         break

# left_cam.release()
# right_cam.release()
# cv2.destroyAllWindows()

import cv2
import numpy as np
import os
import glob

# --- Board Parameters (must match your physical board) ---
SQUARES_X = 9
SQUARES_Y = 7
SQUARE_LENGTH = 0.015   # meters
MARKER_LENGTH = 0.011   # meters
DICT_ID = cv2.aruco.DICT_4X4_250

IMAGE_DIR = "./calib_images"
OUTPUT_DIR = "./data"
CAM_WIDTH = 640
CAM_HEIGHT = 480
IMG_SIZE = (CAM_WIDTH, CAM_HEIGHT)

os.makedirs(OUTPUT_DIR, exist_ok=True)

# -----------------------------------
# Setup ChArUco board
# -----------------------------------
aruco_dict = cv2.aruco.getPredefinedDictionary(DICT_ID)
board = cv2.aruco.CharucoBoard(
    (SQUARES_X, SQUARES_Y), SQUARE_LENGTH, MARKER_LENGTH, aruco_dict
)
charuco_detector = cv2.aruco.CharucoDetector(board)
board_obj_points = board.getChessboardCorners()

# -----------------------------------
# Load image pairs
# -----------------------------------
left_images = sorted(glob.glob(f"{IMAGE_DIR}/left/pair_*.png"))
right_images = sorted(glob.glob(f"{IMAGE_DIR}/right/pair_*.png"))

if len(left_images) == 0:
    print(f"No images found in {IMAGE_DIR}/left/")
    exit()

if len(left_images) != len(right_images):
    print(f"Mismatch: {len(left_images)} left vs {len(right_images)} right images.")
    exit()

print(f"Found {len(left_images)} image pairs. Processing...")

# -----------------------------------
# Detect corners in all pairs
# -----------------------------------
objpoints = []
imgpoints_left = []
imgpoints_right = []
valid_pairs = []

for i, (path_l, path_r) in enumerate(zip(left_images, right_images)):
    img_l = cv2.imread(path_l)
    img_r = cv2.imread(path_r)

    gray_l = cv2.cvtColor(img_l, cv2.COLOR_BGR2GRAY)
    gray_r = cv2.cvtColor(img_r, cv2.COLOR_BGR2GRAY)

    corners_l, ids_l, _, _ = charuco_detector.detectBoard(gray_l)
    corners_r, ids_r, _, _ = charuco_detector.detectBoard(gray_r)

    if ids_l is None or ids_r is None:
        print(f"  pair_{i:03d}: SKIP — board not detected in one or both images")
        continue

    # Find corners seen by both cameras
    ids_l_flat = ids_l.flatten()
    ids_r_flat = ids_r.flatten()
    common_ids, idx_l, idx_r = np.intersect1d(ids_l_flat, ids_r_flat, return_indices=True)

    if len(common_ids) < 6:
        print(f"  pair_{i:03d}: SKIP — only {len(common_ids)} shared corners (need 6+)")
        continue

    obj_pts = board_obj_points[common_ids].astype(np.float32)
    img_pts_l = corners_l[idx_l].astype(np.float32)
    img_pts_r = corners_r[idx_r].astype(np.float32)

    objpoints.append(obj_pts)
    imgpoints_left.append(img_pts_l)
    imgpoints_right.append(img_pts_r)
    valid_pairs.append(i)
    print(f"  pair_{i:03d}: OK — {len(common_ids)} shared corners")

print(f"\n{len(valid_pairs)} valid pairs out of {len(left_images)} total.")

if len(valid_pairs) < 10:
    print("Not enough valid pairs (need at least 10). Capture more images.")
    exit()

# -----------------------------------
# Single camera calibration
# (constrain k3 to prevent blow-up)
# -----------------------------------
print("\nCalibrating individual cameras...")

single_flags = (
    cv2.CALIB_FIX_K3 |
    cv2.CALIB_FIX_K4 |
    cv2.CALIB_FIX_K5
)

ret_l, mtx_l, dist_l, _, _ = cv2.calibrateCamera(
    objpoints, imgpoints_left, IMG_SIZE, None, None, flags=single_flags
)
ret_r, mtx_r, dist_r, _, _ = cv2.calibrateCamera(
    objpoints, imgpoints_right, IMG_SIZE, None, None, flags=single_flags
)

print(f"  Left  camera RMS: {ret_l:.4f}px")
print(f"  Right camera RMS: {ret_r:.4f}px")

if ret_l > 1.0 or ret_r > 1.0:
    print("  WARNING: Single-cam RMS > 1.0px. Consider recapturing with better coverage.")

# -----------------------------------
# Stereo calibration
# -----------------------------------
print("\nRunning stereo calibration...")

stereo_flags = (
    cv2.CALIB_USE_INTRINSIC_GUESS |
    cv2.CALIB_FIX_K3 |
    cv2.CALIB_FIX_K4 |
    cv2.CALIB_FIX_K5
)

criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 200, 1e-6)

ret_stereo, K1, D1, K2, D2, R, T, E, F = cv2.stereoCalibrate(
    objpoints, imgpoints_left, imgpoints_right,
    mtx_l, dist_l, mtx_r, dist_r,
    IMG_SIZE,
    criteria=criteria,
    flags=stereo_flags
)

print(f"  Stereo RMS: {ret_stereo:.4f}px")

if ret_stereo > 0.5:
    print("  WARNING: Stereo RMS > 0.5px — disparity quality may suffer.")
if ret_stereo > 1.0:
    print("  CRITICAL: Stereo RMS > 1.0px — recapture recommended before using this calibration.")

# -----------------------------------
# Stereo rectification
# -----------------------------------
R1, R2, P1, P2, Q, roi_l, roi_r = cv2.stereoRectify(
    K1, D1, K2, D2, IMG_SIZE, R, T,
    alpha=0,                          # crop to valid pixels only
    flags=cv2.CALIB_ZERO_DISPARITY    # align principal points
)

print(f"\n  Baseline:       {abs(T[0,0])*100:.1f} cm")
print(f"  Focal length:   {P1[0,0]:.1f} px")
print(f"  Expected disp @ 0.5m: {P1[0,0]*abs(T[0,0])/0.5:.0f} px")
print(f"  Expected disp @ 1.0m: {P1[0,0]*abs(T[0,0])/1.0:.0f} px")
print(f"  Expected disp @ 2.0m: {P1[0,0]*abs(T[0,0])/2.0:.0f} px")

# -----------------------------------
# Save
# -----------------------------------
out_path = f"{OUTPUT_DIR}/stereo_calib.npz"
np.savez(out_path,
         K1=K1, D1=D1, K2=K2, D2=D2,
         R=R, T=T, R1=R1, R2=R2, P1=P1, P2=P2, Q=Q)

print(f"\nCalibration saved to {out_path}")

# -----------------------------------
# Visual verification — epipolar lines
# -----------------------------------
print("\nShowing rectified preview. Check that horizontal lines pass through matching features.")
print("Press any key to cycle through pairs, Q to quit.")

map_l1, map_l2 = cv2.initUndistortRectifyMap(K1, D1, R1, P1, IMG_SIZE, cv2.CV_16SC2)
map_r1, map_r2 = cv2.initUndistortRectifyMap(K2, D2, R2, P2, IMG_SIZE, cv2.CV_16SC2)

for i in valid_pairs[:5]:  # preview first 5 valid pairs
    img_l = cv2.imread(left_images[i])
    img_r = cv2.imread(right_images[i])

    rect_l = cv2.remap(img_l, map_l1, map_l2, cv2.INTER_LINEAR)
    rect_r = cv2.remap(img_r, map_r1, map_r2, cv2.INTER_LINEAR)

    combined = np.hstack([rect_l, rect_r])

    # Draw epipolar lines
    for y in range(0, CAM_HEIGHT, 30):
        cv2.line(combined, (0, y), (CAM_WIDTH * 2, y), (0, 255, 0), 1)

    cv2.putText(combined, f"Pair {i} — features should align on green lines",
                (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
    cv2.imshow("Epipolar Verification (Left | Right)", combined)

    key = cv2.waitKey(0) & 0xFF
    if key == ord('q'):
        break

cv2.destroyAllWindows()
print("Done.")