import cv2
import numpy as np
import csv
from scipy.spatial.transform import Rotation as R

video_path = "input.mp4"
marker_length = 0.05  # 5cm。単位はメートル

# 事前にキャリブレーションして得た値を使う
camera_matrix = np.load("camera_matrix.npy")
dist_coeffs = np.load("dist_coeffs.npy")

dictionary = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_6X6_250)
parameters = cv2.aruco.DetectorParameters()
detector = cv2.aruco.ArucoDetector(dictionary, parameters)

# マーカー中心を原点とする4隅の3D座標
half = marker_length / 2
object_points = np.array([
    [-half,  half, 0],
    [ half,  half, 0],
    [ half, -half, 0],
    [-half, -half, 0],
], dtype=np.float32)

cap = cv2.VideoCapture(video_path)
fps = cap.get(cv2.CAP_PROP_FPS)

with open("pose_output.csv", "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow([
        "frame", "time_sec", "marker_id",
        "x", "y", "z",
        "roll_deg", "pitch_deg", "yaw_deg"
    ])

    frame_idx = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        corners, ids, rejected = detector.detectMarkers(frame)

        if ids is not None:
            for marker_corners, marker_id in zip(corners, ids.flatten()):
                image_points = marker_corners.reshape(4, 2).astype(np.float32)

                ok, rvec, tvec = cv2.solvePnP(
                    object_points,
                    image_points,
                    camera_matrix,
                    dist_coeffs,
                    flags=cv2.SOLVEPNP_IPPE_SQUARE
                )

                if ok:
                    rotation_matrix, _ = cv2.Rodrigues(rvec)
                    euler = R.from_matrix(rotation_matrix).as_euler("xyz", degrees=True)

                    x, y, z = tvec.flatten()
                    roll, pitch, yaw = euler

                    writer.writerow([
                        frame_idx,
                        frame_idx / fps,
                        int(marker_id),
                        x, y, z,
                        roll, pitch, yaw
                    ])

        frame_idx += 1

cap.release()
