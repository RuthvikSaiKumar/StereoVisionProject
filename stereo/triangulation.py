import cv2
import numpy as np

LEFT_CAM_INDEX = 2
RIGHT_CAM_INDEX = 4

CAM_WIDTH = 640
CAM_HEIGHT = 480

# Your measured baseline
BASELINE = 0.102  # meters

# Approximate focal length (demo value, not calibrated)
FOCAL_LENGTH = 700

OUTPUT_FILE = "point_cloud.ply"


def write_ply(filename, verts, colors):
    verts = verts.reshape(-1, 3)
    colors = colors.reshape(-1, 3)

    mask = np.isfinite(verts).all(axis=1)
    verts = verts[mask]
    colors = colors[mask]

    with open(filename, "w") as f:
        f.write("ply\n")
        f.write("format ascii 1.0\n")
        f.write(f"element vertex {len(verts)}\n")
        f.write("property float x\n")
        f.write("property float y\n")
        f.write("property float z\n")
        f.write("property uchar red\n")
        f.write("property uchar green\n")
        f.write("property uchar blue\n")
        f.write("end_header\n")

        for v, c in zip(verts, colors):
            f.write(
                f"{v[0]} {v[1]} {v[2]} "
                f"{c[2]} {c[1]} {c[0]}\n"
            )


# -----------------------------
# Open cameras
# -----------------------------

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

print("Press SPACE to capture and save point cloud")
print("Press Q to quit")

# -----------------------------
# Stereo matcher
# -----------------------------

stereo = cv2.StereoSGBM_create(
    minDisparity=0,
    numDisparities=16 * 8,
    blockSize=11,
    P1=8 * 3 * 11**2,
    P2=32 * 3 * 11**2,
    disp12MaxDiff=1,
    uniquenessRatio=15,
    speckleWindowSize=200,
    speckleRange=64
)

# Fake Q matrix for quick demo
Q = np.float32([
    [1, 0, 0, -CAM_WIDTH / 2],
    [0, -1, 0, CAM_HEIGHT / 2],
    [0, 0, 0, -FOCAL_LENGTH],
    [0, 0, 1 / BASELINE, 0]
])

# -----------------------------
# Main loop
# -----------------------------

while True:
    ret_left, frame_left = left_cam.read()
    ret_right, frame_right = right_cam.read()

    if not ret_left or not ret_right:
        print("Failed to grab frames")
        break

    gray_left = cv2.cvtColor(frame_left, cv2.COLOR_BGR2GRAY)
    gray_right = cv2.cvtColor(frame_right, cv2.COLOR_BGR2GRAY)

    gray_left = cv2.GaussianBlur(gray_left, (5, 5), 0)
    gray_right = cv2.GaussianBlur(gray_right, (5, 5), 0)

    disparity = stereo.compute(
        gray_left,
        gray_right
    ).astype(np.float32) / 16.0

    disp_display = cv2.normalize(
        disparity,
        None,
        alpha=0,
        beta=255,
        norm_type=cv2.NORM_MINMAX
    )

    disp_display = np.uint8(disp_display)
    disp_display = cv2.medianBlur(disp_display, 5)

    cv2.imshow("Disparity Preview", disp_display)

    key = cv2.waitKey(1) & 0xFF

    # SPACE = save point cloud
    if key == 32:
        points_3D = cv2.reprojectImageTo3D(
            disparity,
            Q
        )

        mask = disparity > disparity.min()

        output_points = points_3D[mask]
        output_colors = frame_left[mask]

        write_ply(
            OUTPUT_FILE,
            output_points,
            output_colors
        )

        print(f"Point cloud saved as: {OUTPUT_FILE}")
        print("Open it in MeshLab or CloudCompare")

    elif key == ord("q"):
        break

left_cam.release()
right_cam.release()
cv2.destroyAllWindows()