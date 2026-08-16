# svg-to-image —— SVG → PNG 封面/信息图引擎规范

> 引擎层 · 平台无关。用 SVG 作为矢量设计稿源，无头 Chrome 渲染输出 2x 高清 PNG。

## 用途

- 把 SVG 设计稿（封面、信息图、卡片）渲染为 PNG 成品
- 封面/信息图统一走「原生 2.35:1 画布 + 2x 高清输出」标准，一套源稿多平台复用
- 与 `html-to-image` 引擎同内核（同一个 `html_to_image.py`），SVG 只是输入格式之一

## 适用平台

| 场景 | 画布 | 输出 |
| --- | --- | --- |
| 公众号封面 | 1600×681（2.35:1） | 3200×1362（2x） |
| 小红书封面/信息图 | 1600×681 或 1080×N 长图 | 2x 高清 |
| X 配图 | 1600×681 / 1080×1350 | 2x 高清 |
| 网页 OG 图 | 1600×681（2.35:1 惯例） | 2x 高清 |

> 平台无关原则：本引擎只负责「SVG → PNG」的通用渲染，具体尺寸由调用方按平台传入。

## 核心原则

### 1. 原生 2.35:1 画布（不要缩放后裁切）

- SVG 直接以 `viewBox="0 0 1600 681"` 设计，逻辑画布就是 2.35:1
- 不要用 3:1 / 16:9 画布再裁成 2.35:1 —— 平台裁切会切掉构图关键元素，且放大后发虚
- 四周保留安全边距（建议 ≥ 64px），防止平台圆角遮罩/裁切压到文字

```xml
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 681" width="1600" height="681">
  <!-- 设计内容，背景铺满 1600×681 -->
</svg>
```

### 2. 2x 高清输出（强制）

- 输出像素 = `画布宽高 × scale`，封面必须 2x：**3200×1362**
- 平台压缩算法对 2x 图友好，1x 图上传后发虚不可逆
- 文字字号以 1600 宽画布为基准设计（标题 ≥ 48px、正文 ≥ 28px），2x 下依然锐利

### 3. 渲染命令

统一走 `html-to-image` 引擎：

```bash
# 推荐：引擎入口（自动探测 Chrome，渲染后自动校验 PNG 尺寸）
python3 engines/html-to-image/html_to_image.py cover.svg \
  --out cover.png --width 1600 --height 681 --scale 2

# 等价的原生 Chrome 命令（--screenshot 方案）
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
  --headless=new --disable-gpu --hide-scrollbars --force-device-scale-factor=2 \
  --window-size=1600,681 --virtual-time-budget=5000 \
  --screenshot=cover.png file:///path/to/cover.svg
```

关键参数：

| 参数 | 值 | 说明 |
| --- | --- | --- |
| `--width` / `--height` | 1600 / 681 | SVG 逻辑画布（CSS 像素） |
| `--scale` | 2 | 设备像素倍率，输出 3200×1362 |
| `--virtual-time-budget` | 5000 | 等 webfont/JS 渲染完成再截图，防止字体缺失 |

### 4. 设计规范要点

- **字体**：优先系统字体栈（`PingFang SC, Helvetica Neue, sans-serif`）；引用的 webfont 必须本地可达，否则截图时字体缺失
- **渐变**：用 SVG 原生 `<linearGradient>`，不要用位图渐变背景
- **文字**：避免超细字重（< 300）和小字号（< 24px），2x 下依然发虚；文字不得溢出 viewBox（静默裁切无报错）
- **导出检查清单**：
  - [ ] viewBox 是 `0 0 1600 681`
  - [ ] 输出 PNG 尺寸 = 3200×1362（引擎自动校验）
  - [ ] 四周安全边距 ≥ 64px
  - [ ] 无文字溢出/被裁切

## 用法示例

```bash
# 封面：2.35:1 原生画布，2x 输出
python3 engines/html-to-image/html_to_image.py covers/launch.svg \
  --out out/launch_cover.png --width 1600 --height 681 --scale 2

# 信息图：1080 宽长图（小红书）
python3 engines/html-to-image/html_to_image.py infographics/flow.svg \
  --out out/flow.png --width 1080 --height 2400 --scale 2
```

## 实测记录（2026-08-16）

- ✅ 公众号封面全链路通过：SVG 1600×681 → PNG 3200×1362，上传平台无压缩发虚
- ✅ 引擎渲染后 PNG 尺寸自动校验（3200×1362）与 2x 要求一致
- 踩坑记录：
  1. **webfont 未加载完就截图** → 文字用回退字体、排版错位。修复：`--virtual-time-budget=5000`
  2. **画布不足 1600 宽**（如 800×340 再放大）→ 输出发虚。修复：一律原生 1600×681 设计
  3. **文字溢出 viewBox 静默裁切** → Chrome 不报错，肉眼难发现。修复：导出前检查文字边界 + 安全边距
  4. **`--force-device-scale-factor` 与 `--window-size` 的乘积即输出像素**，两者都要显式传，别只传一个

## 相关

- 渲染实现：`engines/html-to-image/html_to_image.py`（同一引擎）
- 排版规范：`design-system/spec.md`
- 数据驱动/批量信息图：用 `engines/image-pipeline/README.md`（Pillow 方案）
