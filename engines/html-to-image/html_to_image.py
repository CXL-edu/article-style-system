#!/usr/bin/env python3
"""
html-to-image —— HTML/SVG → PNG 截图引擎（通用内核，平台无关）

基于 2026-08-16 实测沉淀：
- X 长图（1080 宽，最长 8192px 完整文章）
- 公众号 2.35:1 原生封面（1600×681 → 2x = 3200×1362）

原理：无头 Chrome `--headless=new --screenshot`，零依赖（系统 Chrome 即可）。
通用性：任何 HTML/SVG 文件 → PNG，宽/高/缩放/输出路径全部参数化。
公众号也能用（HTML 转图片后可直接贴进文章正文，绕过编辑器 HTML 归一化限制）。

用法:
  python3 html_to_image.py <input.html|svg> --out <out.png> [--width 1080] [--height 8192] [--scale 2] [--virtual-time-budget 5000]

等价的原生 Chrome 命令（--screenshot 方案）:
  "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \\
    --headless=new --disable-gpu --hide-scrollbars --force-device-scale-factor=2 \\
    --window-size=1600,681 --screenshot=out.png file:///path/to/input.svg
"""
import argparse
import os
import shutil
import struct
import subprocess
import sys
from typing import Optional, Tuple

# Python 3.9 兼容：统一用 Optional/默认 None，不用 `X | None` 联合类型语法


def find_chrome() -> str:
    """跨平台探测 Chrome/Chromium（macOS / Linux / Windows 常用路径）。"""
    candidates = [
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "/Applications/Chromium.app/Contents/MacOS/Chromium",
        shutil.which("google-chrome"),
        shutil.which("chromium"),
        shutil.which("chromium-browser"),
        shutil.which("chrome"),
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    ]
    for c in candidates:
        if c and os.path.exists(c):
            return c
    raise FileNotFoundError(
        "未找到 Chrome/Chromium，请安装浏览器，或用 --chrome 显式指定路径"
    )


def _png_size(path: str) -> Optional[Tuple[int, int]]:
    """零依赖读取 PNG 实际像素尺寸（用于 2x 高清校验），非 PNG 返回 None。"""
    try:
        with open(path, "rb") as f:
            head = f.read(24)
        if head[:8] != b"\x89PNG\r\n\x1a\n" or head[12:16] != b"IHDR":
            return None
        width, height = struct.unpack(">II", head[16:24])
        return (width, height)
    except (OSError, struct.error):
        return None


def render(input_path: str, out_path: str, width: int = 1080, height: int = 8192,
           scale: int = 2, chrome: str = None, virtual_time_budget: int = 5000) -> str:
    """无头 Chrome 渲染 HTML/SVG → PNG，返回输出路径。

    - 校验输入存在、输出目录可建
    - 渲染后校验产物存在且尺寸正确（Chrome 可能 exit 0 但静默失败）
    - virtual_time_budget=0 表示禁用（纯静态内容可提速）
    """
    if width <= 0 or height <= 0 or scale <= 0:
        raise ValueError(f"width/height/scale 必须为正数，收到: {width}x{height} @{scale}x")

    chrome = chrome or find_chrome()
    src = os.path.abspath(input_path)
    if not os.path.exists(src):
        raise FileNotFoundError(f"输入文件不存在: {src}")
    out_abs = os.path.abspath(out_path)
    out_dir = os.path.dirname(out_abs)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)

    cmd = [
        chrome,
        "--headless=new",
        "--disable-gpu",
        "--hide-scrollbars",
        f"--force-device-scale-factor={scale}",
        f"--window-size={width},{height}",
    ]
    if virtual_time_budget > 0:
        # 快进虚拟时间，确保字体/异步 JS 渲染完成后再截图（不阻塞真实等待）
        cmd.append(f"--virtual-time-budget={virtual_time_budget}")
    cmd += [f"--screenshot={out_abs}", f"file://{src}"]

    try:
        proc = subprocess.run(cmd, capture_output=True, text=True)
    except OSError as e:
        raise RuntimeError(f"无法启动 Chrome（{e}），可用 --chrome 指定路径") from e

    if proc.returncode != 0:
        detail = (proc.stderr or proc.stdout or "").strip().splitlines()
        tail = detail[-3:] if detail else ["（无输出）"]
        raise RuntimeError(
            f"Chrome 渲染失败 (exit {proc.returncode}):\n" + "\n".join(tail)
        )

    if not os.path.exists(out_abs) or os.path.getsize(out_abs) == 0:
        raise RuntimeError(
            f"Chrome 未产出图片: {out_abs}\n"
            "常见原因：输入文件不是合法 HTML/SVG、资源加载超时（可调大 "
            "--virtual-time-budget）、或 --window-size 超出单图上限（长图建议 ≤ 8192）"
        )

    size = _png_size(out_abs)
    if size is not None and (size[0] != width * scale or size[1] != height * scale):
        raise RuntimeError(
            f"输出尺寸异常: 期望 {width * scale}x{height * scale}px "
            f"（{width}x{height} @{scale}x），实际 {size[0]}x{size[1]}px；"
            "请检查输入内容是否超出画布"
        )
    return out_path


def main():
    ap = argparse.ArgumentParser(
        description="HTML/SVG → PNG（无头 Chrome 截图，平台无关）",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    ap.add_argument("input", help="输入 .html 或 .svg 文件")
    ap.add_argument("--out", required=True, help="输出 PNG 路径")
    ap.add_argument("--width", type=int, default=1080, help="画布宽（CSS 像素）")
    ap.add_argument("--height", type=int, default=8192, help="画布高（CSS 像素，长图上限建议 8192）")
    ap.add_argument("--scale", type=int, default=2, help="设备像素倍率（2 = 高清 2x）")
    ap.add_argument("--virtual-time-budget", type=int, default=5000,
                    help="渲染等待预算 ms（等字体/JS；0 = 禁用，纯静态可提速）")
    ap.add_argument("--chrome", default=None, help="Chrome 可执行文件路径（默认自动探测）")
    args = ap.parse_args()

    if args.width <= 0 or args.height <= 0 or args.scale <= 0:
        ap.error("--width / --height / --scale 必须为正数")
    if args.virtual_time_budget < 0:
        ap.error("--virtual-time-budget 不能为负数（0 = 禁用）")

    try:
        out = render(args.input, args.out, args.width, args.height,
                     args.scale, args.chrome, args.virtual_time_budget)
        size = _png_size(out)
        dim = f"{size[0]}x{size[1]}px" if size else "尺寸未知"
        kb = os.path.getsize(out) // 1024
        print(f"✅ 已输出: {out} ({kb}KB, {dim}, 画布 {args.width}x{args.height} @{args.scale}x)")
    except Exception as e:  # noqa: BLE001 —— CLI 入口统一兜底
        print(f"❌ 失败: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
