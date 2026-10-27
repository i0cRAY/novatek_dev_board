# 開發板感知模組 Spec

> XR 無人機救災物資投放專案 — 開發板（聯詠）部分
> 負責人：林希叡
> 狀態：草案。標示 **TBD** 的項目尚待與組員確認。

---

## 1. 目標

確保投放點是安全的，沒有障礙物或水池。

- **抵達目的地上空時**：利用深度畫面判斷地面坡度與凸起物；水池在深度畫面上與平地無異，需用鏡頭畫面做地面分割。若目標點不平整、有障礙物或水池，從附近找出安全的投放點推薦給操作員選擇。
- **降到投放高度後**：用鏡頭畫面再次確認下方無人、無移動物體，確認安全才允許投放；若不安全則暫停，等待或改選其他投放點。

開發板只負責「判斷與推薦」，不直接控制無人機；最終決定由操作員在 XR 眼鏡中做出。

## 2. 系統中的位置

```
Gazebo（虛擬深度相機） ──TCP──────────▶ ┐
Gazebo（虛擬鏡頭）     ──GStreamer────▶ ├─ 開發板（本模組）
Python Server          ──UDP JSON─────▶ ┘        │
                                                 │
Python Server ◀──────────UDP JSON────────────────┘
```

- 執行環境：開發階段在一般電腦，最終部署到聯詠開發板
- 「接收資料」與「分析資料」必須分開：之後換成真實相機時，只換接收層，演算法不動

## 3. 範圍

**要做**
- 接收深度圖、鏡頭畫面、無人機狀態與指令
- 地面檢查：坡度、粗糙度、凸起物
- 替代投放點推薦，含像素 → NED 座標轉換
- 投放前確認：移動物體偵測、人物偵測、投放區域障礙物
- 回傳結果與心跳
- 假資料來源（fake sender、fake server），讓本模組可獨立測試

**不做**
- 飛行控制、XR 介面、Gazebo 場景（其他組員負責）
- 決定要不要投放（由操作員與 Python Server 決定）

**進階目標（有時間才做）**
- 水池偵測（鏡頭畫面分割）

## 4. 介面

> 介面格式與慣例是與組員的約定，**修改前必須先更新本文件並通知組員**，並記錄在第 13 節。

### 4.1 深度圖（Gazebo → 開發板，TCP）

| 項目 | 規格 |
|---|---|
| 連線 | TCP，Gazebo 端為 server，port **5000**，開發板主動連線；同時只服務一個連線 |
| 解析度 | 320 × 240（降低頻寬用；接收端以 header 寬高為準，不寫死） |
| 型別 / 單位 | float32、公尺、little-endian |
| 深度定義 | 沿相機光軸的 z 深度（不是到像素的直線距離） |
| 排列 | row-major，形狀 `(height, width)`，第 0 列為影像最上方 |
| 無效值 | `inf` |
| 幀率 | 約 10 FPS |
| 頻寬 | 每幀約 0.3 MB，10 FPS 約 25 Mbps |

每一幀格式：

```
[header 16 bytes][深度資料 width × height × 4 bytes]
header = struct.pack("<IId", width, height, timestamp_sec)
```

- `timestamp_sec`：取得該幀時的 Unix 時間（見 4.4）

### 4.2 鏡頭畫面（Gazebo → 開發板，GStreamer）

| 項目 | 規格 |
|---|---|
| 傳輸 | RTP / UDP，port **5600**（TBD） |
| 編碼 | H.264（TBD） |
| 解析度 / 幀率 | 640 × 480、15 FPS（TBD） |

### 4.3 Python Server ↔ 開發板（UDP JSON）

- 每個 UDP 封包 = 一則 JSON，都有 `type` 欄位
- Server → 開發板：開發板 port **6000**
- 開發板 → Server：Server port **6001**
- 單位、座標、時間依 4.4

**Server → 開發板**

