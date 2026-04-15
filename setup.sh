#!/bin/bash

# Create folders
mkdir -p calibration/data
mkdir -p capture/data
mkdir -p stereo
mkdir -p reconstruction
mkdir -p utils

# calibration
touch calibration/capture_calib.py
touch calibration/calibrate.py
touch calibration/rectification.py

# capture
touch capture/capture_stereo.py

# stereo
touch stereo/disparity.py
touch stereo/census.py
touch stereo/triangulation.py

# reconstruction
touch reconstruction/pointcloud.py
touch reconstruction/transform.py
touch reconstruction/fusion.py

# utils
touch utils/camera.py
touch utils/io.py
touch utils/visualization.py

# main entry
touch main.py

# optional
touch requirements.txt

# make packages (clean imports)
touch calibration/__init__.py
touch capture/__init__.py
touch stereo/__init__.py
touch reconstruction/__init__.py
touch utils/__init__.py

echo "Structure created in current repo"