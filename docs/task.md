# 開發板感知模組 Task List

> 依 spec.md 第 8 節里程碑細分。一次做一個 task，完成後打勾、回報做了什麼與預期結果，經使用者同意後再 commit。
> 每個 task 都附「完成條件」，達成才算完成。

---

## M0：專案準備

- [x] **0.1 建立 repo 結構**
  依 spec.md 第 5 節建立 `board/comm/`、`board/perception/`、`tools/`、`tests/` 資料夾與空的 `__init__.py`。
  完成條件：資料夾結構與 spec 一致。

- [x] **0.2 環境與相依套件**
  建立 `pyproject.toml`（相依：numpy、opencv-python；dev：pytest），讓 `pip install -e ".[dev]"` 後任何位置都能 `import board`；加一個冒煙測試（smoke test，只確認 `import board` 成功）；README 寫安裝步驟。
  完成條件：新環境照 README 能裝好，`pytest` 通過（至少 1 個測試，pytest 沒收集到測試時會回傳失敗）。

- [x] **0.3 建立 `config.py`**
  把 spec.md 第 7 節所有參數寫進去，TBD 項目先填暫定值並加註解。
  完成條件：其他模組能 `from board.config import ...`。

- [ ] **0.4 確認投放面積**
  依「物資大小 + 2 ×（位置誤差 + 落下偏移）」決定 `DROP_AREA`，同步更新 spec.md。
  完成條件：spec.md 與 config.py 數值一致，並寫下計算依據。

---

## M1：接收深度圖 + 視覺化

- [ ] **1.1 假深度圖來源 `tools/fake_depth_sender.py`**
  依 spec 4.1 格式送出 320×240 float32 深度圖：平地 10 m、一個移動方塊、雜訊、一小塊 `inf`；時間戳用 `time.time()`。
  第 4 節的 port（5000、6000、6001）與心跳逾時（3 s）加入 config.py，並補進 spec 第 7 節。
  完成條件：執行後等待連線，連線後持續以約 10 FPS 送出。

- [ ] **1.2 深度圖接收 `board/comm/depth_receiver.py`**
  連線、讀 header、`recv_exact` 收滿資料、轉成 NumPy，寬高以 header 為準；斷線自動重連；提供 `frames()` generator。
  完成條件：搭配 1.1 能持續收到正確尺寸的陣列，關掉 sender 再開能自動接回。

- [ ] **1.3 接收端單元測試**
  用 socketpair 或本機 socket 送一幀已知資料，驗證解析結果。
  完成條件：`pytest` 通過，包含 header 解析與資料分兩次到達的情況。

- [ ] **1.4 深度圖視覺化 `tools/visualize.py`**
  繪圖函式（之後 `app.py --show` 也會用）+ 獨立檢視器（直接連 port 5000）。把深度圖轉成彩色圖（`cv2.applyColorMap`），`inf` 顯示為黑色，畫面角落顯示中心距離與 FPS。
  完成條件：開啟視窗即時顯示，看得出移動方塊。

- [ ] **1.5 README 示範說明**
  寫清楚兩個終端機各執行什麼、預期看到什麼，附一張截圖。
  完成條件：別人照 README 能重現。**此時可提交課程 GitHub 作業。**

---

## M2：地面檢查

- [ ] **2.1 合成測試資料產生器**
  `tests/synthetic.py`：可產生平地、斜坡、方塊、多個障礙物、含 `inf` 的深度圖，可指定相機傾斜角，供各測試共用。
  完成條件：產生器本身有基本測試（尺寸、型別、平地深度值正確）；2.3～2.6 的測試都使用它。

- [ ] **2.2 相機內參 `perception/geometry.py`**
  由解析度與 `CAMERA_HFOV_DEG` 算出 fx、fy、cx、cy。
  完成條件：單元測試驗證中心像素對應光軸。

- [ ] **2.3 深度圖 → 點雲**
  將深度圖轉成相機座標系（spec 4.4）的 N×3 點雲，過濾 `inf`/`NaN`。
  完成條件：對「平地 10 m」的合成深度圖，所有點 z ≈ 10。

- [ ] **2.4 姿態補償**
  用 roll、pitch（度）把點雲轉到水平座標系。
  完成條件：合成「傾斜 5° 拍平地」的深度圖，補償後擬合出的坡度 ≈ 0°。

