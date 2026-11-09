---
name: gemini-photo-edit
description: 用 Gemini（Nano Banana）加工 output/posts/ 的照片：去除路人、調整光線與色調。使用者要修圖、去路人、調亮、修色偏時使用。
---

# 照片加工（Gemini）

腳本：`scripts/gemini_edit.py`（用 `.venv/bin/python` 執行；沒有 `.venv` 時先 `python3 -m venv .venv && .venv/bin/pip install -r scripts/requirements.txt`）。

適用範圍只有**去路人**和**調光**。改菜色、招牌／菜單上的字、人物的臉都不交給 AI。簡單的裁切、亮度調整用 Pillow 就好，不必送 AI。

## 流程

1. **原圖先留著**：把要加工的圖放在該主題的 `materials/`（已經在 `photos/` 的用 `cp` 複製過去，不要移動），檔名維持 `NN名稱.副檔名`。
2. **加工**，輸出到 `materials/`，檔名加英文後綴：`_nopeople`（去路人）、`_relit`（調光），兩者都做就 `_nopeople_relit`。例：`01ノッチ店内_nopeople.jpeg`
   ```
   .venv/bin/python scripts/gemini_edit.py <入力> <出力> --preset remove-people
   .venv/bin/python scripts/gemini_edit.py <入力> <出力> --preset relight
   .venv/bin/python scripts/gemini_edit.py <入力> <出力> "Remove only the man in the red jacket on the left"
   ```
   - 自由指示用英文，寫得越具體越好（哪個人、哪個位置）。可以跟 `--preset` 併用。
   - 輸出的副檔名要和原檔一致（`.jpg`／`.jpeg`），腳本會自動轉檔，不用 PNG。
   - 腳本不會覆蓋輸入；輸出已存在時要加 `--force`。
3. **請使用者並排檢查**原圖和結果（改到不該改的地方就重跑或放棄）。我只能先描述看到的差異，不能代替使用者判斷有沒有被改壞。
4. 使用者確認後，才複製到 `photos/NN名稱.副檔名`（沿用 posts-format 的命名，不含後綴）。
5. 在該主題 `plan.md` 的 `## 画像リスト` 備考寫：`materials/○○ を Gemini で編集（通行人除去／調光）。指示：…`。

## 注意

- `GEMINI_API_KEY` 在環境變數裡，不要把 key 寫進任何檔案或 commit。
- 模型預設 `gemini-2.5-flash-image`，要換就設 `GEMINI_IMAGE_MODEL`。
- Gemini 輸出的解析度可能和原圖不同，用在 Discord／Instagram 前確認尺寸。
