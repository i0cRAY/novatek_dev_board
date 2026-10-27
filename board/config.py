"""所有參數與門檻集中於此（對應 docs/spec.md 第 7 節）。

單位：距離公尺、角度「度」、時間秒。
標示「暫定」的數值尚未確認，做到對應 task 或組員回覆後再更新。
"""

# ── 飛行高度 ─────────────────────────────────────────────

# 地面檢查時的懸停高度（m）。暫定，待飛控（吳泯蓁）確認
CHECK_ALTITUDE: float = 10.0

# 投放高度（m）。暫定，待飛控（吳泯蓁）確認
DROP_ALTITUDE: float = 3.0

# ── 地面檢查 ─────────────────────────────────────────────

# 物資箱大小（長, 寬），m。暫定估計值，待使用者確認
PAYLOAD_SIZE: tuple[float, float] = (0.4, 0.4)

# 懸停位置誤差：無人機懸停時偏離目標的距離（m）。暫定估計值，待吳泯蓁確認
HOVER_POS_ERROR: float = 0.3

# 落下偏移：從投放高度落下時因風、彈跳造成的偏移（m）。暫定估計值，待使用者確認
DROP_DRIFT: float = 0.2

# 投放需要的地面面積（長, 寬），m
# = 物資大小 + 2 ×（位置誤差 + 落下偏移），乘 2 是因為兩側都可能偏
DROP_AREA: tuple[float, float] = (
    PAYLOAD_SIZE[0] + 2 * (HOVER_POS_ERROR + DROP_DRIFT),
    PAYLOAD_SIZE[1] + 2 * (HOVER_POS_ERROR + DROP_DRIFT),
)

# 坡度上限（度）
MAX_SLOPE_DEG: float = 10.0

# 粗糙度上限：點到擬合平面距離的標準差（m）
MAX_ROUGHNESS: float = 0.05

# 凸起物高度上限：點到擬合平面的最大高度差（m）
MAX_PROTRUSION: float = 0.15

# RANSAC 迭代次數。暫定，task 2.5 與使用者確認
RANSAC_ITERATIONS: int = 100

# RANSAC 內點門檻：點到平面距離小於此值算內點（m）。暫定，task 2.5 與使用者確認
RANSAC_INLIER_DIST: float = 0.03

# 坡度、粗糙度、凸起物在分數中的權重（總和為 1）。暫定，task 2.6 與使用者確認
SCORE_WEIGHTS: dict[str, float] = {
    "slope": 1 / 3,
    "roughness": 1 / 3,
    "protrusion": 1 / 3,
}

# ── 替代點推薦 ───────────────────────────────────────────

# 離原目標每公尺扣的分數。暫定，task 3.4 與使用者確認
DISTANCE_PENALTY: float = 0.02

# 最多推薦幾個候選點
MAX_CANDIDATES: int = 3

# ── 投放前確認 ───────────────────────────────────────────

# 連續安全多久才回報 safe（s）
SAFE_HOLD_SEC: float = 3.0

# 多久沒收到畫面視為 no_data（s）
NO_DATA_TIMEOUT: float = 1.0

# ── 通訊 ─────────────────────────────────────────────────

# 心跳頻率（Hz）
HEARTBEAT_HZ: float = 1.0

# ── 深度相機 ─────────────────────────────────────────────

# 深度相機水平視角（度）。暫定，採 Gazebo 相機預設值 60°，待王邑安確認
CAMERA_HFOV_DEG: float = 60.0

# 深度相機量測範圍（最近, 最遠），m。暫定，需涵蓋 CHECK_ALTITUDE，待王邑安確認
CAMERA_RANGE_M: tuple[float, float] = (0.1, 20.0)

# 相機安裝位置與朝向（座標系定義見 spec 4.4）。暫定，待王邑安確認
#   offset_frd：相機在機身 FRD 座標系中的位置（m）
#   rotation：相機座標 → 機身座標的旋轉矩陣，機身向量 = rotation × 相機向量
# 預設朝正下方、影像上方朝機頭：相機 x = 機身 y、相機 y = 機身 −x、相機 z = 機身 z
CAMERA_MOUNT: dict[str, tuple] = {
    "offset_frd": (0.0, 0.0, 0.0),
    "rotation": (
        (0.0, -1.0, 0.0),
        (1.0, 0.0, 0.0),
        (0.0, 0.0, 1.0),
    ),
}
