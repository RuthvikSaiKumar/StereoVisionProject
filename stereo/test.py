import numpy as np

calib = np.load('../calibration/data/stereo_calib.npz')
print(calib.files)
for k in calib.files:
    print(k, calib[k])