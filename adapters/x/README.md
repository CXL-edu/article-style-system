# X 适配手册

> X 平台需要区分三种输出形态：**X Article 富文本长文**、普通推文/Thread、长图推文兜底。
> 不要把整篇文章渲染成长图后冒充 X Article。

## 当前成熟度

| 形态 | 状态 | 适用场景 |
|---|---|---|
| X Article | 🟡 已实测，可复用 | 技术文章、专题长文、带章节和正文配图的内容 |
| 普通推文 / Thread | 🟢 可用 | 短内容、讨论、引流 |
| 长图推文 | 🟡 兜底 | Article 权限不可用、临时视觉内容或需要完整海报展示 |

X Article 依赖 X 账号当前具备的 Articles 创建/发布权限；平台权限或编辑器 DOM 改版后，需要重新验证。

## X Article 链路

```text
Markdown / 内容资产
  → 生成 HTML 片段（p / h2 / h3 / strong / ul / ol / blockquote / a）
  → 创建新的 X Article 草稿
  → 填写标题
  → 上传封面并 Apply
  → 真实点击 composer + Meta+V 注入富文本
  → 点击正文锚点后插入正文图片
  → 验证 blocks、标题、图片数量和图片位置
  → 保存草稿
  → 人工审核后点击 Publish
```

**默认安全边界：**公开脚本只创建草稿，不自动点击 Publish。正式发布是有外部副作用的动作，应由用户在 X 编辑器审核后执行，或由上层代理在收到明确发布指令后调用专门流程。

## 可复用脚本

```text
adapters/x/scripts/create_article_draft.py
```

它是一个**参数化的公开参考实现**，不包含任何账号、Cookie、个人路径或发布链接。脚本从浏览器 profile 读取登录态，但不会读取或上传凭证。

### 环境要求（macOS）

```bash
# Playwright MCP
npm install -g @playwright/mcp
playwright-mcp install-browser chrome-for-testing

# 富文本剪贴板支持
python3 -m pip install pyobjc-framework-Cocoa
```

首次运行前，需要在持久化的 Playwright 浏览器 profile 中登录 X。不要把 profile 目录提交到仓库。

### 使用方式

先生成一个 HTML 正文片段，再运行：

```bash
python3 adapters/x/scripts/create_article_draft.py \
  --title "文章标题" \
  --cover /absolute/path/cover.png \
  --body-html /absolute/path/body.html \
  --image "第一段后的唯一锚点=/absolute/path/diagram-1.png" \
  --image "第二段后的唯一锚点=/absolute/path/diagram-2.png"
```

可通过环境变量或参数指定浏览器 profile：

```bash
export X_ARTICLE_PROFILE_DIR="$HOME/.x-article-profile"
python3 adapters/x/scripts/create_article_draft.py \
  --profile-dir "$X_ARTICLE_PROFILE_DIR" \
  --title "文章标题" \
  --cover ./cover.png \
  --body-html ./body.html
```

脚本结束时会输出正文 blocks、图片数量和图片 block 位置；如果锚点点击失败，会跳过该图片而不是把图片错误地插到当前光标处。

## 已验证的关键 DOM 锚点

| 元素 | 选择器 / 行为 |
|---|---|
| 标题 | `textarea[name="Article Title"]` |
| 封面按钮 | `button[aria-label="Add photos or video"]` |
| 正文编辑器 | `[data-testid="composer"]` |
| 正文媒体按钮 | `button[aria-label="Add Media"]` |
| 媒体菜单项 | `[role="menuitem"]`，文本为 `Media` |
| 上传区域 | 对话框中包含 `Choose a file` 的区域 |

这些选择器属于 X 当前编辑器实现，不是稳定 API。每次更新 X 后应重新运行最小草稿测试。

## 富文本兼容契约（2026-08 实测）

X Article 支持的稳定表达不是“完整 Markdown/CSS”，而是一组平台可保留的富文本 block：

