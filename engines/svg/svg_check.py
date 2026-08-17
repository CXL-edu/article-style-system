#!/usr/bin/env python3
"""SVG 信息图质量检查：画布余量 + 文本溢出 + 无卡包含。

用法：
  python3 svg_check.py <file.svg>...          # 检查一个或多个 SVG
  python3 svg_check.py <file.svg> --strict    # 严格模式：画布余量 >60px 即告警

依据 design-system/xhs-infographic-style.md 的布局规则：
- 画布高度 = 内容底 + 40~60px（>80px 报"留白过多"）
- 文本宽度估算：中文 ≈ 字号、ASCII ≈ 0.55×字号
- 文本必须被某个 rect 包含（标题/副标题允许无卡包含，用 --no-title 关闭该告警）

退出码：0 = 干净；1 = 有问题。
"""
import re
import sys


def text_width(text: str, size: float) -> float:
    w = 0.0
    for ch in text:
        if ord(ch) > 0x2E80:          # CJK
            w += size
        elif ch == ' ':
            w += size * 0.4
        else:
            w += size * 0.55
    return w


def check_svg(path: str, strict: bool = False, skip_title: bool = False, ignore: tuple = ()) -> list:
    svg = open(path, encoding='utf-8').read()
    m = re.search(r'<svg[^>]*width="(\d+)"[^>]*height="(\d+)"', svg)
    if not m:
        return [f"{path}: 无法解析画布尺寸"]
    W, H = int(m.group(1)), int(m.group(2))

    rects = [(float(r[0]), float(r[1]), float(r[2]), float(r[3]))
             for r in re.findall(r'<rect x="([\d.]+)" y="([\d.]+)" width="([\d.]+)" height="([\d.]+)"', svg)]

    issues = []
    max_y = 0
    for t in re.finditer(
            r'<text x="([\d.]+)" y="([\d.]+)"(?: text-anchor="(\w+)")?[^>]*?(?:font-size="(\d+)")?[^>]*>(.*?)</text>',
            svg, re.S):
        x, y, anchor, size = float(t.group(1)), float(t.group(2)), t.group(3) or 'start', int(t.group(4) or 21)
        content = re.sub(r'<[^>]+>', '', t.group(5)).strip()
        if not content or any(k in content for k in ignore):
            continue
        w = text_width(content, size)
        x0, x1 = (x - w / 2, x + w / 2) if anchor == 'middle' else ((x - w, x) if anchor == 'end' else (x, x + w))
        max_y = max(max_y, y)
        if x0 < -2 or x1 > W + 2:
            issues.append(f"  画布溢出: '{content[:24]}' x[{x0:.0f},{x1:.0f}] > 画布宽 {W}")
            continue
        if skip_title and y < 150:
            continue  # 标题/副标题允许无卡包含
        contained = any(rx - 2 <= x0 and x1 <= rx + rw + 2 and ry - 3 <= y <= ry + rh + 3
                        for (rx, ry, rw, rh) in rects)
        if not contained:
            issues.append(f"  无卡包含: '{content[:24]}' x[{x0:.0f},{x1:.0f}] y={y:.0f}")

    if rects:
        content_bottom = max(ry + rh for ry, _, _, rh in rects)
        max_y = max(max_y, content_bottom)
    slack = H - max_y
    limit = 60 if strict else 80
    if slack > limit:
        issues.append(f"  画布余量 {slack:.0f}px（内容底 {max_y:.0f}，画布高 {H}）——留白过多，收紧画布")

    return issues


def main():
    args = sys.argv[1:]
    strict = '--strict' in args
    skip_title = '--no-title' in args
    ignore = []
    while '--ignore' in args:
        idx = args.index('--ignore')
        if idx + 1 < len(args):
            ignore.append(args[idx + 1])
            args = args[:idx] + args[idx+2:]
    files = [a for a in args if not a.startswith('--')]
    if not files:
        print(__doc__)
        return 2

    total_issues = 0
    for f in files:
        issues = check_svg(f, strict=strict, skip_title=skip_title, ignore=tuple(ignore))
        if issues:
            total_issues += len(issues)
            print(f"❌ {f}")
            for i in issues:
                print(i)
        else:
            print(f"✅ {f}")
    return 1 if total_issues else 0


if __name__ == '__main__':
    sys.exit(main())
