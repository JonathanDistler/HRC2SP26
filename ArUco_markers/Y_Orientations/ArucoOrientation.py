import cv2
import cv2.aruco as aruco
import numpy as np
import os

#takes png images of AruCo images and shows the y-orientation

# ---------------------------
# 1. List of image paths, from local system; had to convert the pdfs from the AruCo making website into PNGs
# ---------------------------
img_paths = [
    r"C:\Users\jonat\Downloads\2.png",
    r"C:\Users\jonat\Downloads\3.png",
    r"C:\Users\jonat\Downloads\4.png",
    r"C:\Users\jonat\Downloads\5.png",
    r"C:\Users\jonat\Downloads\6.png",
    r"C:\Users\jonat\Downloads\1.png"
]

# Output folder for annotated images
output_folder = r"C:\Users\jonat\Downloads\aruco_output"
os.makedirs(output_folder, exist_ok=True)

# ---------------------------
# 2. Camera intrinsics (replace with your calibration)
# ---------------------------
fx, fy = 800, 800  # focal lengths in pixels
cx, cy = 640, 360  # principal point (example)
camera_matrix = np.array([[fx, 0, cx],
                          [0, fy, cy],
                          [0, 0, 1]], dtype=np.float32)
dist_coeffs = np.zeros((5,), dtype=np.float32)  # assuming no lens distortion

# Marker size in meters
marker_length = 0.05

# ---------------------------
# 3. ArUco dictionary and detector parameters
# ---------------------------
aruco_dict = aruco.getPredefinedDictionary(aruco.DICT_4X4_50)
parameters = aruco.DetectorParameters()  # modern OpenCV

# ---------------------------
# 4. Process each image
# ---------------------------
for path in img_paths:
    img = cv2.imread(path, cv2.IMREAD_COLOR)
    if img is None:
        print(f"Failed to load {path}")
        continue

    # Optionally resize if too large
    scale_factor = 0.5
    img_resized = cv2.resize(img, (0, 0), fx=scale_factor, fy=scale_factor)

    gray = cv2.cvtColor(img_resized, cv2.COLOR_BGR2GRAY)

    # Detect markers
    corners, ids, rejected = aruco.detectMarkers(gray, aruco_dict, parameters=parameters)
    if ids is None:
        print(f"No ArUco markers detected in {path}")
        continue

    aruco.drawDetectedMarkers(img_resized, corners, ids)

    # Estimate pose
    rvecs, tvecs, _ = aruco.estimatePoseSingleMarkers(corners, marker_length, camera_matrix, dist_coeffs)

    for i, (rvec, tvec) in enumerate(zip(rvecs, tvecs)):
        marker_id = ids[i][0]
        print(f"Image: {os.path.basename(path)}, Marker ID: {marker_id}")
        print("Rotation vector (rvec):", rvec.flatten())
        print("Translation vector (tvec):", tvec.flatten())

        # Draw axes using modern OpenCV
        cv2.drawFrameAxes(img_resized, camera_matrix, dist_coeffs, rvec, tvec, marker_length * 0.5)

        # Get Y-axis in camera coordinates
        R, _ = cv2.Rodrigues(rvec)
        y_axis_cam = R[:, 1]
        print("Marker Y-axis in camera coordinates:", y_axis_cam)

    # Save annotated image
    output_path = os.path.join(output_folder, os.path.basename(path))
    cv2.imwrite(output_path, img_resized)
    print(f"Annotated image saved to: {output_path}\n")