- [ ] **2.5 RANSAC 平面擬合**
  對一組點擬合平面，回傳法向量與內點；與使用者確認 `RANSAC_ITERATIONS`、`RANSAC_INLIER_DIST`。
  完成條件：在有 20% 離群點的資料上仍能擬合出正確平面。

- [ ] **2.6 評分 `perception/ground_check.py`**
  對指定區域計算坡度、粗糙度、凸起物高度，與門檻比較，輸出 `safe` 與 0～1 分數；與使用者確認 `SCORE_WEIGHTS`。
  完成條件：合成資料測試——平地安全、10° 以上斜坡不安全、有 20 cm 方塊不安全、含 `inf` 不會崩潰。

- [ ] **2.7 視覺化檢查結果**
  在 visualize.py 疊上檢查區域框，安全綠色、不安全紅色，並顯示三項數值。
  完成條件：fake sender 的方塊移進框內時變紅。

---

## M3：替代點推薦 + 座標轉換

- [ ] **3.1 像素 → 相機座標**
  給定像素與深度，算出相機座標系的 3D 點。
  完成條件：與 2.3 的結果一致。

- [ ] **3.2 相機座標 → NED**
  依 spec 4.4 的慣例，結合 `CAMERA_MOUNT`、無人機 attitude（含 yaw）與 position_ned，算出地面點的 NED 座標（z 為實際地面高度）。
  完成條件：單元測試涵蓋 yaw = 0°、90°、180° 及有 roll/pitch 的情況，誤差 < 5 cm。

- [ ] **3.3 NED → 像素**
  反向轉換，用來把 `target_ned`（只用 N、E）對應到畫面上的檢查區域；目標不在畫面內時要能判斷出來。
  完成條件：與 3.2 來回轉換結果一致；畫面外的目標回報不在畫面內。

- [ ] **3.4 格子搜尋 `perception/candidates.py`**
  把可見地面切成 `DROP_AREA` 大小的格子，每格用 2.6 評分，加入離目標距離的懲罰；與使用者確認 `DISTANCE_PENALTY`。
  完成條件：在「目標處有方塊、旁邊是平地」的合成資料上，最高分的格子不在方塊上。

- [ ] **3.5 挑選候選點**
  取分數最高、彼此不重疊的前 `MAX_CANDIDATES` 個，轉成 NED。
  完成條件：輸出格式符合 spec 4.3 的 `candidates`（含 `error` 欄位）。

- [ ] **3.6 視覺化候選點**
  在畫面上標出原目標與候選點（編號 + 分數）。
  完成條件：肉眼確認候選點都落在平地上。

---

## M4：UDP 通訊

- [ ] **4.1 假 Python Server `tools/fake_server.py`**
  10 Hz 送 `state`；可用鍵盤觸發送出 `check_target`、`confirm_drop`、`cancel`，以及用相同 `id` 重送；印出收到的所有訊息。
  完成條件：可手動操作完整流程。

- [ ] **4.2 `board/comm/server_link.py` 接收**
  監聽 port 6000，解析 JSON，依 `type` 分派；保存最新 `state`。
  完成條件：格式錯誤的封包會被忽略並記錄，不會讓程式崩潰。

- [ ] **4.3 `server_link.py` 發送與心跳**
  提供送 `candidates`、`drop_check` 的函式；背景每秒送 `heartbeat`。
  完成條件：fake server 每秒都收到心跳。

- [ ] **4.4 主程式狀態機 `board/app.py`**
  狀態：`IDLE` → 收到 `check_target` → `CHECKING` → 回覆 `candidates` → `IDLE`；`cancel` 可中斷；依 spec 4.3 處理重複 `id` 與 `error`。
  完成條件：用 fake server 觸發 `check_target`，收到 `id` 相同的回覆；用相同 `id` 重送時收到同一份結果，不重新計算。

- [ ] **4.5 時間對齊**
  做地面檢查時，使用與深度圖時間戳最接近的 `state`（兩者皆為 Unix 時間）。
  完成條件：記錄兩者時間差，正常情況 < 0.1 秒。

- [ ] **4.6 端對端示範**
  fake depth sender + fake server + app 同時執行，完成一次 check_target 流程；app 提供 `--show` 顯示檢查結果（深度來源只接受一個連線，不能再另開 visualize.py）。
  完成條件：README 加上執行步驟。

