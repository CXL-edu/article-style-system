#!/usr/bin/env python3
"""
render_html.py —— 通用「双色对比」Markdown → HTML 渲染器 v3（泛化版）

基于公众号轻风格 v2（2026-08-16 用户定稿）泛化而来：
- 平台无关：输出标准 HTML，任何发布平台（公众号/小红书长图/X 长图/网页）都能用
- 配置驱动：调色板 + 术语映射通过 --config JSON 传入，支持任意「A 侧 vs B 侧」对比主题
- 默认配置 = 公众号蓝橙（保持 v2 完全兼容）

设计系统核心（用户定稿的「轻风格」哲学）：
- 全文只允许两种语义色（A 侧色 / B 侧色），其余全部素净
- 术语着色、金句强调是仅有的两处上色点；引用框内一律不上色
- 标题渐变 = A 色 → B 色；表格/代码块/图片等中性元素用灰阶

用法:
  python3 render_html.py <input.md> [--out <output.html>] [--config <palette.json>]

  palette.json 示例:
  {
    "name": "deepseek-vs-claude",
    "palette": {
      "A":  "#2F6BB8",   // A 侧术语色（原 DeepSeek 蓝）
      "B":  "#D97706",   // B 侧术语色（原 Claude Code 橙）
      "neutral": "#111827",   // 金句/粗体深色
      "text":   "#2D3748",    // 正文
      "text2":  "#718096",    // 图注/次要
      "border": "#E5E9F0",    // 描边
      "accent": "#6C9EE8",    // 表头/引用边条/标题左条
      "quote_bg": "#F0F5FC",  // 引用底色
      "code_inline_bg": "#F0F5FC"
    },
    "terms": {
      "A": ["DeepSeek Harness", "PTC", "DeepSeek"],
      "B": ["Claude Code", "Dynamic Workflows", "Dynamic Workflow"]
    }
  }

  markdown 标记约定:
  - {{术语}}  → A 侧或 B 侧术语着色（按 terms 映射，未知默认 A）
  - ==金句== → 强调色加粗（默认 neutral 深色；可在配置里加 "emphasis": "#2F6BB8"）
  - **粗体** → neutral 深色加粗（不加彩）
  - `代码`   → 浅色底行内代码
  - [文字](url) → 链接蓝色下划线
"""
import json
import re
import sys

DEFAULT_CONFIG = {
    "name": "wechat-light-v2",
    "palette": {
        "A": "#2F6BB8",
        "B": "#D97706",
        "neutral": "#111827",
        "text": "#2D3748",
        "text2": "#718096",
        "border": "#E5E9F0",
        "accent": "#6C9EE8",
        "quote_bg": "#F0F5FC",
        "quote_text": "#3D5A8C",
        "code_inline_bg": "#F0F5FC",
        "code_inline_text": "#4A7BC4",
        "link": "#3B7DD8",
        "code_bg": "#1E1E1E",
        "code_text": "#D4D4D4",
    },
    "terms": {
        "A": ["DeepSeek Harness", "PTC", "DeepSeek"],
        "B": ["Claude Code", "Dynamic Workflows", "Dynamic Workflow"],
    },
    "emphasis": "#2F6BB8",  # 正文金句色；None 则用 neutral
}


def load_config(path: str) -> dict:
    with open(path, encoding="utf-8") as f:
        cfg = json.load(f)
    # 深合并默认值
    merged = json.loads(json.dumps(DEFAULT_CONFIG))
    merged.update({k: v for k, v in cfg.items() if k != "palette" and k != "terms"})
    merged["palette"].update(cfg.get("palette", {}))
    merged["terms"].update(cfg.get("terms", {}))
    return merged


