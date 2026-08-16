# X 适配手册（待优化 🔴）

> 链路：渲染器 → HTML 转长图（1080 宽，最长 8192px）→ 短文案 + 长图推文。
> 成熟度：能发布但格式优化效果最差——全程在跟平台限制搏斗，尚未沉淀成稳定资产。

## 链路总览

```
article.md
  → engines/md-to-html/render_html.py 渲染
  → engines/html-to-image/html_to_image.py 转长图（1080 宽，最长 8192px，完整文章内容）
  → 短文案 + 长图推文（原始 API /2/tweets）
```

## 关键要点

### 1. CJK 加权字符限制 ⚠️ 最大坑

- 中文按 **CJK 加权** 计算：1 个汉字 = 2 权重，280 限制是**加权后**
- 长文直接发 → 超限被拒。两次碰壁后靠「压缩文案 + 长图」绕过
- **结论**：X 不适合发长文文本，长图是正确形态

### 2. 长图方案

- 画布 1080 宽，最长 8192px（平台上限），完整文章内容进长图
- 推文只留短文案（犀利简洁，英文技术圈风格），图片承载正文

### 3. xurl 工具 bug

- `xurl post` 快捷命令有 403 bug → 改用原始 API `/2/tweets` 成功
- 详见 Hermes skill：xurl / xactions-publishing / x-article-publishing

### 4. X Articles 富文本（未成功，待优化）

- 尝试过 Article 长文：标题字段填错（全文写进标题框），Publish 按钮禁用
- **正确流程（TODO）**：标题框只填标题、正文区填正文，验证后再发布
- 目标形态：真 Article 富文本（而非长图），但目前**格式优化效果最差**

### 5. 与公众号的差异（仅输出端）

| 维度 | 公众号 | X |
|---|---|---|
| 输出形态 | HTML 直贴 | 长图 + 短文案 |
| 标题 | 摘要式 | 短文案（英文/犀利简洁） |
| 话题 | — | #AI #DeepSeek #ClaudeCode |
| 发布 | API 草稿 + 网页 | 原始 API /2/tweets（xurl 有 bug） |

## 工具

- `xurl`（OAuth 已绑账号 `<X_HANDLE>`）：post / search / DM；凭证存于本地配置（不入库）
- OpenCLI（已装 + 扩展已加载）：免 API 额度发推
- 详见 Hermes skill：xurl / x-article-publishing / xactions-publishing / api-free-social-publishing

## 待优化（TODO）

- [ ] X Articles 正确发布流程实测沉淀（标题/正文/发布按钮）
- [ ] 短文案模板（英文技术圈风格）沉淀
- [ ] CJK 加权预算工具（发前算好字符权重）
- [ ] 长图推文 vs Article 的形态决策规则

## 踩坑日志

- 2026-08-16：`xurl post` 403 → 原始 API `/2/tweets` 成功
- 2026-08-16：CJK 加权字符超限两次 → 压缩文案 + 长图方案
- 2026-08-16：Article 标题填错（全文进标题框）→ Publish 禁用，停在草稿
