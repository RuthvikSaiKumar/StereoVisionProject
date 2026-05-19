# import cv2
# import numpy as np
# import matplotlib.pyplot as plt

# LEFT_CAM_INDEX = 2
# RIGHT_CAM_INDEX = 4

# CAM_WIDTH = 640
# CAM_HEIGHT = 480

# BASELINE = 0.102  # meters

# # TODO:real value should come from calibration
# FOCAL_LENGTH = 700


# # -----------------------------------
# # Open Cameras
# # -----------------------------------

# left_cam = cv2.VideoCapture(LEFT_CAM_INDEX, cv2.CAP_V4L2)
# right_cam = cv2.VideoCapture(RIGHT_CAM_INDEX, cv2.CAP_V4L2)

# for cam in [left_cam, right_cam]:
#     cam.set(cv2.CAP_PROP_FRAME_WIDTH, CAM_WIDTH)
#     cam.set(cv2.CAP_PROP_FRAME_HEIGHT, CAM_HEIGHT)
#     cam.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))

# if not left_cam.isOpened():
#     print("Failed to open LEFT camera")
#     exit()

# if not right_cam.isOpened():
#     print("Failed to open RIGHT camera")
#     exit()


# # -----------------------------------
# # Stereo Matcher
# # -----------------------------------

# stereo = cv2.StereoSGBM_create(
#     minDisparity=0,
#     numDisparities=16 * 8,
#     blockSize=11,
#     P1=8 * 3 * 11**2,
#     P2=32 * 3 * 11**2,
#     disp12MaxDiff=1,
#     uniquenessRatio=15,
#     speckleWindowSize=200,
#     speckleRange=64
# )


# # -----------------------------------
# # TODO: Q Matrix (demo only, get actual value from calibration)
# # -----------------------------------

# Q = np.float32([
#     [1, 0, 0, -CAM_WIDTH / 2],
#     [0, -1, 0, CAM_HEIGHT / 2],
#     [0, 0, 0, -FOCAL_LENGTH],
#     [0, 0, 1 / BASELINE, 0]
# ])


# print("Press SPACE to capture and show point cloud")
# print("Press Q to quit")


# # -----------------------------------
# # Main Loop
# # -----------------------------------

# while True:
#     ret_left, frame_left = left_cam.read()
#     ret_right, frame_right = right_cam.read()

#     if not ret_left or not ret_right:
#         print("Failed to grab frames")
#         break

#     gray_left = cv2.cvtColor(frame_left, cv2.COLOR_BGR2GRAY)
#     gray_right = cv2.cvtColor(frame_right, cv2.COLOR_BGR2GRAY)

#     gray_left = cv2.GaussianBlur(gray_left, (3, 3), 0)
#     gray_right = cv2.GaussianBlur(gray_right, (3, 3), 0)

#     disparity = stereo.compute(
#         gray_left,
#         gray_right
#     ).astype(np.float32) / 16.0

#     disp_display = cv2.normalize(
#         disparity,
#         None,
#         alpha=0,
#         beta=255,
#         norm_type=cv2.NORM_MINMAX
#     )

#     disp_display = np.uint8(disp_display)

#     cv2.imshow("Disparity Preview", disp_display)

#     key = cv2.waitKey(1) & 0xFF

#     # SPACE = capture point cloud
#     if key == 32:
#         print("Generating point cloud...")

#         points_3D = cv2.reprojectImageTo3D(
#             disparity,
#             Q
#         )

#         mask = disparity > 5  # remove invalid / noisy points

#         output_points = points_3D[mask]
#         output_colors = frame_left[mask]

#         # Reduce number of points for plotting speed
#         if len(output_points) > 10000:
#             idx = np.random.choice(
#                 len(output_points),
#                 10000,
#                 replace=False
#             )
#             output_points = output_points[idx]
#             output_colors = output_colors[idx]

#         colors_rgb = output_colors[:, ::-1] / 255.0

#         print(f"Displaying {len(output_points)} points")

#         fig = plt.figure(figsize=(10, 8))
#         ax = fig.add_subplot(111, projection='3d')

#         ax.scatter(
#             output_points[:, 0],
#             output_points[:, 1],
#             output_points[:, 2],
#             c=colors_rgb,
#             s=1
#         )

#         ax.set_title("Stereo Point Cloud")
#         ax.set_xlabel("X")
#         ax.set_ylabel("Y")
#         ax.set_zlabel("Z")

#         plt.show()

#     elif key == ord("q"):
#         break


# left_cam.release()
# right_cam.release()
# cv2.destroyAllWindows()

import cv2
import numpy as np
import matplotlib.pyplot as plt
import os

LEFT_CAM_INDEX = 2
RIGHT_CAM_INDEX = 4
CAM_WIDTH = 640
CAM_HEIGHT = 480

# -----------------------------------
# Load Calibration Data
# -----------------------------------
calib_file = '../calibration/data/stereo_calib.npz'
if not os.path.exists(calib_file):
    print(f"Error: {calib_file} not found. Ensure the path is correct.")
    exit()

calib = np.load(calib_file)
K1, D1 = calib['K1'], calib['D1']
K2, D2 = calib['K2'], calib['D2']
R1, R2 = calib['R1'], calib['R2']
P1, P2 = calib['P1'], calib['P2']
Q = calib['Q']

# Compute rectification maps once at startup
img_size = (CAM_WIDTH, CAM_HEIGHT)
left_map1, left_map2 = cv2.initUndistortRectifyMap(K1, D1, R1, P1, img_size, cv2.CV_16SC2)
right_map1, right_map2 = cv2.initUndistortRectifyMap(K2, D2, R2, P2, img_size, cv2.CV_16SC2)

