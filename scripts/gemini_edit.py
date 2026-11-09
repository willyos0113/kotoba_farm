#!/usr/bin/env python3
"""Gemini (Nano Banana) で写真を編集する。通行人の除去と明るさ・色味の調整が目的。

使い方:
    .venv/bin/python scripts/gemini_edit.py <入力画像> <出力画像> --preset remove-people
    .venv/bin/python scripts/gemini_edit.py <入力画像> <出力画像> --preset relight
    .venv/bin/python scripts/gemini_edit.py <入力画像> <出力画像> "自由な指示（英語推奨）"

- API キーは環境変数 GEMINI_API_KEY から読む。
- モデルは GEMINI_IMAGE_MODEL で変更可（既定: gemini-2.5-flash-image）。
- 出力の拡張子は出力パスに合わせて変換する（.jpg / .jpeg / .png）。
- 入力ファイルは絶対に上書きしない。出力が既にある場合は --force が必要。
"""
import argparse
import base64
import io
import json
import mimetypes
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

from PIL import Image

DEFAULT_MODEL = "gemini-2.5-flash-image"

GUARDRAIL = (
    " Keep everything else exactly as in the original photo: do not change, add or remove "
    "any text, signs, menus, food, objects, buildings or the main subject. "
    "Do not change the framing, aspect ratio or perspective. Photorealistic result."
)

PRESETS = {
    "remove-people": (
        "Remove the passers-by and background people from this photo and fill in the "
        "areas behind them naturally to match the surrounding scene."
    ),
    "relight": (
        "Adjust the lighting of this photo: correct exposure and white balance so it looks "
        "natural and bright, recover dark shadows and blown highlights, without changing "
        "the content of the scene."
    ),
}


def call_gemini(model: str, api_key: str, prompt: str, image_path: Path) -> bytes:
    mime = mimetypes.guess_type(image_path.name)[0] or "image/jpeg"
    body = {
        "contents": [{
            "parts": [
                {"text": prompt},
                {"inline_data": {"mime_type": mime,
                                 "data": base64.b64encode(image_path.read_bytes()).decode()}},
            ]
        }]
    }
    req = urllib.request.Request(
        f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json", "x-goog-api-key": api_key},
    )
    try:
        with urllib.request.urlopen(req, timeout=180) as res:
            data = json.load(res)
    except urllib.error.HTTPError as e:
        sys.exit(f"API エラー {e.code}: {e.read().decode(errors='replace')[:500]}")

    parts = (data.get("candidates") or [{}])[0].get("content", {}).get("parts", [])
    for part in parts:
        inline = part.get("inlineData") or part.get("inline_data")
        if inline:
            return base64.b64decode(inline["data"])
    texts = " ".join(p.get("text", "") for p in parts).strip()
    sys.exit(f"画像が返ってこなかった。モデルの返答: {texts or data}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("input", type=Path)
    ap.add_argument("output", type=Path)
    ap.add_argument("prompt", nargs="?", default="", help="自由な指示（--preset に追加される）")
    ap.add_argument("--preset", choices=PRESETS)
    ap.add_argument("--force", action="store_true", help="出力が既にあっても上書きする")
    args = ap.parse_args()

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        sys.exit("GEMINI_API_KEY が設定されていない。")
    if not args.input.is_file():
        sys.exit(f"入力画像がない: {args.input}")
    if args.input.resolve() == args.output.resolve():
        sys.exit("入力と出力が同じパス。原本は上書きしない。")
    if args.output.exists() and not args.force:
        sys.exit(f"出力が既にある: {args.output}（上書きするなら --force）")
    if not (args.preset or args.prompt):
        sys.exit("--preset か指示文のどちらかが必要。")

    prompt = " ".join(filter(None, [PRESETS.get(args.preset, ""), args.prompt])) + GUARDRAIL
    model = os.environ.get("GEMINI_IMAGE_MODEL", DEFAULT_MODEL)
    print(f"model={model}\nprompt={prompt}", file=sys.stderr)

    img = Image.open(io.BytesIO(call_gemini(model, api_key, prompt, args.input)))
    ext = args.output.suffix.lower()
    if ext in (".jpg", ".jpeg"):
        img = img.convert("RGB")
        img.save(args.output, quality=95)
    elif ext == ".png":
        img.save(args.output)
    else:
        sys.exit(f"対応していない拡張子: {ext}")
    print(f"保存した: {args.output}（{img.size[0]}x{img.size[1]}）")


if __name__ == "__main__":
    main()