- 短概念模型 / 箭头链路 → `<blockquote>` + 显式换行；
- 真正的程序步骤 → `<ul>` / `<ol>`；
- 行内技术 token → `<strong>`；
- `h2` 保留；`h3` 在适配层降级为粗体段落；
- 不依赖 `<pre>`、`<code>`、`<hr>`、等宽空格对齐或复杂 CSS。

正文注入必须是真实点击 composer 后 `Meta+V`，不能在 `browser_evaluate` 中调用 `execCommand('paste')`，也不能用整篇 `insertHTML` 代替 Draft.js 输入。

图片必须按唯一正文锚点插入；发布前后都要检查图片数量、图片前后文本、标题层级、引用框和列表结构。最终状态以公开 Article URL 的 DOM 为准，不以脚本退出码、草稿保存或编辑器填充成功作为公开发布证据。

## 关键坑点

### 正文注入

不要在 `browser_evaluate` 中直接执行 `document.execCommand('paste')`：在 Playwright MCP 通道下没有有效的用户手势上下文时会返回失败，正文仍然是空的。

正确顺序是：

```text
browser_click composer
→ browser_press_key Meta+v
→ 检查 blocks > 1
```

### 封面遮挡

上传封面后必须点击 `Apply`，否则封面图可能覆盖正文编辑器，后续点击会落到封面上。

### 图片定位

每次插图前必须清理旧的 `data-anchor` 标记，否则多个目标会导致点击定位不唯一。锚点点击失败时必须跳过该图，不能继续上传。

### HTML 剪贴板

剪贴板需要同时提供 HTML 和去标签的纯文本 fallback。纯文本通道不能直接存 HTML 源码，否则 X 可能只粘贴出残片。

## 与 Hermes 的关系

Hermes 本地 skill 中的脚本是运行适配层；本目录中的脚本是经过脱敏、参数化后的公开参考实现：

| 层 | 位置 | 内容 |
|---|---|---|
| 公开项目 | `adapters/x/` | 平台规范、验证规则、参数化草稿脚本 |
| Hermes 本地 skill | `~/.hermes/skills/social-media/x-article-publishing/` | Hermes 集成、运行环境约定、实测排障记录 |
| 本地浏览器 profile | 用户本机 | X 登录态和 Cookie，**永不入库** |

本项目不包含：账号名、文章链接、Cookie、浏览器 profile、个人绝对路径、个人素材或发布记录。

## 上游参考与许可

本流程参考了 [wshuyi/x-article-publisher-skill](https://github.com/wshuyi/x-article-publisher-skill) 的 Markdown → X Article 思路。上游项目采用 MIT License；本项目保持自己的实现，并在涉及代码复用时保留上游版权和许可证声明。

## 与公众号、小红书的差异

| 维度 | 公众号 | 小红书 | X Article |
|---|---|---|---|
| 正文形态 | HTML / 富文本 | 多张竖版图片 | Article 富文本 |
| 图片 | 正文配图 | 图片本身承载内容 | 封面 + 正文配图 |
| 发布通道 | API 草稿 / 网页 | MCP | Playwright MCP 草稿 + X 编辑器发布 |
| 主要限制 | 未认证账号发布能力 | 图片比例与文字溢出 | 编辑器 DOM、账号 Article 权限 |

## 踩坑日志

- 2026-08-17：完成真实 X Article 端到端测试：60 个正文 blocks、1 张封面、6 张正文图，图片位置逐一验证正确。
- 2026-08-17：确认 `execCommand('paste')` 在 evaluate 中失败；改为真实点击 composer + `Meta+V`。
- 2026-08-17：确认每张图插入前清理 `data-anchor`，否则会触发非唯一定位。
- 2026-08-17：确认正式发布后仍需单独验证文章页面，不以“草稿已保存”代替发布成功。
- 2026-08-16：`xurl post` 曾出现 403；普通推文使用原始 API 或浏览器通道时需单独验证。
