#!/usr/bin/env python3
"""
cover_generator.py — Pillow でカバー画像を自動生成（完全無料）

Pinterest 推奨: 1000x1500px (2:3)
Gumroad thumbnail: 1280x720px (16:9)
→ 1000x1500 で作って両方に使う
"""

import json
import random
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

BASE_DIR     = Path(__file__).parent
PRODUCTS_DIR = BASE_DIR / "products"
FONTS_DIR    = BASE_DIR / "assets" / "fonts"

# カラーパレット（プロフェッショナル系・5テーマ）
THEMES = [
    {"bg": [(15, 23, 42), (30, 58, 138)],   "accent": (99, 179, 237),  "text": (255, 255, 255)},  # Navy
    {"bg": [(17, 24, 39), (31, 41, 55)],    "accent": (167, 243, 208), "text": (255, 255, 255)},  # Dark Green
    {"bg": [(55, 48, 163), (109, 40, 217)], "accent": (251, 191, 36),  "text": (255, 255, 255)},  # Purple-Gold
    {"bg": [(15, 23, 42), (30, 41, 59)],    "accent": (251, 113, 133), "text": (255, 255, 255)},  # Dark-Rose
    {"bg": [(6, 78, 59), (4, 120, 87)],     "accent": (252, 211, 77),  "text": (255, 255, 255)},  # Forest-Gold
]

CATEGORY_ICONS = {
    "AI":            "✦",
    "Programming":   "⌨",
    "Business":      "◈",
    "Productivity":  "◉",
    "Design":        "◎",
    "Marketing":     "▲",
    "Finance":       "◆",
    "Writing":       "✎",
    "default":       "★",
}

W, H = 1000, 1500


def _gradient(draw: ImageDraw.ImageDraw, color1: tuple, color2: tuple):
    for y in range(H):
        t = y / H
        r = int(color1[0] + (color2[0] - color1[0]) * t)
        g = int(color1[1] + (color2[1] - color1[1]) * t)
        b = int(color1[2] + (color2[2] - color1[2]) * t)
        draw.line([(0, y), (W, y)], fill=(r, g, b))


