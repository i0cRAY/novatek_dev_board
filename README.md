## 目標

> 確保投放點是安全的，沒有障礙物或水池

飛到目的地時利用深度畫面判斷地面坡度與凸起物，水池可能需要做地面分割。

如果目標點不適合，推薦安全的投放點給操作員選擇

投放前再次確認下方無人，確認安全才允許投放。

## 預計部署在聯詠板子上的部分

- 接收：深度圖、鏡頭畫面、無人機狀態與指令
- 地面檢查：坡度、凸起物判斷，推薦替代投放點
- 投放前確認：移動物體偵測、人物偵測
- 水池判斷：影像分割模型
- 回傳：檢查結果與心跳

## 安裝

需要 Python 3.10 以上。

```bash
git clone <repo 網址>
cd novatek_dev_board
python3 -m venv .venv            # 建立虛擬環境（獨立的 Python 套件空間）
source .venv/bin/activate        # 啟用虛擬環境（Windows：.venv\Scripts\activate）
pip install -e ".[dev]"          # 安裝本專案與相依套件（numpy、opencv-python、pytest）
pytest                           # 執行測試，應顯示 passed
```

`-e` 代表「可編輯安裝」：修改 `board/` 裡的程式後不需要重新安裝。
