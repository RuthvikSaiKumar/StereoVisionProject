# import cv2
# import numpy as np
# import os
# import tkinter as tk
# from tkinter import ttk
# import threading

# LEFT_CAM_INDEX = 2
# RIGHT_CAM_INDEX = 4
# CAM_WIDTH = 640
# CAM_HEIGHT = 480

# # -----------------------------------
# # Load Calibration
# # -----------------------------------
# calib_file = '../calibration/data/stereo_calib.npz'
# if not os.path.exists(calib_file):
#     print(f"Error: {calib_file} not found.")
#     exit()

# calib = np.load(calib_file)
# K1, D1 = calib['K1'], calib['D1']
# K2, D2 = calib['K2'], calib['D2']
# R1, R2 = calib['R1'], calib['R2']
# P1, P2 = calib['P1'], calib['P2']
# Q      = calib['Q']

# img_size = (CAM_WIDTH, CAM_HEIGHT)
# map_l1, map_l2 = cv2.initUndistortRectifyMap(K1, D1, R1, P1, img_size, cv2.CV_16SC2)
# map_r1, map_r2 = cv2.initUndistortRectifyMap(K2, D2, R2, P2, img_size, cv2.CV_16SC2)

# FOCAL_LENGTH = P1[0, 0]
# BASELINE     = abs(calib['T'][0, 0])
# DISP_MIN     = FOCAL_LENGTH * BASELINE / 4.0
# DISP_MAX     = FOCAL_LENGTH * BASELINE / 0.3

# clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))

# # -----------------------------------
# # Open Cameras
# # -----------------------------------
# left_cam  = cv2.VideoCapture(LEFT_CAM_INDEX, cv2.CAP_V4L2)
# right_cam = cv2.VideoCapture(RIGHT_CAM_INDEX, cv2.CAP_V4L2)

# for cam in [left_cam, right_cam]:
#     cam.set(cv2.CAP_PROP_FRAME_WIDTH,  CAM_WIDTH)
#     cam.set(cv2.CAP_PROP_FRAME_HEIGHT, CAM_HEIGHT)
#     cam.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))

# if not left_cam.isOpened() or not right_cam.isOpened():
#     print("Failed to open cameras.")
#     exit()

# # -----------------------------------
# # Shared state
# # -----------------------------------
# params = {
#     "num_disp_mult": 14,
#     "block_size":    7,
#     "uniqueness":    10,
#     "speckle_win":   100,
#     "speckle_range": 32,
#     "d12":           2,
#     "wls_lambda":    8000,
#     "wls_sigma":     15,   # stored x10, so 15 = 1.5
# }

# running = True


# # -----------------------------------
# # Camera thread
# # -----------------------------------
# def camera_loop():
#     while running:
#         ret_l, frame_l = left_cam.read()
#         ret_r, frame_r = right_cam.read()
#         if not ret_l or not ret_r:
#             continue

#         p     = dict(params)
#         block = p["block_size"]
#         if block % 2 == 0:
#             block += 1
#         block    = max(1, block)
#         num_disp = p["num_disp_mult"] * 16

#         rect_l = cv2.remap(frame_l, map_l1, map_l2, cv2.INTER_LINEAR)
#         rect_r = cv2.remap(frame_r, map_r1, map_r2, cv2.INTER_LINEAR)

#         gray_l = clahe.apply(cv2.cvtColor(rect_l, cv2.COLOR_BGR2GRAY))
#         gray_r = clahe.apply(cv2.cvtColor(rect_r, cv2.COLOR_BGR2GRAY))
#         gray_l = cv2.GaussianBlur(gray_l, (3, 3), 0)
#         gray_r = cv2.GaussianBlur(gray_r, (3, 3), 0)

#         left_matcher = cv2.StereoSGBM_create(
#             minDisparity=0,
#             numDisparities=num_disp,
#             blockSize=block,
#             P1=8  * 3 * block**2,
#             P2=32 * 3 * block**2,
#             disp12MaxDiff=p["d12"],
#             uniquenessRatio=p["uniqueness"],
#             speckleWindowSize=p["speckle_win"],
#             speckleRange=p["speckle_range"],
#             mode=cv2.STEREO_SGBM_MODE_SGBM_3WAY
#         )
#         right_matcher = cv2.ximgproc.createRightMatcher(left_matcher)

