import cv2
import numpy as np
import os
import open3d as o3d

LEFT_CAM_INDEX = 2
RIGHT_CAM_INDEX = 4
CAM_WIDTH  = 640
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

FOCAL_LENGTH = P1[0, 0]
BASELINE     = abs(calib['T'][0, 0])

print(f"Focal: {FOCAL_LENGTH:.1f}px  Baseline: {BASELINE*100:.1f}cm")

clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))

# -----------------------------------
# Your tuned params
# -----------------------------------
# NEAR matcher
NEAR = dict(
    numDisparities    = 256,
    minDisparity      = 53,
    blockSize         = 5,
    uniquenessRatio   = 8,
    speckleWindowSize = 80,
    speckleRange      = 16,
    wls_lambda        = 5543,
    wls_sigma         = 1.6,
)

# FAR matcher
FAR = dict(
    numDisparities    = 128,
    minDisparity      = 0,
    blockSize         = 9,
    uniquenessRatio   = 10,
    speckleWindowSize = 150,
    speckleRange      = 2,
    wls_lambda        = 12000,
    wls_sigma         = 1.8,
)

BLEND_DISP  = 100   # crossover in px (~1.0m for your setup)
BLEND_WIDTH = 40

# Depth clipping
MIN_DEPTH = 0.3   # metres
MAX_DEPTH = 4.0


# -----------------------------------
# Matcher factory
# -----------------------------------
def make_matcher(p):
    block = p["blockSize"] if p["blockSize"] % 2 == 1 else p["blockSize"] + 1
    block = max(1, block)
    lm = cv2.StereoSGBM_create(
        minDisparity    = p["minDisparity"],
        numDisparities  = p["numDisparities"],
        blockSize       = block,
        P1              = 8  * 3 * block**2,
        P2              = 32 * 3 * block**2,
        disp12MaxDiff   = 2,
        uniquenessRatio = p["uniquenessRatio"],
        speckleWindowSize = p["speckleWindowSize"],
        speckleRange    = p["speckleRange"],
        mode            = cv2.STEREO_SGBM_MODE_SGBM_3WAY
    )
    rm  = cv2.ximgproc.createRightMatcher(lm)
    wls = cv2.ximgproc.createDisparityWLSFilter(matcher_left=lm)
    wls.setLambda(p["wls_lambda"])
    wls.setSigmaColor(p["wls_sigma"])
    return lm, rm, wls


def compute_disp(lm, rm, wls, gl, gr, rect_l):
    dl = np.int16(lm.compute(gl, gr))
    dr = np.int16(rm.compute(gr, gl))
    return wls.filter(dl, rect_l, None, dr).astype(np.float32) / 16.0


# -----------------------------------
# Blend two disparity maps
# -----------------------------------
def blend_disparities(disp_near, disp_far, min_disp_near):
    weight_near = 1.0 / (1.0 + np.exp(-(disp_near - BLEND_DISP) / max(1, BLEND_WIDTH)))
    weight_far  = 1.0 - weight_near

    valid_near  = disp_near > min_disp_near
    valid_far   = disp_far  > 0

    combined    = np.zeros_like(disp_near)
    both        = valid_near & valid_far
    combined[both]               = (weight_near[both] * disp_near[both] +
                                    weight_far[both]  * disp_far[both])
    combined[valid_near & ~valid_far] = disp_near[valid_near & ~valid_far]
    combined[valid_far & ~valid_near] = disp_far[valid_far & ~valid_near]
    return combined


# -----------------------------------
# Open3D live visualiser
# -----------------------------------
def make_point_cloud(points, colors):
    pcd = o3d.geometry.PointCloud()
    pcd.points = o3d.utility.Vector3dVector(points)
    pcd.colors = o3d.utility.Vector3dVector(colors)
    return pcd


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

# Build matchers once
near_lm, near_rm, near_wls = make_matcher(NEAR)
far_lm,  far_rm,  far_wls  = make_matcher(FAR)

# -----------------------------------
# Open3D visualiser setup
# -----------------------------------
vis = o3d.visualization.VisualizerWithKeyCallback()
vis.create_window("Live Point Cloud", width=1024, height=768)

opt = vis.get_render_option()
opt.background_color = np.array([0.1, 0.1, 0.1])
opt.point_size       = 2.0

pcd      = o3d.geometry.PointCloud()
geo_added = False

# Coordinate frame for reference
frame = o3d.geometry.TriangleMesh.create_coordinate_frame(size=0.3)
vis.add_geometry(frame)

print()
print("Controls:")
print("  SPACE  — capture point cloud from current frame")
print("  C      — clear point cloud")
print("  S      — save point cloud to .ply file")
print("  Q      — quit")
print()
print("Open3D window: mouse to rotate, scroll to zoom, right-drag to pan")