無人機狀態（約 10 Hz）：
```json
{"type": "state", "t": 1730000000.12,
 "position_ned": [12.3, -4.5, -10.0], "altitude": 10.0,
 "attitude": {"roll": 1.2, "pitch": -0.8, "yaw": 90.0}}
```
- `altitude`：相對起飛點的高度，等於 `-position_ned[2]`；本模組計算以 `position_ned` 為準

任務指令（每次 `id` 加一）：
```json
{"type": "command", "id": 12, "cmd": "check_target", "target_ned": [50.0, 20.0, 0.0]}
{"type": "command", "id": 13, "cmd": "confirm_drop"}
{"type": "command", "id": 14, "cmd": "cancel"}
```
- `target_ned`：開發板只使用 N、E 兩個分量，z 由深度圖算出實際地面高度

**開發板 → Server**

地面檢查結果（回覆 `check_target`，`id` 相同）：
```json
{"type": "candidates", "id": 12, "target_ok": false, "error": null,
 "candidates": [{"ned": [52.0, 18.0, 0.3], "score": 0.92},
                {"ned": [47.5, 23.0, 0.1], "score": 0.85}]}
```
- `target_ok: true` 時 `candidates` 可為空陣列
- `score` 範圍 0～1，越高越好，最多回傳 3 個
- `ned` 的 z 為深度圖算出的地面 NED z（地面不一定在 z = 0）
- `error`：`null` / `target_not_in_view`（目標不在畫面內）/ `no_data`（沒有可用的深度圖或 state）；非 `null` 時 `target_ok: false`、`candidates` 為空陣列

投放前確認（回覆 `confirm_drop`，`id` 相同）：
```json
{"type": "drop_check", "id": 13, "safe": false, "reason": "moving_object"}
```
- `reason`：`person` / `moving_object` / `obstacle`（投放區域有凸起物）/ `no_data`；`safe: true` 時為 `null`
- 收到 `confirm_drop` 後持續檢查，狀態改變時再送一次，直到收到下一個指令或 `cancel`

心跳（每秒一次）：
```json
{"type": "heartbeat", "t": 1730000000.12}
```
- Server 超過 3 秒沒收到，視為開發板失效

**掉封包與重送**
- UDP 可能掉封包。Server 送出指令後 1 秒內沒收到對應回覆，可用**相同 `id`** 重送
- 開發板收到與最近一次指令 `id` 相同的指令時，不重新執行，直接重送上次的回覆（`confirm_drop` 則重送目前的 `drop_check` 狀態）

### 4.4 共通慣例（座標、姿態、時間）

- **單位**：距離公尺、角度「度」（沿用 MAVSDK）、時間秒
- **時間**：所有時間戳（深度圖 header、`state.t`、`heartbeat.t`）都是 Unix 時間（`time.time()`）。Gazebo 端在收到影像當下打上時間戳，不使用模擬時間；不同電腦之間需用 NTP / chrony 同步時鐘
- **世界座標系 NED**：原點為起飛點，x 北、y 東、z 下
- **機身座標系 FRD**：x 機頭、y 右、z 下
- **姿態**：roll / pitch / yaw（度），旋轉順序 ZYX（先 yaw、再 pitch、再 roll），yaw 0° 指北、順時針為正（與 MAVSDK / PX4 相同）
- **相機座標系**（OpenCV 慣例）：x 影像右、y 影像下、z 沿光軸向前
- **相機安裝**：預設朝正下方、影像上方朝機頭，即 相機 x = 機身 y、相機 y = 機身 −x、相機 z = 機身 z；實際值以 `CAMERA_MOUNT` 為準

## 5. 模組劃分