---

## M5：投放前確認

- [ ] **5.1 鏡頭畫面接收 `board/comm/camera_receiver.py`**
  用 OpenCV + GStreamer pipeline 接收 RTP/H.264。
  完成條件：能顯示畫面；先用 `gst-launch-1.0 videotestsrc` 自建測試來源。

- [ ] **5.2 假鏡頭來源**
  `tools/fake_camera_sender.py`：送出含移動色塊的畫面，並可加入整體晃動（平移、旋轉、縮放）。
  完成條件：5.1 收得到。

- [ ] **5.3 晃動補償 `perception/motion.py`**
  用特徵點匹配估計前後幀的 homography 並對齊前一幀。
  完成條件：只有晃動（含旋轉與縮放）、沒有移動物體時，補償後差異接近 0。

- [ ] **5.4 移動物體偵測**
  補償後做幀差或背景相減，回傳移動區域。
  完成條件：5.2 的移動色塊被偵測到，晃動不會誤判。

- [ ] **5.5 人物偵測 `perception/person.py`（PC 版）**
  使用預訓練 YOLO 偵測人、車、動物。
  完成條件：在含人物的 Gazebo 畫面或測試圖片上框出人物；另用**俯視角度**畫面實測並記錄偵測率，偵測率不足時提出微調方案。

- [ ] **5.6 安全判斷與延遲確認**
  綜合 5.4、5.5 與投放區域的深度凸起物判斷（`obstacle`）；須連續 `SAFE_HOLD_SEC` 安全才回 `safe: true`；超過 `NO_DATA_TIMEOUT` 沒畫面回 `no_data`。
  完成條件：單元測試覆蓋「短暫消失不算安全」、「沒畫面」與「投放區域有障礙物」的情況。

- [ ] **5.7 接上狀態機**
  `confirm_drop` → `CONFIRMING`，狀態改變時送 `drop_check`，直到 `cancel` 或新指令。
  完成條件：fake server 能看到 unsafe → safe 的變化。

---

## M6：移植聯詠 NPU

- [ ] **6.1 確認開發板型號與 SDK**
  取得 SDK 文件，記錄支援的模型格式、運算子、量化方式。
  完成條件：寫成 `docs/npu_notes.md`。

- [ ] **6.2 跑通官方範例**
  在開發板上執行 SDK 內建的範例模型。
  完成條件：記錄步驟與 FPS。

- [ ] **6.3 在開發板上跑 CPU 部分**
  把 M1～M4 程式部署到開發板（Python 環境、相依套件）。
  完成條件：開發板連到 PC 上的 fake sender / fake server 完成端對端流程。

- [ ] **6.4 轉換 YOLO 模型**
  依 SDK 流程轉換與量化（通常 INT8），準備校正資料。
  完成條件：轉換成功，PC 上模擬推論結果與原模型相近。

- [ ] **6.5 NPU 推論整合**
  `person.py` 加入 NPU 後端，可用設定切換 PC / NPU。
  完成條件：開發板上偵測結果正確，記錄 FPS 與延遲。

- [ ] **6.6 效能檢查**
  量測各階段耗時（接收、地面檢查、偵測）與網路實際傳輸量，找出瓶頸。
  完成條件：整體處理能跟上 10 FPS，否則記錄並提出降解析度等對策。

---

## M7：水池偵測（進階）

- [ ] **7.1 顏色判斷版本**
  HSV 門檻找出水面區域，門檻放 config.py。
  完成條件：Gazebo 水池畫面中水面被正確標出。

- [ ] **7.2 鏡頭像素 ↔ 深度像素對齊**
  處理兩顆相機位置、視角與解析度差異，把水面遮罩對應到深度圖。
  完成條件：遮罩疊在深度圖上位置正確。

- [ ] **7.3 排除水面候選點**
  3.4 評分時，含水面的格子直接判定不安全。
  完成條件：水池上不會出現候選點。

- [ ] **7.4（選做）分割模型**
  用 Gazebo 分割相機自動產生標註，訓練小型分割模型取代顏色判斷。
  完成條件：在不同水池顏色下仍能偵測。

---

## 需要組員配合（不擋開發，可並行）

見 `docs/questions.md`。