#         wls = cv2.ximgproc.createDisparityWLSFilter(matcher_left=left_matcher)
#         wls.setLambda(p["wls_lambda"])
#         wls.setSigmaColor(p["wls_sigma"] / 10.0)

#         disp_l   = np.int16(left_matcher.compute(gray_l, gray_r))
#         disp_r   = np.int16(right_matcher.compute(gray_r, gray_l))
#         filtered = wls.filter(disp_l, rect_l, None, disp_r).astype(np.float32) / 16.0

#         valid    = filtered > DISP_MIN
#         disp_vis = np.zeros_like(filtered, dtype=np.uint8)
#         disp_vis[valid] = np.clip(
#             (filtered[valid] - DISP_MIN) / (DISP_MAX - DISP_MIN) * 255, 0, 255
#         ).astype(np.uint8)
#         output = cv2.applyColorMap(disp_vis, cv2.COLORMAP_JET)

#         cv2.imshow("Disparity", output)
#         cv2.waitKey(1)

#     left_cam.release()
#     right_cam.release()
#     cv2.destroyAllWindows()


# # -----------------------------------
# # Tkinter UI
# # -----------------------------------
# def build_ui():
#     root = tk.Tk()
#     root.title("Disparity Tuner")
#     root.resizable(False, False)
#     root.configure(bg="#1e1e1e")

#     BG     = "#1e1e1e"
#     FG     = "#e0e0e0"
#     ACCENT = "#00aaff"
#     TRACK  = "#2e2e2e"
#     LABEL_W = 18
#     VAL_W   = 10

#     # Each row: (display label, param key, min, max, divisor, unit suffix)
#     SLIDERS = [
#         ("numDisparities",  "num_disp_mult", 1,    20,    1,    "× 16"),
#         ("blockSize",       "block_size",    1,    15,    1,    "px"),
#         ("uniquenessRatio", "uniqueness",    0,    30,    1,    ""),
#         ("speckleWindow",   "speckle_win",   0,    300,   1,    "px"),
#         ("speckleRange",    "speckle_range", 1,    64,    1,    ""),
#         ("disp12MaxDiff",   "d12",           0,    10,    1,    ""),
#         ("WLS lambda",      "wls_lambda",    1000, 30000, 1,    ""),
#         ("WLS sigma",       "wls_sigma",     1,    30,    10.0, ""),
#     ]

#     # Title
#     tk.Label(root, text="Disparity Tuner",
#              bg=BG, fg=ACCENT, font=("Segoe UI", 13, "bold")
#              ).grid(row=0, column=0, columnspan=3, pady=(16, 10), padx=24)

#     val_labels = {}

#     for i, (label, key, lo, hi, div, unit) in enumerate(SLIDERS):
#         row = i + 1

#         # Parameter name
#         tk.Label(root, text=label, bg=BG, fg=FG,
#                  font=("Segoe UI", 10), anchor="w", width=LABEL_W
#                  ).grid(row=row, column=0, padx=(24, 8), pady=6, sticky="w")

#         # Value label (shows current value)
#         def fmt(v, d, u):
#             return f"{int(v) if d==1 else f'{v/d:.1f}'} {u}".strip()

#         val_var = tk.StringVar(value=fmt(params[key], div, unit))
#         val_label = tk.Label(root, textvariable=val_var, bg=BG, fg=ACCENT,
#                              font=("Segoe UI", 10, "bold"),
#                              anchor="e", width=VAL_W)
#         val_label.grid(row=row, column=2, padx=(8, 24), sticky="e")
#         val_labels[key] = (val_var, div, unit)

#         # Slider
#         int_var = tk.IntVar(value=params[key])

