# image-pipeline —— Pillow 信息图流水线规范

> 引擎层 · 平台无关。纯 Python（Pillow）程序化生成信息图/卡片/长图，无浏览器依赖。

## 用途

- 数据驱动、批量生成信息图：对比表、榜单、流程图、封面、卡片
- 适合「模板 + 数据 → 出图」的流水线：同一套代码换数据反复出图
- 与 `svg-to-image` 分工：**数据驱动/批量 → Pillow；复杂设计稿/精细排版 → SVG**

## 适用平台

| 场景 | 画布（逻辑） | 输出 |
| --- | --- | --- |
| 小红书长图 | 1080×N | 2x 超采样输出 |
| 公众号正文插图 | 1080 宽 | 2x 超采样输出 |
| 封面（与 svg-to-image 同标准） | 1600×681（2.35:1） | 3200×1362 |
| X 配图 | 1080 宽 | 2x 超采样输出 |

## 流水线要点

### 1. 画布

- 统一 **1080 宽** 为基准逻辑画布（长图高度按内容累加，如 1080×2400）
- 封面沿用 2.35:1 原则：逻辑 1600×681，与 `svg-to-image` 标准一致
- **2x 超采样**：在 2 倍尺寸（2160 宽 / 3200 宽）上绘制，最后 `resize` 降回逻辑尺寸 —— 文字和线条抗锯齿，这是 Pillow 出高清图的关键

```python
from PIL import Image, ImageDraw, ImageFont

SUPER = 2  # 超采样倍率
W, H = 1080 * SUPER, 2400 * SUPER  # 实际绘制画布
img = Image.new("RGB", (W, H), "#FFFFFF")
d = ImageDraw.Draw(img)
# ... 绘制 ...
img = img.resize((W // SUPER, H // SUPER), Image.LANCZOS)  # 降采样抗锯齿
img.save("out.png")
```

### 2. 卡片（圆角 + 层次）

- 卡片：`rounded_rectangle`（圆角半径建议 24px 逻辑尺寸 = 48px 超采样尺寸），浅灰底或白底 + 描边
- 阴影：多层半透明圆角矩形向下偏移叠加模拟（Pillow 无原生阴影）
- 内边距：卡片内容距边缘 ≥ 32px（逻辑）
- 卡片间距 ≥ 24px（逻辑）

```python
# 圆角卡片（超采样坐标下）
d.rounded_rectangle([64, 64, W - 64, 400], radius=48, fill="#F5F8FD", outline="#E5E9F0", width=2)
```

### 3. 字体（中文字体是最大坑）

- **必须显式指定字体文件**：Pillow 默认字体不含中文，缺字会画成方块
- macOS：系统字体目录下的 `PingFang.ttc`（可用 `ImageFont.truetype(path, size)` 加载）
- Linux/CI：思源黑体（Source Han Sans SC）OTF
- 字号层级（逻辑尺寸）：标题 48 / 副题 36 / 正文 28 / 图注 20
- 行高 = 字号 × 1.5 ~ 1.7；**Pillow 没有自动换行**，用 `draw.textlength()` 测量手动断行

```python
font = ImageFont.truetype("/System/Library/Fonts/PingFang.ttc", 56)  # 超采样下 28×2
text = "对比结论：A 侧方案在成本维度占优"
while draw.textlength(text, font=font) > W - 128:  # 手动断行
    text = text[:-1]
```

### 4. 导出

- 一律 PNG（无损）；需 JPEG 时先 `img.convert("RGB")`，否则 RGBA 会出黑底
- 文件名带尺寸信息（如 `info_1080x2400.png`），方便平台侧核对
- 长图高度上限：小红书建议 ≤ 屏幕 3 屏高度（约 2400~3000 逻辑 px），过长加载慢

## 用法示例

```bash
# 无 CLI：Pillow 是库，直接写 Python 脚本调用
python3 scripts/make_infographic.py data.json --out out/info_1080x2400.png
```

```python
# 核心流程骨架（模板 + 数据 → 图）
def render_card(draw, xy, title, body, font_title, font_body):
    x1, y1, x2, y2 = xy
    draw.rounded_rectangle(xy, radius=48, fill="#F5F8FD", outline="#E5E9F0", width=2)
    draw.text((x1 + 64, y1 + 48), title, font=font_title, fill="#111827")
    draw.text((x1 + 64, y1 + 160), body, font=font_body, fill="#2D3748")
```

## 实测记录（2026-08-16）

- ✅ 1080 宽信息图长图全链路通过：2x 超采样 → 降回 1080 → 平台上传无发虚
- ✅ 封面 1600×681 → 3200×1362（Pillow 与 SVG 双链路同一标准）
- 踩坑记录：
  1. **Pillow 无自动换行** → 长中文文本直接溢出画布。修复：`textlength` 手动断行 + 每行末尾检测
  2. **中文字体缺失画方块** → 必须显式 `ImageFont.truetype` 加载系统中文字体，默认字体不可用
  3. **彩色 emoji 渲染不了**（Pillow 只画单色字形）→ 数据里混 emoji 时改用图标占位或转 `svg-to-image` 方案
  4. **直接 1080 宽绘制文字发虚** → 2x 超采样 + LANCZOS 降采样后锐利
  5. **RGBA 直接存 JPEG 出黑底** → 先 `convert("RGB")`

## 相关

- 复杂设计稿封面：`engines/svg-to-image/README.md`
- 渲染实现：本引擎为规范文档；实际脚本按需建在 `engines/image-pipeline/scripts/`
- 排版规范：`design-system/spec.md`
