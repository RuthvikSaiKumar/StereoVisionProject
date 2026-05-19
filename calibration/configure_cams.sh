# 1. Turn OFF Auto White Balance
v4l2-ctl -d /dev/video2 -c white_balance_automatic=0
v4l2-ctl -d /dev/video4 -c white_balance_automatic=0

# 2. Turn OFF Auto Exposure (Setting '1' usually forces Manual Mode)
v4l2-ctl -d /dev/video2 -c auto_exposure=1
v4l2-ctl -d /dev/video4 -c auto_exposure=1

# 3. Turn OFF Dynamic Framerate (Forces strict sync)
v4l2-ctl -d /dev/video2 -c exposure_dynamic_framerate=0
v4l2-ctl -d /dev/video4 -c exposure_dynamic_framerate=0

# 4. Set exact identical Exposure Time (156 is your default, adjust if it's too dark/bright)
v4l2-ctl -d /dev/video2 -c exposure_time_absolute=156
v4l2-ctl -d /dev/video4 -c exposure_time_absolute=156

# 5. Lock Gain to the same value (0 eliminates digital noise)
v4l2-ctl -d /dev/video2 -c gain=0
v4l2-ctl -d /dev/video4 -c gain=0