#         def make_cb(k, iv, vv, d, u):
#             def cb(*_):
#                 v = iv.get()
#                 params[k] = v
#                 vv.set(fmt(v, d, u))
#             return cb

#         slider = tk.Scale(
#             root,
#             variable=int_var,
#             from_=lo, to=hi,
#             orient="horizontal",
#             length=280,
#             bg=BG, fg=FG,
#             troughcolor=TRACK,
#             activebackground=ACCENT,
#             highlightthickness=0,
#             bd=0,
#             showvalue=False,
#             command=make_cb(key, int_var, val_var, div, unit)
#         )
#         slider.grid(row=row, column=1, padx=4, pady=2, sticky="ew")

#     # Divider
#     tk.Frame(root, bg="#333", height=1).grid(
#         row=len(SLIDERS)+1, column=0, columnspan=3,
#         sticky="ew", padx=24, pady=10)

#     # Print button
#     def print_params():
#         p     = dict(params)
#         block = p["block_size"]
#         if block % 2 == 0: block += 1
#         print("\n--- Copy these into disparity.py ---")
#         print(f"num_disp    = 16 * {p['num_disp_mult']}  # = {p['num_disp_mult']*16}")
#         print(f"window_size = {block}")
#         print(f"uniquenessRatio   = {p['uniqueness']}")
#         print(f"speckleWindowSize = {p['speckle_win']}")
#         print(f"speckleRange      = {p['speckle_range']}")
#         print(f"disp12MaxDiff     = {p['d12']}")
#         print(f"wls_filter.setLambda({p['wls_lambda']})")
#         print(f"wls_filter.setSigmaColor({p['wls_sigma'] / 10.0})")
#         print("-------------------------------------\n")

#     tk.Button(
#         root, text="  Print params to terminal  ",
#         command=print_params,
#         bg=ACCENT, fg="#000000",
#         font=("Segoe UI", 10, "bold"),
#         relief="flat", padx=12, pady=8,
#         cursor="hand2", activebackground="#33bbff"
#     ).grid(row=len(SLIDERS)+2, column=0, columnspan=3, pady=(0, 18))

#     def on_close():
#         global running
#         running = False
#         root.destroy()

#     root.protocol("WM_DELETE_WINDOW", on_close)
#     root.mainloop()


# # -----------------------------------
# # Launch
# # -----------------------------------
# cam_thread = threading.Thread(target=camera_loop, daemon=True)
# cam_thread.start()

# build_ui()

import cv2
import numpy as np
import os
import tkinter as tk
import threading

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

# depth = f*B/d  →  d = f*B/depth
def depth_to_disp(depth_m):
    return FOCAL_LENGTH * BASELINE / depth_m

clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))

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
# Params — two independent matchers
# NEAR: optimised for 0.3–1.0m  (high disparity, small block)
# FAR:  optimised for 1.0–4.0m  (low disparity, larger block)
# -----------------------------------
params = {
    # --- NEAR matcher ---
    "near_num_disp":      16 * 16,   # 256 — covers high disparity close objects
    "near_min_disp":      64,        # push dead zone off left edge
    "near_block":         5,         # small block = fine detail up close
    "near_uniqueness":    8,
    "near_speckle_win":   80,
    "near_speckle_range": 16,
    "near_wls_lambda":    6000,
    "near_wls_sigma":     12,        # stored x10

    # --- FAR matcher ---
    "far_num_disp":       16 * 8,    # 128 — background doesn't need huge range
    "far_min_disp":       0,
    "far_block":          9,         # larger block = more stable on flat surfaces
    "far_uniqueness":     12,
    "far_speckle_win":    150,
    "far_speckle_range":  32,
    "far_wls_lambda":     10000,
    "far_wls_sigma":      18,        # stored x10

    # --- Blend threshold ---
    # Disparity value where we crossfade near→far
    # depth_to_disp(1.0m) ≈ 100px for your setup
    "blend_disp":         100,       # crossover point in px
    "blend_width":        30,        # soft blend zone ±width around crossover
}

running  = True
disp_mode = 0   # 0=blended, 1=near only, 2=far only


