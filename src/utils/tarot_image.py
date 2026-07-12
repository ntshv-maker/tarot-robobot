from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from src.engines.tarot import ARCANA_NAMES, card_image_path


def ensure_tarot_assets(assets_dir: Path | None = None) -> None:
    assets_dir = assets_dir or Path(__file__).resolve().parents[2] / "assets" / "tarot"
    assets_dir.mkdir(parents=True, exist_ok=True)
    colors = [
        (45, 27, 78),
        (78, 45, 120),
        (30, 60, 90),
        (90, 30, 60),
        (60, 90, 30),
    ]
    for i in range(22):
        path = assets_dir / f"{i:02d}.png"
        if path.exists():
            continue
        color = colors[i % len(colors)]
        img = Image.new("RGB", (400, 640), color=color)
        draw = ImageDraw.Draw(img)
        try:
            font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial.ttf", 28)
            font_sm = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial.ttf", 20)
        except OSError:
            font = ImageFont.load_default()
            font_sm = font
        draw.text((20, 280), ARCANA_NAMES[i], fill=(255, 255, 255), font=font)
        draw.text((20, 330), f"Аркан {i}", fill=(220, 220, 255), font=font_sm)
        img.save(path)


def render_daily_card_image(user_name: str, arcana_index: int, ref_date: str, assets_dir: Path | None = None) -> Path:
    assets_dir = assets_dir or Path(__file__).resolve().parents[2] / "assets" / "tarot"
    ensure_tarot_assets(assets_dir)
    base = Image.open(card_image_path(arcana_index, assets_dir)).convert("RGBA")
    overlay = Image.new("RGBA", base.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    draw.rectangle([(0, base.height - 100), (base.width, base.height)], fill=(0, 0, 0, 160))
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial.ttf", 18)
    except OSError:
        font = ImageFont.load_default()
    draw.text((16, base.height - 80), ref_date, fill=(255, 255, 255), font=font)
    draw.text((16, base.height - 50), user_name[:24], fill=(255, 220, 180), font=font)
    result = Image.alpha_composite(base, overlay)
    out_dir = assets_dir / "generated"
    out_dir.mkdir(exist_ok=True)
    out_path = out_dir / f"daily_{arcana_index}_{ref_date.replace('.', '')}.png"
    result.convert("RGB").save(out_path)
    return out_path