def _highlight_code(line: str) -> str:
    """Mac 编辑器风格语法高亮（深色主题，单遍正则防嵌套）。"""
    t = line.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    if not t.strip():
        return "&nbsp;"
    token_re = re.compile(
        r"(//[^\n]*|\"[^\"]*\"|'[^']*'|"
        r"\b(?:const|let|var|function|return|await|async|new|if|else|for|of|in|"
        r"map|filter|Promise|import|from|export|class|interface|type|default)\b|"
        r"\b\d+(?:\.\d+)?\b)"
    )

    def repl(m):
        tok = m.group(0)
        if tok.startswith("//"):
            return f'<span style="color:#6A9955;">{tok}</span>'
        if tok.startswith('"') or tok.startswith("'"):
            return f'<span style="color:#CE9178;">{tok}</span>'
        if tok[0].isdigit():
            return f'<span style="color:#B5CEA8;">{tok}</span>'
        return f'<span style="color:#569CD6;">{tok}</span>'

    return token_re.sub(repl, t)


def _make_inline(cfg: dict):
    P = cfg["palette"]
    term_map = {}
    for side in ("A", "B"):
        for term in cfg["terms"].get(side, []):
            term_map[term] = side
    emphasis = cfg.get("emphasis") or P["neutral"]

    def _inline(text: str, in_quote: bool = False) -> str:
        t = text

        def _term(m):
            term = m.group(1)
            if in_quote:
                return term  # 引用框内不上色
            side = term_map.get(term, "A")
            color = P["A"] if side == "A" else P["B"]
            return f'<span style="color:{color};font-weight:600;">{term}</span>'

        t = re.sub(r"\{\{([^}]+)\}\}", _term, t)
        # 金句：正文用 emphasis 色加粗；引用框内降级 neutral（不上色原则）
        color = P["neutral"] if in_quote else emphasis
        t = re.sub(r"==(.+?)==", rf'<strong style="color:{color};">\1</strong>', t)
        # 行内代码
        t = re.sub(r"`([^`]+)`",
                   rf'<code style="background:{P["code_inline_bg"]};color:{P["code_inline_text"]};'
                   rf'padding:1px 6px;border-radius:4px;font-size:0.9em;">\1</code>', t)
        # 超链接
        t = re.sub(r"\[([^\]]+)\]\((https?://[^)\s]+)\)",
                   rf'<a href="\2" style="color:{P["link"]};text-decoration:underline;'
                   rf'word-break:break-all;">\1</a>', t)
        # 粗体（中性色，不加彩）
        t = re.sub(r"\*\*(.+?)\*\*", rf'<strong style="color:{P["neutral"]};">\1</strong>', t)
        # 斜体
        t = re.sub(r"(?<!\*)\*([^*\n]+)\*(?!\*)", r"<em>\1</em>", t)
        return t

    return _inline


def _md_table(lines, _inline, cfg) -> str:
    P = DEFAULT_CONFIG["palette"]  # 表结构中性，用默认灰阶
    rows = []
    for ln in lines:
        ln = ln.strip()
        if not ln.startswith("|"):
            continue
        cells = [c.strip() for c in ln.strip("|").split("|")]
        if all(re.fullmatch(r":?-{2,}:?", c) for c in cells):
            continue
        rows.append(cells)
    if not rows:
        return ""
    ncol = max(len(r) for r in rows)
    rows = [r + [""] * (ncol - len(r)) for r in rows]

    tmin = cfg.get("table_min_width", "")  # 如 "900px" → 移动端容器横向滑动
    tstyle = f'width:{tmin};' if tmin else 'width:100%;'
    html = ['<div style="overflow-x:auto;margin:24px 0;border-radius:12px;border:1px solid #E5E9F0;background:#FFFFFF;">',
            f'<table style="{tstyle}border-collapse:collapse;font-size:15px;line-height:1.6;">']
    for ri, row in enumerate(rows):
        tag = "th" if ri == 0 else "td"
        if ri == 0:
            style = 'background:#6C9EE8;color:#FFFFFF;font-weight:600;padding:12px 14px;text-align:center;'
        else:
            bg = 'background:#F5F8FD;' if ri % 2 == 0 else ''
            style = 'padding:11px 14px;text-align:center;color:#2D3748;' + bg
        cells_html = []
        for c in row:
            cells_html.append("<" + tag + ' style="' + style + '">' + _inline(c) + "</" + tag + ">")
        html.append("<tr>" + "".join(cells_html) + "</tr>")
    html.append("</table></div>")
    return "\n".join(html)


