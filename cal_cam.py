import cv2
import numpy as np
import glob
import os

# =========================
# 設定
# =========================

# チェスボードの「内側の交点数」
# 例: 横10マス x 縦7マスのチェスボードなら、内側交点は 9 x 6
CHECKERBOARD = (9, 6)

# 1マスの実寸
# 単位は任意ですが、後で距離推定にも使うならメートル推奨
# 例: 25mm = 0.025m
SQUARE_SIZE = 0.025

IMAGE_DIR = "calib_images"
OUTPUT_DIR = "calibration_result"

os.makedirs(OUTPUT_DIR, exist_ok=True)

# cornerSubPix用の終了条件
criteria = (
    cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER,
    30,
    0.001
)

# =========================
# 3D点を準備
# =========================

# チェスボードは平面なので Z=0
# 例:
# (0,0,0), (1,0,0), (2,0,0), ...
objp = np.zeros((CHECKERBOARD[0] * CHECKERBOARD[1], 3), np.float32)
objp[:, :2] = np.mgrid[
    0:CHECKERBOARD[0],
    0:CHECKERBOARD[1]
].T.reshape(-1, 2)

# 実寸スケールを反映
objp *= SQUARE_SIZE

# 全画像分の3D点・2D点
objpoints = []  # 3D点
imgpoints = []  # 画像上の2D点

# =========================
# 画像を読み込んでコーナー検出
# =========================

image_paths = sorted(glob.glob(os.path.join(IMAGE_DIR, "*.jpg")))

if not image_paths:
    raise RuntimeError(f"{IMAGE_DIR} に .jpg 画像が見つかりません。")

image_size = None
valid_count = 0

for path in image_paths:
    img = cv2.imread(path)

    if img is None:
        print(f"読み込み失敗: {path}")
        continue

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    image_size = gray.shape[::-1]  # (width, height)

    ret, corners = cv2.findChessboardCorners(gray, CHECKERBOARD, None)

    if ret:
        # コーナー位置をサブピクセル精度に補正
        corners_refined = cv2.cornerSubPix(
            gray,
            corners,
            (11, 11),
            (-1, -1),
            criteria
        )

        objpoints.append(objp)
        imgpoints.append(corners_refined)
        valid_count += 1

        print(f"OK: {path}")
    else:
        print(f"NG: {path}")

if valid_count < 10:
    print(f"警告: 有効画像が {valid_count} 枚です。最低10枚以上、できれば20枚以上を推奨します。")

# =========================
# キャリブレーション
# =========================

ret, camera_matrix, dist_coeffs, rvecs, tvecs = cv2.calibrateCamera(
    objpoints,
    imgpoints,
    image_size,
    None,
    None
)

print("\n=== Calibration Result ===")
print("RMS reprojection error:", ret)
print("camera_matrix:")
print(camera_matrix)
print("dist_coeffs:")
print(dist_coeffs)

# =========================
# 再投影誤差を計算
# =========================

mean_error = 0.0

for i in range(len(objpoints)):
    projected_points, _ = cv2.projectPoints(
        objpoints[i],
        rvecs[i],
        tvecs[i],
        camera_matrix,
        dist_coeffs
    )

    error = cv2.norm(imgpoints[i], projected_points, cv2.NORM_L2) / len(projected_points)
    mean_error += error

mean_error /= len(objpoints)

print("mean reprojection error:", mean_error)

# =========================
# .npy と .npz で保存
# =========================

np.save(os.path.join(OUTPUT_DIR, "camera_matrix.npy"), camera_matrix)
np.save(os.path.join(OUTPUT_DIR, "dist_coeffs.npy"), dist_coeffs)

# まとめて保存したい場合はこちらも便利
np.savez(
    os.path.join(OUTPUT_DIR, "camera_calibration.npz"),
    camera_matrix=camera_matrix,
    dist_coeffs=dist_coeffs,
    rvecs=rvecs,
    tvecs=tvecs,
    image_size=image_size,
    rms_error=ret,
    mean_reprojection_error=mean_error
)

print("\n保存しました:")
print(os.path.join(OUTPUT_DIR, "camera_matrix.npy"))
print(os.path.join(OUTPUT_DIR, "dist_coeffs.npy"))
print(os.path.join(OUTPUT_DIR, "camera_calibration.npz"))
