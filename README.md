# Article Style System

> 从内容母稿到公众号、X Article、小红书图文和竖屏短视频的多平台 AI 内容生产与排版工具链。
> 双色对比排版是本项目中的一个设计系统，不是项目的全部范围。

## 项目定位

本仓库保存可复用、可脱敏的内容生产技术层：

- **内容母稿驱动**：一个主题先形成事实与叙事源头，再生成多个平台版本。
- **平台适配**：公众号、X Article、小红书图文和短视频各自处理排版、尺寸、语气和发布门禁。
- **图片与视频共用资产**：先规划内容层视觉资产，再生成平台版式和 1080×1920 视频。
- **安全分层**：通用引擎和参数化脚本进入 GitHub；个人账号、真实内容和发布记录留在私有 vault。

```text
素材与事实
  → 内容母稿
  → 视觉方案与共用资产
  → 公众号 / X Article / 小红书图文 / 竖屏短视频
  → 校验
  → 草稿或经过授权的发布
```

私有运营记忆、实际内容包和平台数据存放在本地 Obsidian vault；本仓库只保存通用规范、渲染器、适配器、模板、Schema 和脱敏示例。

## 为什么从双色对比排版开始

做对比型内容（DeepSeek vs Claude、方案 A vs 方案 B、新旧对比）时，排版最大的坑是**花里胡哨**——多色相同时出现，读者分不清颜色是装饰还是语义。

因此，本项目最初从「双色语义排版」开始，把一套真实公众号实战沉淀为平台无关的 design-system。现在它是多平台内容生产工具链中的一个视觉子系统：可以被公众号、X Article、小红书和视频资产共同复用。

## 三层架构

```
article-style-system/
├── design-system/                 # ★ 规范层（平台无关：定义「长什么样」）
│   ├── spec.md                    #   双色对比排版规范 v2（设计哲学/配色/标记/结构）
│   ├── tokens/wechat-light-v2.json  # 公众号蓝橙 token 实例（默认主题）
│   └── components/                #   组件规范（表格/引用/代码块/图片/封面/信息图）
├── engines/                       # ★ 引擎层（平台无关：定义「怎么生成」）
│   ├── md-to-html/render_html.py  #   MD → inline-style HTML 渲染器 v3（配置驱动）
│   ├── html-to-image/html_to_image.py  # HTML/SVG → PNG（无头 Chrome，零依赖）
│   ├── svg-to-image/              #   SVG 模板规范（2.35:1 原生封面、2x 高清）
│   ├── image-pipeline/            #   Pillow 信息图流水线规范
│   └── motion/                    #   HTML 动画引擎指引（跨 Agent 复用）
├── adapters/                      # ★ 适配层（平台定制化：尽情定制）
│   ├── wechat/README.md           #   公众号：API 草稿 + 网页版发表（权限相关 🟡）
│   ├── xiaohongshu/README.md      #   小红书：长图 + MCP 全自动发布（次之 🟡）
│   └── x/README.md                #   X：Article 富文本 + 普通推文 + 长图兜底（已实测 🟡）
└── docs/                          # ★ 内容生产架构与脱敏 Schema
```

### 各层职责

| 层 | 回答的问题 | 原则 |
|---|---|---|
| design-system/ | 内容长什么样？ | 只写规范与 token，平台无关 |
| engines/ | 内容怎么生成？ | 可执行、可复用，平台无关 |
| adapters/ | 平台怎么发？ | 链路/权限边界/踩坑，平台差异只允许出现在这一层 |

## 快速开始

```bash
# 1. MD → HTML（默认公众号蓝橙主题，零配置）
python3 engines/md-to-html/render_html.py article.md --out article.html

# 2. 自定义对比主题（A/B 两色 + 术语映射）
python3 engines/md-to-html/render_html.py article.md --config my-palette.json --out article.html

# 3. HTML → 长图（小红书 / X 长图兜底：1080 宽，最长 8192px）
python3 engines/html-to-image/html_to_image.py article.html --out article.png --width 1080 --height 8192 --scale 2

# 4. 创建 X Article 草稿（真实 Article，不是长图推文）
python3 adapters/x/scripts/create_article_draft.py \
  --title "文章标题" \
  --cover ./cover.png \
  --body-html ./article.html

# 5. SVG → 高清封面（公众号封面 2.35:1，2x 渲染）
python3 engines/html-to-image/html_to_image.py cover.svg --out cover.png --width 1600 --height 681 --scale 2
```

### 内容生产文档

本仓库只保存脱敏、可复用的技术层，不保存个人账号、真实内容、发布记录或登录态：