def _get_font(size: int):
    """システムフォントをフォールバック付きで取得"""
    candidates = [
        "/System/Library/Fonts/Helvetica.ttc",
        "/System/Library/Fonts/Arial.ttf",
        "/Library/Fonts/Arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    ]
    for path in candidates:
        try:
            return ImageFont.truetype(path, size)
        except (IOError, OSError):
            continue
    return ImageFont.load_default()


def _wrap_text(text: str, font, max_width: int, draw: ImageDraw.ImageDraw) -> list[str]:
    words = text.split()
    lines, current = [], ""
    for word in words:
        test = f"{current} {word}".strip()
        bbox = draw.textbbox((0, 0), test, font=font)
        if bbox[2] - bbox[0] <= max_width:
            current = test
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def generate_cover(spec: dict, output_path: Path) -> Path:
    """
    spec: product spec dict (name, category, subcategory, price_usd, product_type)
    output_path: 保存先（.png）
    """
    name      = spec.get("name", "Digital Product")
    category  = spec.get("category", "default")
    subcat    = spec.get("subcategory", "")
    price     = spec.get("price_usd", spec.get("price", 9))
    ptype     = spec.get("product_type", "guide")

    # テーマを category で固定（毎回同じになるよう hash）
    theme_idx = hash(category) % len(THEMES)
    theme     = THEMES[theme_idx]
    icon      = CATEGORY_ICONS.get(category, CATEGORY_ICONS["default"])

    img  = Image.new("RGB", (W, H))
    draw = ImageDraw.Draw(img)

    # 背景グラデーション
    _gradient(draw, theme["bg"][0], theme["bg"][1])

    # 装飾：右下に大きな半透明円
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    odraw   = ImageDraw.Draw(overlay)
    odraw.ellipse([(W - 400, H - 500), (W + 300, H + 300)],
                  fill=(*theme["accent"], 20))
    odraw.ellipse([(W - 250, H - 350), (W + 200, H + 200)],
                  fill=(*theme["accent"], 15))
    img.paste(overlay, mask=overlay.split()[3])

    # アクセントライン（上部）
    draw.rectangle([(60, 80), (60 + 80, 86)], fill=theme["accent"])

    # カテゴリアイコン（大）
    icon_font = _get_font(120)
    draw.text((60, 100), icon, font=icon_font, fill=(*theme["accent"], 220))

    # カテゴリラベル
    cat_font = _get_font(28)
    cat_text = f"{category.upper()}  ·  {subcat.upper()}" if subcat else category.upper()
    draw.text((60, 270), cat_text, font=cat_font, fill=(*theme["accent"], 200))

    # タイトル（メイン）
    title_font  = _get_font(72)
    title_small = _get_font(58)
    padding     = 60
    max_w       = W - padding * 2

    # 長いタイトルは小さいフォントで
    lines = _wrap_text(name, title_font, max_w, draw)
    if len(lines) > 3:
        lines = _wrap_text(name, title_small, max_w, draw)
        used_font = title_small
    else:
        used_font = title_font

    y = 360
    line_h = used_font.size + 16
    for line in lines[:4]:
        draw.text((padding, y), line, font=used_font, fill=theme["text"])
        y += line_h

    # 区切り線
    draw.rectangle([(padding, y + 40), (W - padding, y + 43)],
                   fill=(*theme["accent"], 120))

    # 商品タイプバッジ
    badge_font = _get_font(30)
    type_labels = {
        "prompt_pack": "PROMPT PACK",
        "ebook":       "eBOOK",
        "template":    "TEMPLATE",
        "guide":       "GUIDE",
        "checklist":   "CHECKLIST",
        "toolkit":     "TOOLKIT",
    }
    type_label = type_labels.get(ptype, ptype.upper().replace("_", " "))
    bx, by = padding, y + 70
    bbox = draw.textbbox((bx, by), type_label, font=badge_font)
    draw.rectangle(
        [bbox[0] - 12, bbox[1] - 8, bbox[2] + 12, bbox[3] + 8],
        fill=theme["accent"]
    )
    draw.text((bx, by), type_label, font=badge_font, fill=(15, 23, 42))

    # 価格
    price_font = _get_font(52)
    price_text = f"${price}"
    price_bbox = draw.textbbox((0, 0), price_text, font=price_font)
    price_w    = price_bbox[2] - price_bbox[0]
    draw.text((W - padding - price_w, y + 62), price_text,
              font=price_font, fill=theme["accent"])

    # 下部：ブランド
    brand_font  = _get_font(26)
    brand_text  = "AETERNA  ·  instant download"
    draw.text((padding, H - 80), brand_text,
              font=brand_font, fill=(*theme["text"], 140))
    # ブランドライン
    draw.rectangle([(padding, H - 95), (W - padding, H - 92)],
                   fill=(*theme["accent"], 80))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(str(output_path), "PNG", optimize=True)
    return output_path


def generate_all_missing(limit: int = 999) -> int:
    """products/ 以下の全商品にカバー画像がなければ生成"""
    generated = 0
    dirs = sorted(PRODUCTS_DIR.iterdir()) if PRODUCTS_DIR.exists() else []

    for d in dirs:
        if not d.is_dir():
            continue
        cover = d / "cover.png"
        if cover.exists():
            continue
        spec_file = d / "spec.json"
        if not spec_file.exists():
            continue
        spec = json.loads(spec_file.read_text())
        try:
            generate_cover(spec, cover)
            print(f"  ✓ {spec.get('name', d.name)[:50]}")
            generated += 1
        except Exception as e:
            print(f"  ✗ {d.name}: {e}")
        if generated >= limit:
            break

    return generated


if __name__ == "__main__":
    print("カバー画像を一括生成します...")
    n = generate_all_missing()
    print(f"\n完了: {n} 件生成しました")
    if n == 0:
        print("（全件生成済み or products/ が空）")