```
board/
├── comm/
│   ├── depth_receiver.py   # TCP 收深度圖 → (timestamp, ndarray)
│   ├── camera_receiver.py  # GStreamer 收鏡頭畫面 → (timestamp, ndarray BGR)
│   └── server_link.py      # UDP 收 state/command、送結果/心跳
├── perception/
│   ├── geometry.py         # 相機內參、深度 → 點雲、像素 ↔ NED
│   ├── ground_check.py     # 地面檢查與評分
│   ├── candidates.py       # 替代投放點搜尋
│   ├── motion.py           # 移動物體偵測（含無人機晃動補償）
│   └── person.py           # 人物偵測（YOLO）
├── app.py                  # 主程式：串起 comm 與 perception，處理指令狀態機
└── config.py               # 所有參數集中於此
tools/
├── fake_depth_sender.py    # 假深度圖來源
├── fake_camera_sender.py   # 假鏡頭來源（M5）
├── fake_server.py          # 假 Python Server
└── visualize.py            # 深度圖與檢查結果的繪圖函式 + 獨立檢視器
tests/
pyproject.toml              # 套件與相依設定（pip install -e ".[dev]"）
```

原則：
- `perception/` 內的函式只吃 NumPy 陣列與參數、回傳結果，不碰網路，方便單元測試
- 所有門檻與參數放 `config.py`，不寫死在程式中
- 接收層命名為 `comm`，避免與 Python 標準函式庫 `io` 同名
- 深度來源只接受一個連線：M1～M3 由 `visualize.py` 直接連線當獨立檢視器；`app.py` 執行後改用 `app.py --show` 呼叫 `visualize.py` 的繪圖函式顯示

## 6. 演算法方向

### 6.1 地面檢查（`check_target`）

1. 用相機內參把深度圖轉成相機座標系點雲
2. 用無人機姿態（roll、pitch）把點雲轉到水平座標系，排除機身傾斜影響
3. 對投放區域（`DROP_AREA`）的點用 RANSAC 擬合平面
4. 計算：
   - **坡度**：平面法向量與垂直方向的夾角
   - **粗糙度**：點到平面距離的標準差
   - **凸起物**：點到平面的最大高度差
5. 三項都低於門檻 → 安全；分數依三項加權計算（權重 `SCORE_WEIGHTS`）

### 6.2 替代點推薦

1. 將畫面可見地面切成格子（每格約等於投放面積）
2. 每格跑 6.1 評分，加入「離原目標距離」懲罰（`DISTANCE_PENALTY`）
3. 取分數最高且彼此不重疊的前 3 格
4. 格子中心像素 + 深度 → 相機座標 → 機身座標 → NED（用 `CAMERA_MOUNT`、attitude、position_ned），z 為實際地面高度

### 6.3 投放前確認（`confirm_drop`）

- **檢查範圍**：人物與移動物體看整張畫面（保守）；障礙物看無人機正下方的投放區域
- **人物偵測**：YOLO 偵測人、車、動物，畫面中出現即判定不安全（即使靜止）
  - 風險：COCO 預訓練模型很少看過從正上方俯拍的人，需用俯視畫面實測偵測率，不足時再微調模型
- **移動偵測**：用特徵點匹配估計前後兩幀之間的 homography（描述兩張畫面平面對應關係的 3×3 矩陣），補償無人機晃動、下降造成的平移、旋轉與縮放，再用幀差或背景相減找出仍在移動的區域
- **障礙物**：用深度圖對投放區域跑 6.1 的凸起物判斷，超過 `MAX_PROTRUSION` → `obstacle`
- 任一判定不安全 → `safe: false`
- 須**連續**安全 `SAFE_HOLD_SEC` 才回報 `safe: true`，避免單幀誤判
- 超過 `NO_DATA_TIMEOUT` 沒收到畫面 → `safe: false, reason: no_data`

### 6.4 水池偵測（進階）

鏡頭畫面語意分割，標出水面區域，在 6.2 評分中排除。

## 7. 參數（`config.py`）