# -----------------------------------
# Setup Image Enhancement (CLAHE)
# -----------------------------------
clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))

# -----------------------------------
# Stereo Matcher & WLS Filter Setup
# -----------------------------------
window_size = 5
min_disp = 0
num_disp = 16 * 8 # Must be divisible by 16

# Left matcher
left_matcher = cv2.StereoSGBM_create(
    minDisparity=min_disp,
    numDisparities=num_disp,
    blockSize=window_size,
    P1=8 * 3 * window_size**2,
    P2=32 * 3 * window_size**2,
    disp12MaxDiff=1,
    uniquenessRatio=10,
    speckleWindowSize=100,
    speckleRange=32,
    mode=cv2.STEREO_SGBM_MODE_SGBM_3WAY
)

# Right matcher (required for WLS)
right_matcher = cv2.ximgproc.createRightMatcher(left_matcher)

# WLS Filter
wls_filter = cv2.ximgproc.createDisparityWLSFilter(matcher_left=left_matcher)
wls_filter.setLambda(80000)
wls_filter.setSigmaColor(1.5)

# -----------------------------------
# Open Cameras
# -----------------------------------
left_cam = cv2.VideoCapture(LEFT_CAM_INDEX, cv2.CAP_V4L2)
right_cam = cv2.VideoCapture(RIGHT_CAM_INDEX, cv2.CAP_V4L2)

for cam in [left_cam, right_cam]:
    cam.set(cv2.CAP_PROP_FRAME_WIDTH, CAM_WIDTH)
    cam.set(cv2.CAP_PROP_FRAME_HEIGHT, CAM_HEIGHT)
    cam.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))

if not left_cam.isOpened() or not right_cam.isOpened():
    print("Failed to open cameras")
    exit()

print("Press SPACE to capture and show point cloud")
print("Press Q to quit")

# -----------------------------------
# Main Loop
# -----------------------------------
while True:
    ret_left, frame_left = left_cam.read()
    ret_right, frame_right = right_cam.read()

    if not ret_left or not ret_right:
        print("Failed to grab frames")
        break

    # 1. Rectify frames using the calibration maps
    rect_left = cv2.remap(frame_left, left_map1, left_map2, cv2.INTER_LINEAR)
    rect_right = cv2.remap(frame_right, right_map1, right_map2, cv2.INTER_LINEAR)

    # 2. Convert to Grayscale
    gray_left = cv2.cvtColor(rect_left, cv2.COLOR_BGR2GRAY)
    gray_right = cv2.cvtColor(rect_right, cv2.COLOR_BGR2GRAY)

    # 3. Apply CLAHE to boost local contrast/texture
    gray_left = clahe.apply(gray_left)
    gray_right = clahe.apply(gray_right)

    # Optional slight blur to reduce image noise before matching
    gray_left = cv2.GaussianBlur(gray_left, (3, 3), 0)
    gray_right = cv2.GaussianBlur(gray_right, (3, 3), 0)

    # 4. Compute Left and Right Disparities
    disp_left = left_matcher.compute(gray_left, gray_right)
    disp_right = right_matcher.compute(gray_right, gray_left)

    disp_left = np.int16(disp_left)
    disp_right = np.int16(disp_right)

    # 5. Apply WLS Filter
    filtered_disp = wls_filter.filter(disp_left, rect_left, None, disp_right)

    # Normalize for visual display
    disp_display = cv2.normalize(filtered_disp, None, alpha=0, beta=255, norm_type=cv2.NORM_MINMAX)
    disp_display = np.uint8(disp_display)

    cv2.imshow("Filtered Disparity Preview", disp_display)

    key = cv2.waitKey(1) & 0xFF

    if key == 32: # SPACE
        print("Generating point cloud...")

        # Convert WLS filtered disparity to float32 and scale down
        # OpenCV SGBM stores disparities scaled by 16.0
        disparity_float = filtered_disp.astype(np.float32) / 16.0

        # Reproject using the calibrated Q matrix
        points_3D = cv2.reprojectImageTo3D(disparity_float, Q)

        # Filter out invalid points (WLS marks highly uncertain areas with negative/zero disparity)
        mask = disparity_float > 0.0

        output_points = points_3D[mask]
        output_colors = rect_left[mask] # Use rectified color image

        # Downsample points for Matplotlib plotting speed
        if len(output_points) > 10000:
            idx = np.random.choice(len(output_points), 10000, replace=False)
            output_points = output_points[idx]
            output_colors = output_colors[idx]

        colors_rgb = output_colors[:, ::-1] / 255.0

        print(f"Displaying {len(output_points)} points")

        fig = plt.figure(figsize=(10, 8))
        ax = fig.add_subplot(111, projection='3d')

        ax.scatter(
            output_points[:, 0],
            output_points[:, 1],
            output_points[:, 2],
            c=colors_rgb,
            s=1
        )

        ax.set_title("Stereo Point Cloud (WLS + CLAHE)")
        ax.set_xlabel("X (meters)")
        ax.set_ylabel("Y (meters)")
        ax.set_zlabel("Z (meters)")
        
        # Invert Z and Y axes for proper viewing orientation
        ax.invert_zaxis()
        ax.invert_yaxis()

        plt.show()

    elif key == ord("q"):
        break

left_cam.release()
right_cam.release()
cv2.destroyAllWindows()