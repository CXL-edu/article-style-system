# motion —— HTML 动画引擎指引

> 引擎层 · 平台无关。HTML/CSS/JS 动画（MG 动画、开场动画、数据动效）的生产指引。
> HTML/CSS/JS 动画实现可由独立项目 `agent-motion-skills` 承载；本仓库同时提供参数化的静态信息图 + 音频竖屏成片入口 `render_asset_slide_video.py`。两者共享 1080×1920 / H.264 输出契约，但不复制用户私有内容。

## 用途

- 用 HTML/CSS/JS 制作动画：MG 动画、开场片头、数据可视化动效、产品演示
- 动画在浏览器里逐帧渲染，输出 mp4 / WebM / GIF 成片
- 与 `html-to-image` 同内核思路：无头 Chrome 渲染，一个浏览器搞定静态图与动态视频

## 适用平台

| 场景 | 画布 | 输出 |
| --- | --- | --- |
| 公众号视频 | 1920×1080（16:9） | mp4（H.264） |
| 小红书视频 | 1080×1440（3:4）或 1080×1920 | mp4 |
| X / 网页 | 16:9 或 1:1 | mp4 / WebM / GIF |
| 正文内嵌动效 | 与正文同宽 | GIF / 短 mp4 |

## 为什么是独立项目（跨 Agent Runtime 复用原则）

`agent-motion-skills` 是**独立维护**的动画技能库，本仓库不复制其实现。原因：

1. **单一事实来源**：动画模板/脚本只在 `agent-motion-skills` 维护，修 bug、加模板只改一处，避免双份维护漂移
2. **跨 Runtime 复用**：任何 Agent Runtime（Hermes、Claude Code、Codex 等）都能按同一接口接入——加载技能 → 取模板 → 生成 HTML 动画 → 无头 Chrome 录帧 → 合成视频。能力属于「引擎」，不属于任何特定 Agent
3. **本仓库的职责**：只写「用哪套接口、产物长什么样」，不写实现细节。在 `engines/` 发现动画问题 → 反馈到 `agent-motion-skills` 修复，**不要在本仓库打补丁**

### 接口约定（占位描述）

| 项 | 约定 |
| --- | --- |
| 安装 | 按 `agent-motion-skills` 的 skill 安装方式接入，工具目录占位 `<TOOL_DIR>` |
| 输入 | 动画脚本/分镜（markdown）+ 模板名 |
| 中间产物 | 独立 HTML 动画文件（自包含 CSS/JS，可本地打开预览） |
| 成片产物 | 帧序列 + mp4（H.264，兼容性最好）/ WebM / GIF |
| 渲染 | 无头 Chrome 录帧，复用 `html-to-image` 同款参数（`--virtual-time-budget` 固定帧） |

## 用法示例

```bash
# 1. 接入动画技能（按 agent-motion-skills 文档，路径用 <TOOL_DIR> 占位）
# 2. 生成动画 HTML（输入脚本，输出自包含 HTML）
# 3. 无头 Chrome 渲染成片
python3 engines/html-to-image/html_to_image.py scene.html \
  --out frame_%d.png --width 1920 --height 1080 --scale 1 --virtual-time-budget 0  # 单帧示意

# 实际成片请走 agent-motion-skills 的录帧 + 合成命令（ffmpeg 合成 mp4）
```

> 注：逐帧录制时 `--virtual-time-budget` 用于固定虚拟时钟，保证每帧渲染状态一致；成片合成由 `agent-motion-skills` 提供。

## 实测记录（2026-08-16）

- ✅ 与 `html-to-image` 引擎同批验证：HTML 动画 → 无头 Chrome 渲染链路可用
- 踩坑记录：
  1. **rAF 动画依赖真实时间戳** → 录帧时帧间状态漂移。修复：固定虚拟时间（`--virtual-time-budget`）驱动动画时钟
  2. **webfont 未预载，首帧字体闪烁/回退** → 动画 HTML 里预加载字体，渲染预算给足
  3. **时长与帧率不对齐掉帧** → 30fps 每帧 33.3ms、60fps 每帧 16.7ms，脚本里按帧率写时间轴
  4. **成片格式** → 平台兼容性 mp4/H.264 最稳；GIF 仅限短动效（≤ 3s）

## 相关

- 动画实现与模板：独立项目 `agent-motion-skills`
- 静态渲染内核：`engines/html-to-image/html_to_image.py`
- 静态封面/信息图：`engines/svg-to-image/README.md`、`engines/image-pipeline/README.md`