| 參數 | 預設值 | 說明 |
|---|---|---|
| `CHECK_ALTITUDE` | 10 m（TBD） | 地面檢查時的懸停高度 |
| `DROP_ALTITUDE` | 3 m（TBD） | 投放高度 |
| `DROP_AREA` | 1.0 × 1.0 m | 投放需要的地面面積 |
| `MAX_SLOPE_DEG` | 10° | 坡度上限 |
| `MAX_ROUGHNESS` | 0.05 m | 粗糙度上限 |
| `MAX_PROTRUSION` | 0.15 m | 凸起物高度上限 |
| `RANSAC_ITERATIONS` | TBD（task 2.5 決定） | RANSAC 迭代次數 |
| `RANSAC_INLIER_DIST` | TBD（task 2.5 決定） | 點到平面距離小於此值算內點 |
| `SCORE_WEIGHTS` | TBD（task 2.6 決定） | 坡度、粗糙度、凸起物在分數中的權重 |
| `DISTANCE_PENALTY` | TBD（task 3.4 決定） | 離原目標距離的扣分 |
| `MAX_CANDIDATES` | 3 | 最多推薦幾個點 |
| `SAFE_HOLD_SEC` | 3 s | 連續安全多久才回報 safe |
| `NO_DATA_TIMEOUT` | 1 s | 多久沒畫面視為 no_data |
| `HEARTBEAT_HZ` | 1 | 心跳頻率 |
| `CAMERA_HFOV_DEG` | TBD | 深度相機水平視角 |
| `CAMERA_RANGE_M` | TBD | 深度相機量測範圍 |
| `CAMERA_MOUNT` | 正下方、影像上方朝機頭（TBD） | 相機安裝位置與朝向（見 4.4） |

TBD 參數在對應 task 做到時與使用者確認數值。

## 8. 里程碑

| | 內容 | 完成條件 |
|---|---|---|
| **M1** | 收深度圖 + 視覺化 | fake sender 送出，接收端以彩色深度圖顯示，即時印出距離 |
| **M2** | 地面檢查 | 對假資料中的平地回報安全、方塊與斜坡回報不安全，並在畫面標出 |
| **M3** | 替代點 + 座標轉換 | 目標點不安全時輸出 3 個候選 NED 座標，在畫面標出位置；座標轉換有單元測試 |
| **M4** | UDP 通訊 | 與 fake server 完成 check_target → candidates 流程與心跳 |
| **M5** | 投放前確認 | 鏡頭畫面中有人或移動物體時回報 unsafe，離開並持續 3 秒後回報 safe |
| **M6** | 移植 NPU | YOLO 在聯詠開發板 NPU 上執行，記錄 FPS |
| M7 | 水池偵測（進階） | 鏡頭畫面中的水面被排除在候選點外 |

M1 完成即可作為課程 GitHub 提交。

## 9. 測試方式

- 單元測試（pytest）：`perception/` 內的函式用合成深度圖測試（平地、斜坡、方塊、含 inf）
- 整合測試：`tools/fake_depth_sender.py` + `tools/fake_server.py` 跑完整流程，不依賴組員
- 實際資料：自行執行 PX4 SITL + Gazebo 深度相機機型錄製深度圖（`.npy`），作為回歸測試資料

## 10. 技術選擇

- Python 3.10+，以 `pyproject.toml` 管理相依套件
- NumPy、OpenCV（`opencv-python`）
- GStreamer（透過 OpenCV 或 PyGObject 接收）
- YOLO（M5 起；M6 依聯詠 SDK 支援的格式轉換）

## 11. 給 AI 協作者的規則

見 `CLAUDE.md`。

## 12. 待確認事項（TBD）

見 `docs/questions.md`。

## 13. 變更紀錄

| 日期 | 變更 | 需通知 |
|---|---|---|
| 2026-10-26 | 4.1 深度圖解析度 640×480 → 320×240；明定 z 深度、row-major、單一連線、時間戳為 Unix 時間 | Gazebo |
| 2026-10-26 | 4.3 `candidates` 新增 `error` 欄位；候選點 z 改為實際地面高度；新增掉封包重送規則；明定 `altitude` 與 `target_ned` 的用法 | Python Server |
| 2026-10-26 | 新增 4.4 共通慣例（時間、座標系、姿態旋轉順序、相機安裝） | 全體 |