def md_to_html(md_text: str, cfg: dict = None) -> str:
    """完整 Markdown → HTML（双色对比设计系统）。
    自动剥离 YAML frontmatter（title/author/digest 只用于发布配置，不渲染进正文）
    """
    cfg = cfg or DEFAULT_CONFIG
    P = cfg["palette"]
    _inline = _make_inline(cfg)

    fm = re.match(r"^---\n(.*?)\n---\n(.*)$", md_text, re.S)
    md_text = fm.group(2) if fm else md_text
    lines = md_text.split("\n")
    out = []
    i = 0
    n = len(lines)

    def flush_list(li):
        if li:
            out.append(f'<ul style="margin:12px 0 12px 8px;padding-left:20px;color:{P["text"]};line-height:1.75;">'
                       + "".join(f'<li style="margin:8px 0;">{_inline(x)}</li>' for x in li) + "</ul>")

    li = []
    first_h1 = True  # 跳过正文第一个 h1：平台标题栏已展示标题，正文再渲染会重复
    while i < n:
        line = lines[i].rstrip()

        # 表格
        if line.strip().startswith("|"):
            tbl = []
            while i < n and lines[i].strip().startswith("|"):
                tbl.append(lines[i]); i += 1
            out.append(_md_table(tbl, _inline, cfg))
            continue

        # 空行
        if not line.strip():
            flush_list(li); li = []
            i += 1
            continue

        # 标题
        m = re.match(r"^(#{1,4})\s+(.*)", line)
        if m:
            flush_list(li); li = []
            lvl = len(m.group(1))
            if lvl == 1 and first_h1:
                first_h1 = False
                i += 1
                continue
            txt = _inline(m.group(2))
            if lvl == 1:
                out.append(f'<h1 style="font-size:22px;font-weight:700;color:#1F2937;margin:44px 0 18px;'
                           f'padding-bottom:10px;border-bottom:2px solid;'
                           f'border-image:linear-gradient(90deg,{P["A"]},{P["B"]}) 1;">{txt}</h1>')
            elif lvl == 2:
                out.append(f'<h2 style="font-size:19px;font-weight:700;color:#2D3748;margin:36px 0 14px;'
                           f'padding-left:12px;border-left:4px solid {P["accent"]};">{txt}</h2>')
            else:
                out.append(f'<h3 style="font-size:17px;font-weight:700;color:#2D3748;margin:28px 0 10px;">{txt}</h3>')
            i += 1
            continue

        # 引用
        if line.startswith(">"):
            flush_list(li); li = []
            q = []
            while i < n and lines[i].startswith(">"):
                q.append(lines[i].lstrip("> ").strip()); i += 1
            body = "".join(f"<p style='margin:4px 0;'>{_inline(x, in_quote=True)}</p>" for x in q if x)
            out.append(f'<blockquote style="margin:20px 0;padding:14px 18px;background:{P["quote_bg"]};'
                       f'border-left:4px solid {P["accent"]};border-radius:8px;color:{P["quote_text"]};'
                       f'font-size:15px;line-height:1.7;">{body}</blockquote>')
            continue

        # 无序列表
        m = re.match(r"^[-*]\s+(.*)", line)
        if m:
            li.append(m.group(1)); i += 1
            continue
        # 有序列表
        m = re.match(r"^\d+\.\s+(.*)", line)
        if m:
            flush_list(li); li = []
            ordered = []
            while i < n:
                mm = re.match(r"^\d+\.\s+(.*)", lines[i].rstrip())
                if mm:
                    ordered.append(mm.group(1)); i += 1
                else:
                    break
            out.append(f'<ol style="margin:12px 0;padding-left:22px;color:{P["text"]};line-height:1.75;">'
                       + "".join(f"<li style='margin:8px 0;'>{_inline(x)}</li>" for x in ordered) + "</ol>")
            continue

        # 图片
        m = re.match(r"^!\[([^\]]*)\]\(([^)]+)\)\s*$", line)
        if m:
            flush_list(li); li = []
            alt, url = m.group(1), m.group(2)
            cap = (f'<p style="text-align:center;color:{P["text2"]};font-size:12px;margin:10px 0 28px;">'
                   f'{_inline(alt)}</p>') if alt else ""
            out.append(f'<p style="text-align:center;margin:24px 0 0;"><img src="{url}" alt="{alt}" '
                       f'style="max-width:100%;border-radius:12px;border:1px solid {P["border"]};'
                       f'box-shadow:0 2px 12px rgba(44,62,80,0.06);"/></p>{cap}')
            i += 1
            continue

        # 分隔线
        if re.match(r"^[-*_]{3,}$", line.strip()):
            flush_list(li); li = []
            out.append(f'<div style="height:2px;margin:32px 0;'
                       f'background:linear-gradient(90deg,{P["A"]},{P["B"]});'
                       f'border-radius:2px;opacity:0.5;"></div>')
            i += 1
            continue

        # 代码块
        m = re.match(r"^```(\w*)", line.strip())
        if m:
            flush_list(li); li = []
            lang = m.group(1)
            i += 1
            code = []
            while i < n and not lines[i].strip().startswith("```"):
                code.append(lines[i]); i += 1
            i += 1
            lang_name = {"ts": "TypeScript", "js": "JavaScript", "text": "流程图 / 伪代码"}.get(lang, "代码")
            header_line = (
                '<span style="color:#FF5F57;margin-right:8px;">●</span>'
                '<span style="color:#FEBC2E;margin-right:8px;">●</span>'
                '<span style="color:#28C840;margin-right:14px;">●</span>'
                f'<span style="color:#9DA5B4;">{lang_name}</span>'
            )
            code_html = "<br/>".join(
                [header_line, "&nbsp;"] + [_highlight_code(l) if l.strip() else "&nbsp;" for l in code]
            )
            out.append(
                f'<pre style="background:{P["code_bg"]};border-radius:10px;padding:14px 16px;'
                f'margin:20px 0;overflow-x:auto;font-size:13.5px;line-height:1.3;">'
                f'<code style="font-family:Menlo,Consolas,monospace;font-size:13.5px;'
                f'line-height:1.3;color:{P["code_text"]};">{code_html}</code></pre>'
            )
            continue

        # 原生 HTML 块透传（section/table 等微信兼容结构：不包 <p>，避免结构破坏）
        if line.lstrip().startswith("<") and re.match(r"</?[a-zA-Z]", line.lstrip()):
            flush_list(li); li = []
            out.append(line)
            i += 1
            continue

        # 普通段落
        flush_list(li); li = []
        out.append(f'<p style="margin:14px 0;color:{P["text"]};font-size:16px;line-height:1.75;">{_inline(line)}</p>')
        i += 1

    flush_list(li)
    return "\n".join(out)


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 1
    src = sys.argv[1]
    out_path = None
    cfg = DEFAULT_CONFIG
    if "--out" in sys.argv:
        out_path = sys.argv[sys.argv.index("--out") + 1]
    if "--config" in sys.argv:
        cfg = load_config(sys.argv[sys.argv.index("--config") + 1])
    text = open(src, encoding="utf-8").read()
    html = md_to_html(text, cfg)
    if out_path:
        open(out_path, "w", encoding="utf-8").write(html)
        print(f"✅ HTML 已输出: {out_path} ({len(html)} chars) [config={cfg['name']}]")
    else:
        print(html)
    return 0


if __name__ == "__main__":
    sys.exit(main())
