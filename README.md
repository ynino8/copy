# copy

OpenCV を使って、カメラキャリブレーションと ArUco マーカーの姿勢推定を行う小さなスクリプト集です。

## What is included

- `cal_cam.py`
  - `calib_images/*.jpg` に置いたチェスボード画像を読み込みます。
  - チェスボードの内側交点を検出し、カメラ行列と歪み係数を推定します。
  - 結果を `calibration_result/` に `.npy` と `.npz` で保存します。
- `ana_mov.py`
  - `input.mp4` から ArUco マーカーを検出します。
  - `camera_matrix.npy` と `dist_coeffs.npy` を使って各マーカーの位置と姿勢を推定します。
  - フレーム番号、時刻、マーカー ID、並進量、roll/pitch/yaw を `pose_output.csv` に書き出します。

## Requirements

Python 3 と以下のライブラリが必要です。

```bash
python3 -m pip install numpy scipy opencv-contrib-python
```

`ana_mov.py` は `cv2.aruco` を使うため、通常の `opencv-python` ではなく `opencv-contrib-python` を使います。

## Calibration workflow

1. チェスボードを複数角度から撮影した `.jpg` 画像を `calib_images/` に置きます。
2. `cal_cam.py` の設定値を撮影に合わせて確認します。
   - `CHECKERBOARD`: チェスボードの内側交点数です。例として、横 10 マス、縦 7 マスなら `(9, 6)` です。
   - `SQUARE_SIZE`: 1 マスの実寸です。距離推定にも使う場合はメートル単位を推奨します。
3. キャリブレーションを実行します。

```bash
python3 cal_cam.py
```

成功すると、以下が作成されます。

- `calibration_result/camera_matrix.npy`
- `calibration_result/dist_coeffs.npy`
- `calibration_result/camera_calibration.npz`

有効画像が 10 枚未満の場合は警告が出ます。実用上は 20 枚以上の画像を用意すると安定しやすくなります。

## Pose estimation workflow

1. 解析したい動画を `input.mp4` として配置します。
2. `ana_mov.py` が読み込める場所にキャリブレーション結果を置きます。

```bash
cp calibration_result/camera_matrix.npy .
cp calibration_result/dist_coeffs.npy .
```

3. 必要に応じて `ana_mov.py` の設定値を調整します。
   - `video_path`: 入力動画のパスです。既定値は `input.mp4` です。
   - `marker_length`: ArUco マーカーの一辺の実寸です。既定値は `0.05`、つまり 5 cm です。
   - ArUco 辞書は `cv2.aruco.DICT_6X6_250` を使っています。
4. 姿勢推定を実行します。

```bash
python3 ana_mov.py
```

出力される `pose_output.csv` には次の列が含まれます。

| Column | Description |
| --- | --- |
| `frame` | 動画内のフレーム番号 |
| `time_sec` | `frame / fps` で計算した動画内時刻 |
| `marker_id` | 検出した ArUco マーカー ID |
| `x`, `y`, `z` | カメラ座標系でのマーカー位置 |
| `roll_deg`, `pitch_deg`, `yaw_deg` | 回転行列から `xyz` 順で変換した姿勢角 |

## Notes

- `ana_mov.py` はマーカー中心を原点とし、マーカー平面を `Z=0` とする 4 隅の 3D 座標を使って `cv2.solvePnP(..., flags=cv2.SOLVEPNP_IPPE_SQUARE)` を実行します。
- キャリブレーション結果は `cal_cam.py` では `calibration_result/` に保存されますが、`ana_mov.py` は既定でリポジトリ直下の `camera_matrix.npy` と `dist_coeffs.npy` を読みます。必要に応じてファイルをコピーするか、読み込みパスを変更してください。
- 入力画像、入力動画、キャリブレーション結果、CSV 出力は生成物・ローカルデータとして扱い、必要なものだけ管理対象に追加してください。
