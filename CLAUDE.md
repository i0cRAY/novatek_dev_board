# CLAUDE.md

## 專案概要

XR 無人機救災物資投放專案中的**開發板感知模組**，最終部署在聯詠開發板上。
負責判斷投放點是否安全：地面檢查（坡度、凸起物、水池）、推薦替代投放點、投放前確認下方無人與無移動物體。
本模組只負責判斷與推薦，不控制無人機。

開發階段資料來源是 Gazebo 模擬（透過網路傳入），組員未就緒時用 `tools/` 下的假資料來源測試。

## 開始工作前

1. 讀 `docs/spec.md`：目標、介面格式、座標與時間慣例、模組劃分、演算法方向、參數
2. 讀 `docs/task.md`：找到目前要做的 task 與完成條件
3. 若使用者沒指定 task，做 `docs/task.md` 中第一個未打勾的項目

## 工作方式

- **一次只做一個 task**。完成條件達成後停下來，不要自行接著做下一個
- 完成後在 `docs/task.md` 把該項打勾，並向使用者回報：
  - **做了什麼**：新增／修改了哪些檔案、主要做法
  - **預期結果**：要執行什麼指令、應該看到什麼
  - **實際驗證**：測試或示範實際跑出來的結果
- 回報後**詢問使用者要不要 commit**；未經同意不得 commit 或 push
- 不確定的設計決策先問，不要自行決定
- 不要做 task 範圍外的功能、重構或「順便」的改進；發現問題就提出來

## 不可違反的規則

- **不得修改 `docs/spec.md` 第 4 節的介面格式與慣例**（TCP header、port、UDP JSON 欄位、座標與時間慣例）。這是與組員的約定，若真的需要修改，先提出理由並等使用者同意，修改後記錄在 spec 第 13 節
- 所有參數與門檻放 `board/config.py`，不寫死在程式中
- `board/perception/` 只處理 NumPy 陣列，**不得**引用 socket、網路或 I/O 相關程式
- 接收資料（`board/comm/`）與分析資料（`board/perception/`）保持分離，之後換成真實相機時只改 comm 層

## 程式慣例

- Python 3.10+，使用 type hints
- 單位：距離公尺、角度在介面與 config 中用「度」，內部計算可轉弧度但要在函式邊界轉回
- 座標系：依 spec 4.4（世界 NED、機身 FRD、相機 OpenCV 慣例）；函式 docstring 註明輸入輸出所在的座標系
- 深度圖：`float32`、`(H, W)`，值為沿光軸的 z 深度，無效值為 `inf`，所有處理都必須能容忍 `inf` / `NaN`
- 深度圖寬高以 header 為準，不寫死解析度
- 註解與 docstring 用繁體中文
- 函式保持小而純粹，方便單元測試

## 測試

- 每個 task 都要附測試或可執行的示範
- `board/perception/` 的功能用 `tests/synthetic.py` 產生的合成深度圖測試
- 涉及座標轉換的功能，測試要涵蓋多個 yaw 角度與有 roll/pitch 的情況

## 常用指令

```bash
pip install -e ".[dev]"                   # 安裝本專案（可 import board）與相依套件
pytest                                    # 執行所有測試
python tools/fake_depth_sender.py         # 假深度圖來源（port 5000）
python tools/fake_server.py               # 假 Python Server（M4 起）
python tools/visualize.py                 # 深度圖視覺化（M1～M3 的獨立檢視器）
```

## 溝通

- 用繁體中文回覆
- 使用者正在學習中，解釋時避免堆疊術語；用到新概念（例如 RANSAC、光流）時簡短說明它是什麼、為什麼用