# -----------------------------------
# Build one SGBM + WLS pair
# -----------------------------------
def make_matcher(num_disp, min_disp, block, uniqueness,
                 speckle_win, speckle_range, wls_lambda, wls_sigma_x10):
    block = block if block % 2 == 1 else block + 1
    block = max(1, block)
    lm = cv2.StereoSGBM_create(
        minDisparity=min_disp,
        numDisparities=num_disp,
        blockSize=block,
        P1=8  * 3 * block**2,
        P2=32 * 3 * block**2,
        disp12MaxDiff=2,
        uniquenessRatio=uniqueness,
        speckleWindowSize=speckle_win,
        speckleRange=speckle_range,
        mode=cv2.STEREO_SGBM_MODE_SGBM_3WAY
    )
    rm  = cv2.ximgproc.createRightMatcher(lm)
    wls = cv2.ximgproc.createDisparityWLSFilter(matcher_left=lm)
    wls.setLambda(wls_lambda)
    wls.setSigmaColor(wls_sigma_x10 / 10.0)
    return lm, rm, wls


def compute_disparity(lm, rm, wls, gray_l, gray_r, rect_l):
    dl = np.int16(lm.compute(gray_l, gray_r))
    dr = np.int16(rm.compute(gray_r, gray_l))
    return wls.filter(dl, rect_l, None, dr).astype(np.float32) / 16.0


# -----------------------------------
# Camera thread
# -----------------------------------
def camera_loop():
    global disp_mode
    while running:
        ret_l, frame_l = left_cam.read()
        ret_r, frame_r = right_cam.read()
        if not ret_l or not ret_r:
            continue

        p = dict(params)

        rect_l = cv2.remap(frame_l, map_l1, map_l2, cv2.INTER_LINEAR)
        rect_r = cv2.remap(frame_r, map_r1, map_r2, cv2.INTER_LINEAR)

        gray_l = clahe.apply(cv2.cvtColor(rect_l, cv2.COLOR_BGR2GRAY))
        gray_r = clahe.apply(cv2.cvtColor(rect_r, cv2.COLOR_BGR2GRAY))
        gray_l = cv2.GaussianBlur(gray_l, (3, 3), 0)
        gray_r = cv2.GaussianBlur(gray_r, (3, 3), 0)

        # Build matchers from current params
        near_lm, near_rm, near_wls = make_matcher(
            p["near_num_disp"], p["near_min_disp"], p["near_block"],
            p["near_uniqueness"], p["near_speckle_win"], p["near_speckle_range"],
            p["near_wls_lambda"], p["near_wls_sigma"]
        )
        far_lm, far_rm, far_wls = make_matcher(
            p["far_num_disp"], p["far_min_disp"], p["far_block"],
            p["far_uniqueness"], p["far_speckle_win"], p["far_speckle_range"],
            p["far_wls_lambda"], p["far_wls_sigma"]
        )

        disp_near = compute_disparity(near_lm, near_rm, near_wls, gray_l, gray_r, rect_l)
        disp_far  = compute_disparity(far_lm,  far_rm,  far_wls,  gray_l, gray_r, rect_l)

        if disp_mode == 1:
            combined = disp_near
        elif disp_mode == 2:
            combined = disp_far
        else:
            # Soft blend: sigmoid centred at blend_disp
            # near disparity is high → used for close objects
            # far  disparity is low  → used for distant objects
            bd = p["blend_disp"]
            bw = max(1, p["blend_width"])
            # weight_near: 1 where disp is high (close), 0 where disp is low (far)
            weight_near = 1.0 / (1.0 + np.exp(-(disp_near - bd) / bw))
            weight_far  = 1.0 - weight_near

            valid_near = disp_near > p["near_min_disp"]
            valid_far  = disp_far  > 0

            combined = np.zeros_like(disp_near)

            # Where both are valid: blend
            both = valid_near & valid_far
            combined[both] = (weight_near[both] * disp_near[both] +
                              weight_far[both]  * disp_far[both])

            # Where only one is valid: use that one
            combined[valid_near & ~valid_far] = disp_near[valid_near & ~valid_far]
            combined[valid_far  & ~valid_near] = disp_far[valid_far  & ~valid_near]

        # Visualise
        disp_min_vis = depth_to_disp(4.0)
        disp_max_vis = depth_to_disp(0.3)

        valid = combined > disp_min_vis
        vis   = np.zeros_like(combined, dtype=np.uint8)
        vis[valid] = np.clip(
            (combined[valid] - disp_min_vis) / (disp_max_vis - disp_min_vis) * 255,
            0, 255
        ).astype(np.uint8)
        output = cv2.applyColorMap(vis, cv2.COLORMAP_JET)

        mode_names = {0: "Blended", 1: "Near only", 2: "Far only"}
        cv2.putText(output, f"[M] {mode_names[disp_mode]}  [Q] quit",
                    (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255,255,255), 2)

        cv2.imshow("Disparity", output)
        key = cv2.waitKey(1) & 0xFF
        if key == ord('m'):
            disp_mode = (disp_mode + 1) % 3
        elif key == ord('q'):
            break

    left_cam.release()
    right_cam.release()
    cv2.destroyAllWindows()