- [`docs/content-pipeline.md`](docs/content-pipeline.md) — 内容母稿 → 平台适配 → 图片 → 短视频 → 发布门禁
- [`docs/content-package-schema.md`](docs/content-package-schema.md) — 内容包命名、`content_id`、目录和状态字段
- [`adapters/x/README.md`](adapters/x/README.md) — X Article 富文本草稿适配和验证规则

私有运营记忆、平台实际状态和每个主题的内容包应放在本地 Obsidian vault；GitHub 只实现通用引擎、适配器、模板和测试。

### palette.json 示例

```json
{
  "name": "my-contrast-theme",
  "palette": {
    "A": "#2F6BB8",
    "B": "#D97706",
    "neutral": "#111827"
  },
  "terms": {
    "A": ["产品A", "技术A"],
    "B": ["产品B", "技术B"]
  },
  "emphasis": "#2F6BB8"
}
```

### Markdown 标记

| 标记 | 含义 |
|---|---|
| `{{术语}}` | 术语着色（按映射表，A 色 / B 色） |
| `==金句==` | 金句强调（正文 A 色加粗，引用框内深色） |
| `**粗体**` | 普通强调（深色，不加彩） |
| `` `代码` `` | 行内代码（浅蓝底） |
| 原生 HTML 块（`<section` 等开头行） | **原样透传**，不包 `<p>`（微信端 section/table 结构必需，2026-08-17 实测） |

### 表格能力（2026-08-17 实测沉淀）

| 配置 | 说明 |
|---|---|
| `table_min_width: "900px"`（palette.json） | 表格固定宽度，配合外层 `overflow-x:auto` 容器实现移动端横向滑动 |
| 原生 HTML 表格块 | 直接在 md 里写 `<section>` + `<table>` HTML（需渲染器透传支持），适合微信场景：外层 section 滑动容器 + 内层百分比撑宽 + table 自身 border-radius（separate 模式） |

完整微信表格结构见 `adapters/wechat/` 手册。

### 小红书信息图风格（2026-08-17 沉淀）

- 规范：`design-system/xhs-infographic-style.md`——白底 + 冷暖双色 token、5 级文字层级、卡片/结论条/**箭头标准画法**（垂直箭头翼角水平排列）、布局规则、内容结构模板
- 检查：`engines/svg/svg_check.py <file.svg>...`（画布余量/文本溢出/无卡包含，`--strict`/`--no-title`/`--ignore`）
- 工作流：SVG 写完 → `svg_check.py` 检查 → `html_to_image.py` 渲染 → 发布

## 平台成熟度

| 平台 | 成熟度 | 链路 | 手册 |
|---|---|---|---|
| 公众号 | 🟡 权限相关 | 渲染器 → API 草稿 → 网页版发表（账号权限决定） | `adapters/wechat/` |
| 小红书 | 🟡 次之 | 渲染器 → 长图 → MCP 全自动发布 | `adapters/xiaohongshu/` |
| X Article | 🟡 已实测 | HTML 片段 → Playwright MCP → Article 草稿 → 审核发布 | `adapters/x/` |
| X 普通推文 | 🟢 可用 | 短文案 → API / 浏览器通道 | `adapters/x/` |
| X 长图 | 🟡 兜底 | 渲染器 → 长图 → 推文 | `adapters/x/` |

## 迭代纪律

- **踩坑必沉淀**：实战遇到的问题必须写回三层之一——规范问题进 design-system、能力问题进 engines、平台问题进 adapters/ 对应手册，否则重构无意义
- **平台差异收敛**：引擎与规范保持平台无关，任何平台专属逻辑（权限、字符限制、文案风格）只写在 adapters/
- **凭证永不入库**：AppID、Secret、凭证文件等一律用占位符描述，真实值只存本地
- **手册跟着实战走**：每次发布后更新对应平台手册的「踩坑日志」（日期 + 现象 + 修复）

## 版本历史

- **v2（2026-08-18）**：将仓库总定位扩展为多平台 AI 内容生产与排版工具链；加入内容母稿、内容包 Schema、平台适配文档和发布安全边界；双色对比排版保留为 design-system 子模块。
- **v1（2026-08-17）**：从公众号轻风格 v2 泛化。确立三层架构（design-system / engines / adapters）；渲染器 v3 配置驱动；spec 平台无关化；平台手册全量去隐私化；建立本仓库。
- **v0（2026-08-16）**：公众号轻风格 v2 定稿（蓝橙双色、引用框内不上色、跳首 h1、摘要上引用下）。

## License

MIT
