#!/usr/bin/env python3
"""Render approved infographic assets plus scene audio into a vertical MP4.

The input is a JSON manifest. Paths are resolved relative to the manifest file,
so the repository contains no account paths or private content assumptions.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFilter, ImageFont

DEFAULT_WIDTH = 1080
DEFAULT_HEIGHT = 1920
DEFAULT_FPS = 30


def find_font(explicit: str | None = None) -> str:
    candidates = [
        explicit,
        os.environ.get("VIDEO_FONT_PATH"),
        "/System/Library/Fonts/Hiragino Sans GB.ttc",
        "/System/Library/Fonts/PingFang.ttc",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.otf",
    ]
    for candidate in candidates:
        if candidate and Path(candidate).exists():
            return candidate
    raise FileNotFoundError(
        "No CJK font found. Pass --font or set VIDEO_FONT_PATH."
    )


def make_font(path: str, size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    try:
        return ImageFont.truetype(path, size=size, index=1 if bold else 0)
    except OSError:
        return ImageFont.truetype(path, size=size)


def wrap_text(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont, width: int) -> list[str]:
    lines: list[str] = []
    current = ""
    for char in text:
        candidate = current + char
        if not current or draw.textlength(candidate, font=font) <= width:
            current = candidate
        else:
            lines.append(current)
            current = char
    if current:
        lines.append(current)
    return lines


def rounded(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], radius: int,
            fill: tuple[int, int, int], outline: tuple[int, int, int] | None = None,
            width: int = 1) -> None:
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def create_slide(asset: Path, output: Path, label: str, title: str, caption: str,
                 index: int, total: int, theme: str, font_path: str,
                 width: int, height: int) -> None:
    source = Image.open(asset).convert("RGB")
    if theme == "mint":
        background = (242, 250, 247)
        accent = (13, 148, 136)
        accent2 = (16, 185, 129)
        ink = (19, 78, 74)
        sub = (82, 122, 117)
    else:
        background = (243, 246, 250)
        accent = (79, 70, 229)
        accent2 = (14, 165, 233)
        ink = (30, 41, 59)
        sub = (95, 108, 125)

    canvas = Image.new("RGB", (width, height), background)
    glow = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow)
    glow_draw.ellipse((width - 520, -260, width + 260, 520), fill=(*accent2, 22))
    canvas = Image.alpha_composite(canvas.convert("RGBA"), glow).convert("RGB")
    draw = ImageDraw.Draw(canvas)

    header_font = make_font(font_path, 25, True)
    draw.rectangle((54, 61, 92, 67), fill=accent)
    draw.text((110, 46), label, font=header_font, fill=sub)
    page = f"{index:02d} / {total:02d}"
    page_width = draw.textlength(page, font=header_font)
    draw.text((width - 54 - page_width, 46), page, font=header_font, fill=sub)
    draw.line((54, 132, width - 54, 132), fill=(210, 219, 229), width=2)

    max_width, max_height = width - 108, 1460
    scale = min(max_width / source.width, max_height / source.height)
    image_size = (max(1, int(source.width * scale)), max(1, int(source.height * scale)))
    image = source.resize(image_size, Image.Resampling.LANCZOS)
    x = (width - image_size[0]) // 2
    y = 176 + (max_height - image_size[1]) // 2

    shadow = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    shadow_draw = ImageDraw.Draw(shadow)
    shadow_draw.rounded_rectangle(
        (x - 10, y - 10, x + image_size[0] + 10, y + image_size[1] + 10),
        radius=28,
        fill=(25, 40, 60, 30),
    )
    shadow = shadow.filter(ImageFilter.GaussianBlur(12))
    canvas = Image.alpha_composite(canvas.convert("RGBA"), shadow).convert("RGB")
    draw = ImageDraw.Draw(canvas)
    rounded(draw, (x - 5, y - 5, x + image_size[0] + 5, y + image_size[1] + 5),
            24, (255, 255, 255), outline=(214, 222, 231), width=2)
    canvas.paste(image, (x, y))

    panel_y = height - 240
    rounded(draw, (54, panel_y, width - 54, height - 75), 26,
            (255, 255, 255), outline=(218, 225, 233), width=2)
    draw.rectangle((54, panel_y, 68, height - 75), fill=accent)
    title_font = make_font(font_path, 36, True)
    title_y = panel_y + 24
    for line in wrap_text(draw, title, title_font, width - 190)[:2]:
        draw.text((96, title_y), line, font=title_font, fill=ink)
        title_y += 47
    caption_font = make_font(font_path, 25)
    caption_y = min(title_y + 8, panel_y + 111)
    for line in wrap_text(draw, caption, caption_font, width - 220)[:2]:
        draw.text((96, caption_y), line, font=caption_font, fill=sub)
        caption_y += 34
    draw.text((54, height - 49), "AI CONTENT PIPELINE", font=make_font(font_path, 21, True), fill=sub)
    output.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(output, quality=95)


def duration(path: Path) -> float:
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
        capture_output=True, text=True, check=True,
    )
    return float(result.stdout.strip())


def run(command: list[str]) -> None:
    print("+", " ".join(str(part) for part in command))
    subprocess.run(command, check=True)


def resolve(root: Path, value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else root / path


def load_manifest(path: Path) -> tuple[dict[str, Any], Path]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or not isinstance(data.get("scenes"), list) or not data["scenes"]:
        raise ValueError("Manifest must be an object with a non-empty scenes list")
    return data, path.parent


def build(manifest_path: Path, output_override: str | None = None) -> Path:
    manifest, root = load_manifest(manifest_path)
    width = int(manifest.get("width", DEFAULT_WIDTH))
    height = int(manifest.get("height", DEFAULT_HEIGHT))
    fps = int(manifest.get("fps", DEFAULT_FPS))
    if (width, height) != (1080, 1920):
        raise ValueError("This vertical-video renderer requires width=1080 and height=1920")
    if fps <= 0:
        raise ValueError("fps must be positive")

    output = resolve(root, output_override or str(manifest.get("out_dir", "out")))
    slides = output / "slides"
    scenes_dir = output / "scenes"
    slides.mkdir(parents=True, exist_ok=True)
    scenes_dir.mkdir(parents=True, exist_ok=True)
    for old in slides.glob("*.png"):
        old.unlink()
    for old in scenes_dir.glob("*.mp4"):
        old.unlink()

    font_path = find_font(manifest.get("font"))
    label = str(manifest.get("label", "AI CONTENT PIPELINE"))
    theme = str(manifest.get("theme", "frost"))
    scenes = manifest["scenes"]
    rendered: list[dict[str, Any]] = []

    for index, scene in enumerate(scenes, start=1):
        if not isinstance(scene, dict):
            raise ValueError(f"scene {index} must be an object")
        asset = resolve(root, str(scene["asset"]))
        audio = resolve(root, str(scene["audio"]))
        if not asset.exists():
            raise FileNotFoundError(asset)
        if not audio.exists():
            raise FileNotFoundError(audio)
        slide = slides / f"scene-{index:03d}.png"
        video = scenes_dir / f"scene-{index:03d}.mp4"
        create_slide(asset, slide, label, str(scene.get("title", "")),
                     str(scene.get("caption", "")), index, len(scenes), theme,
                     font_path, width, height)
        audio_duration = duration(audio)
        run([
            "ffmpeg", "-y", "-v", "error", "-loop", "1", "-i", str(slide),
            "-i", str(audio), "-c:v", "libx264", "-preset", "medium",
            "-tune", "stillimage", "-pix_fmt", "yuv420p", "-r", str(fps),
            "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
            "-t", f"{audio_duration:.3f}", "-movflags", "+faststart", str(video),
        ])
        rendered.append({
            "scene": index,
            "asset": str(asset),
            "audio": str(audio),
            "slide": str(slide),
            "video": str(video),
            "audio_duration": audio_duration,
            "title": scene.get("title", ""),
            "caption": scene.get("caption", ""),
        })

    concat = output / "concat.txt"
    concat.write_text(
        "\n".join(f"file '{scenes_dir / f'scene-{i:03d}.mp4'}'" for i in range(1, len(scenes) + 1)) + "\n",
        encoding="utf-8",
    )
    final = output / "final.mp4"
    run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0",
         "-i", str(concat), "-c", "copy", "-movflags", "+faststart", str(final)])
    (output / "manifest.resolved.json").write_text(
        json.dumps({"source": str(manifest_path), "scenes": rendered}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"FINAL {final}")
    print(f"DURATION {duration(final):.3f}")
    print(f"SCENES {len(rendered)}")
    return final


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path, help="JSON scene manifest")
    parser.add_argument("--out-dir", help="Override manifest out_dir")
    parser.add_argument("--font", help="CJK font path (also accepted in manifest or VIDEO_FONT_PATH)")
    args = parser.parse_args()
    if args.font:
        os.environ["VIDEO_FONT_PATH"] = args.font
    if shutil.which("ffmpeg") is None or shutil.which("ffprobe") is None:
        raise SystemExit("ffmpeg and ffprobe are required")
    build(args.manifest, args.out_dir)


if __name__ == "__main__":
    main()