# -----------------------------------
# Disparity preview window state
# -----------------------------------
DISP_MIN_VIS = FOCAL_LENGTH * BASELINE / MAX_DEPTH
DISP_MAX_VIS = FOCAL_LENGTH * BASELINE / MIN_DEPTH

capture_flag = [False]
clear_flag   = [False]
save_flag    = [False]
quit_flag    = [False]


def process_frame(frame_l, frame_r):
    rect_l = cv2.remap(frame_l, map_l1, map_l2, cv2.INTER_LINEAR)
    rect_r = cv2.remap(frame_r, map_r1, map_r2, cv2.INTER_LINEAR)

    gray_l = clahe.apply(cv2.cvtColor(rect_l, cv2.COLOR_BGR2GRAY))
    gray_r = clahe.apply(cv2.cvtColor(rect_r, cv2.COLOR_BGR2GRAY))
    gray_l = cv2.GaussianBlur(gray_l, (3, 3), 0)
    gray_r = cv2.GaussianBlur(gray_r, (3, 3), 0)

    disp_near = compute_disp(near_lm, near_rm, near_wls, gray_l, gray_r, rect_l)
    disp_far  = compute_disp(far_lm,  far_rm,  far_wls,  gray_l, gray_r, rect_l)
    combined  = blend_disparities(disp_near, disp_far, NEAR["minDisparity"])

    return rect_l, combined


def disparity_to_pointcloud(disparity, color_img):
    """Reproject disparity to 3D, filter by depth, return (Nx3, Nx3) arrays."""
    points_3d = cv2.reprojectImageTo3D(disparity, Q)

    # Valid: disparity > 0 and depth within range
    depth = points_3d[:, :, 2]
    mask  = (disparity > 0) & (depth > MIN_DEPTH) & (depth < MAX_DEPTH)
    mask  &= np.isfinite(depth)

    pts    = points_3d[mask]
    colors = color_img[mask][:, ::-1].astype(np.float64) / 255.0  # BGR→RGB, 0-1

    return pts, colors


save_counter = [0]

while True:
    ret_l, frame_l = left_cam.read()
    ret_r, frame_r = right_cam.read()
    if not ret_l or not ret_r:
        continue

    rect_l, combined = process_frame(frame_l, frame_r)

    # Disparity preview
    valid   = combined > DISP_MIN_VIS
    vis_img = np.zeros((CAM_HEIGHT, CAM_WIDTH), dtype=np.uint8)
    vis_img[valid] = np.clip(
        (combined[valid] - DISP_MIN_VIS) / (DISP_MAX_VIS - DISP_MIN_VIS) * 255,
        0, 255
    ).astype(np.uint8)
    disp_preview = cv2.applyColorMap(vis_img, cv2.COLORMAP_JET)

    cv2.putText(disp_preview, "SPACE=capture  C=clear  S=save  Q=quit",
                (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 2)
    cv2.imshow("Disparity Preview", disp_preview)

    key = cv2.waitKey(1) & 0xFF

    if key == ord('q'):
        break

    elif key == 32:  # SPACE — capture
        print("Generating point cloud...")
        pts, cols = disparity_to_pointcloud(combined, rect_l)

        if len(pts) == 0:
            print("No valid points — try moving closer or adjusting lighting.")
        else:
            # Voxel downsample for performance
            temp = make_point_cloud(pts, cols)
            temp = temp.voxel_down_sample(voxel_size=0.005)  # 5mm voxels

            # Statistical outlier removal
            temp, _ = temp.remove_statistical_outlier(nb_neighbors=20, std_ratio=2.0)

            pcd.points = temp.points
            pcd.colors = temp.colors

            if not geo_added:
                vis.add_geometry(pcd)
                geo_added = True
            else:
                vis.update_geometry(pcd)

            vis.reset_view_point(True)
            print(f"  {len(pcd.points):,} points displayed.")

    elif key == ord('c'):  # clear
        pcd.clear()
        if geo_added:
            vis.update_geometry(pcd)
        print("Point cloud cleared.")

    elif key == ord('s'):  # save
        if len(pcd.points) == 0:
            print("Nothing to save — capture a frame first.")
        else:
            fname = f"pointcloud_{save_counter[0]:03d}.ply"
            o3d.io.write_point_cloud(fname, pcd)
            print(f"Saved {fname}  ({len(pcd.points):,} points)")
            save_counter[0] += 1

    # Tick Open3D window
    vis.poll_events()
    vis.update_renderer()

# Cleanup
left_cam.release()
right_cam.release()
cv2.destroyAllWindows()
vis.destroy_window()