# -----------------------------------
# Tkinter UI
# -----------------------------------
def build_ui():
    root = tk.Tk()
    root.title("Dual Matcher Tuner")
    root.resizable(False, False)

    BG     = "#1a1a2e"
    FG     = "#e0e0e0"
    NEAR_C = "#00ccff"   # blue-ish for near
    FAR_C  = "#ff9900"   # orange for far
    BLEND_C= "#aaffaa"   # green for blend controls
    TRACK  = "#2a2a3e"
    root.configure(bg=BG)

    def section_label(text, color, row, col, colspan):
        tk.Label(root, text=text, bg=BG, fg=color,
                 font=("Segoe UI", 11, "bold")
                 ).grid(row=row, column=col, columnspan=colspan,
                        pady=(14, 4), padx=24, sticky="w")

    def add_slider(row, label, key, lo, hi, color):
        tk.Label(root, text=label, bg=BG, fg=FG,
                 font=("Segoe UI", 9), anchor="w", width=20
                 ).grid(row=row, column=0, padx=(24, 6), pady=3, sticky="w")

        val_var = tk.StringVar(value=str(params[key]))

        int_var = tk.IntVar(value=params[key])

        def cb(*_):
            v = int_var.get()
            params[key] = v
            val_var.set(str(v))

        tk.Scale(root, variable=int_var, from_=lo, to=hi,
                 orient="horizontal", length=260,
                 bg=BG, fg=color, troughcolor=TRACK,
                 highlightthickness=0, bd=0, showvalue=False,
                 activebackground=color,
                 command=cb
                 ).grid(row=row, column=1, padx=4, pady=2)

        tk.Label(root, textvariable=val_var, bg=BG, fg=color,
                 font=("Segoe UI", 9, "bold"), width=8, anchor="e"
                 ).grid(row=row, column=2, padx=(4, 24), sticky="e")

    r = 0

    # NEAR section
    section_label("NEAR matcher  (0.3 – 1.0 m)", NEAR_C, r, 0, 3); r += 1
    add_slider(r, "numDisparities (×16)", "near_num_disp",      16,   256,  NEAR_C); r += 1
    add_slider(r, "minDisparity",         "near_min_disp",      0,    128,  NEAR_C); r += 1
    add_slider(r, "blockSize",            "near_block",         1,    15,   NEAR_C); r += 1
    add_slider(r, "uniquenessRatio",      "near_uniqueness",    0,    30,   NEAR_C); r += 1
    add_slider(r, "speckleWindow",        "near_speckle_win",   0,    300,  NEAR_C); r += 1
    add_slider(r, "speckleRange",         "near_speckle_range", 1,    64,   NEAR_C); r += 1
    add_slider(r, "WLS lambda",           "near_wls_lambda",    1000, 20000,NEAR_C); r += 1
    add_slider(r, "WLS sigma (×10)",      "near_wls_sigma",     1,    30,   NEAR_C); r += 1

    tk.Frame(root, bg="#333", height=1).grid(
        row=r, column=0, columnspan=3, sticky="ew", padx=24, pady=6); r += 1

    # FAR section
    section_label("FAR matcher  (1.0 – 4.0 m)", FAR_C, r, 0, 3); r += 1
    add_slider(r, "numDisparities (×16)", "far_num_disp",       16,   256,  FAR_C); r += 1
    add_slider(r, "minDisparity",         "far_min_disp",       0,    128,  FAR_C); r += 1
    add_slider(r, "blockSize",            "far_block",          1,    15,   FAR_C); r += 1
    add_slider(r, "uniquenessRatio",      "far_uniqueness",     0,    30,   FAR_C); r += 1
    add_slider(r, "speckleWindow",        "far_speckle_win",    0,    300,  FAR_C); r += 1
    add_slider(r, "speckleRange",         "far_speckle_range",  1,    64,   FAR_C); r += 1
    add_slider(r, "WLS lambda",           "far_wls_lambda",     1000, 20000,FAR_C); r += 1
    add_slider(r, "WLS sigma (×10)",      "far_wls_sigma",      1,    30,   FAR_C); r += 1

    tk.Frame(root, bg="#333", height=1).grid(
        row=r, column=0, columnspan=3, sticky="ew", padx=24, pady=6); r += 1

    # BLEND section
    section_label("Blend controls", BLEND_C, r, 0, 3); r += 1
    add_slider(r, "blend crossover (px)", "blend_disp",  10, 250, BLEND_C); r += 1
    add_slider(r, "blend width (px)",     "blend_width", 1,  100, BLEND_C); r += 1

    tk.Frame(root, bg="#333", height=1).grid(
        row=r, column=0, columnspan=3, sticky="ew", padx=24, pady=8); r += 1

    # Hint label
    tk.Label(root,
             text="In disparity window: M = cycle near/far/blend view   Q = quit",
             bg=BG, fg="#888", font=("Segoe UI", 9)
             ).grid(row=r, column=0, columnspan=3, pady=(0, 6)); r += 1

    # Print button
    def print_params():
        p = dict(params)
        print("\n--- NEAR matcher ---")
        print(f"numDisparities    = {p['near_num_disp']}")
        print(f"minDisparity      = {p['near_min_disp']}")
        print(f"blockSize         = {p['near_block']}")
        print(f"uniquenessRatio   = {p['near_uniqueness']}")
        print(f"speckleWindowSize = {p['near_speckle_win']}")
        print(f"speckleRange      = {p['near_speckle_range']}")
        print(f"wls_lambda        = {p['near_wls_lambda']}")
        print(f"wls_sigma         = {p['near_wls_sigma']/10.0}")
        print("\n--- FAR matcher ---")
        print(f"numDisparities    = {p['far_num_disp']}")
        print(f"minDisparity      = {p['far_min_disp']}")
        print(f"blockSize         = {p['far_block']}")
        print(f"uniquenessRatio   = {p['far_uniqueness']}")
        print(f"speckleWindowSize = {p['far_speckle_win']}")
        print(f"speckleRange      = {p['far_speckle_range']}")
        print(f"wls_lambda        = {p['far_wls_lambda']}")
        print(f"wls_sigma         = {p['far_wls_sigma']/10.0}")
        print(f"\nblend_disp  = {p['blend_disp']}")
        print(f"blend_width = {p['blend_width']}")
        print("-----------------------------\n")

    tk.Button(root, text="  Print params to terminal  ",
              command=print_params,
              bg="#00aaff", fg="#000", font=("Segoe UI", 10, "bold"),
              relief="flat", padx=12, pady=8, cursor="hand2"
              ).grid(row=r, column=0, columnspan=3, pady=(0, 18))

    def on_close():
        global running
        running = False
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_close)
    root.mainloop()


# -----------------------------------
# Launch
# -----------------------------------
cam_thread = threading.Thread(target=camera_loop, daemon=True)
cam_thread.start()
build_ui()