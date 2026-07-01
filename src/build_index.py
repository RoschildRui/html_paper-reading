"""扫描 reports/ 下所有 HTML 报告，生成仓库根目录的 index.html 首页导航。

用法：
    python src/build_index.py
"""

import html
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REPORTS_DIR = ROOT / "reports"
OUTPUT = ROOT / "index.html"

# 一级目录 -> 展示名
GROUP_NAMES = {
    "deepseek": "DeepSeek",
    "glm": "GLM · 智谱",
    "kimi": "Kimi · 月之暗面",
    "longcat": "LongCat · 美团",
    "minimax": "MiniMax",
    "qwen": "Qwen · 通义千问",
    "seed": "Seed · 字节",
    "stepfun": "StepFun · 阶跃",
    "_misc": "其它",
}

TITLE_RE = re.compile(r"<title[^>]*>(.*?)</title>", re.IGNORECASE | re.DOTALL)


def extract_title(path: Path) -> str:
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        text = ""
    m = TITLE_RE.search(text)
    if m:
        return html.unescape(re.sub(r"\s+", " ", m.group(1)).strip())
    return path.stem


def collect():
    groups = {}
    for f in sorted(REPORTS_DIR.rglob("*.html")):
        rel = f.relative_to(REPORTS_DIR)
        parts = rel.parts
        group = parts[0] if len(parts) >= 3 else "_misc"
        groups.setdefault(group, []).append(
            {"title": extract_title(f), "href": str(f.relative_to(ROOT))}
        )
    return groups


def render(groups) -> str:
    total = sum(len(v) for v in groups.values())
    order = [k for k in GROUP_NAMES if k in groups] + [
        k for k in sorted(groups) if k not in GROUP_NAMES
    ]

    sections = []
    for key in order:
        items = sorted(groups[key], key=lambda x: x["title"].lower())
        name = GROUP_NAMES.get(key, key)
        entries = "\n".join(
            f'          <a class="entry" href="{html.escape(it["href"])}">'
            f'<span class="entry-title">{html.escape(it["title"])}</span>'
            f'<span class="entry-go" aria-hidden="true">&rarr;</span></a>'
            for it in items
        )
        sections.append(
            f'      <section class="group">\n'
            f'        <div class="group-head">\n'
            f'          <h2 class="group-name">{html.escape(name)}</h2>\n'
            f'          <span class="group-rule" aria-hidden="true"></span>\n'
            f'          <span class="group-count">{len(items):02d}</span>\n'
            f'        </div>\n'
            f'        <div class="entries">\n{entries}\n        </div>\n'
            f'      </section>'
        )
    sections_html = "\n".join(sections)

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>论文导读 · Paper Reading</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600&family=Lora:ital,wght@0,400;0,500;1,400&display=swap" rel="stylesheet">
<style>
  :root {{
    --bg: #faf9f5;
    --ink: #141413;
    --muted: #6b6a62;
    --faint: #b0aea5;
    --line: #e4e1d7;
    --hover: #f1eee4;
    --clay: #d97757;
    --clay-deep: #bf5c3c;
    --sans: "Poppins", "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", sans-serif;
    --serif: "Lora", "PingFang SC", "Songti SC", serif;
  }}
  * {{ box-sizing: border-box; }}
  html {{ -webkit-font-smoothing: antialiased; text-rendering: optimizeLegibility; }}
  body {{
    margin: 0; background: var(--bg); color: var(--ink);
    font-family: var(--serif); font-size: 16px; line-height: 1.65;
  }}
  .wrap {{ max-width: 960px; margin: 0 auto; padding: 0 32px; }}

  /* 顶栏 */
  .topbar {{
    display: flex; align-items: center; justify-content: space-between;
    padding: 26px 0; border-bottom: 1px solid var(--line);
  }}
  .brand {{ display: flex; align-items: center; gap: 10px; font-family: var(--sans); font-weight: 500; letter-spacing: .2px; }}
  .brand .dot {{ width: 9px; height: 9px; border-radius: 50%; background: var(--clay); display: inline-block; }}
  .topbar .meta {{ font-family: var(--sans); font-size: 13px; color: var(--faint); }}

  /* 主视觉 */
  .hero {{ padding: 92px 0 80px; max-width: 720px; }}
  .eyebrow {{
    font-family: var(--sans); font-size: 12px; font-weight: 500;
    letter-spacing: .22em; text-transform: uppercase; color: var(--clay);
    margin: 0 0 22px;
  }}
  .hero h1 {{
    font-family: var(--sans); font-weight: 600; color: var(--ink);
    font-size: clamp(34px, 6vw, 56px); line-height: 1.08;
    letter-spacing: -0.01em; margin: 0 0 24px;
  }}
  .hero p {{ font-size: 19px; line-height: 1.7; color: var(--muted); margin: 0; max-width: 40em; }}
  .hero p em {{ color: var(--ink); font-style: italic; }}

  /* 分组 */
  .group {{ padding: 34px 0; border-top: 1px solid var(--line); }}
  .group:first-of-type {{ border-top: none; padding-top: 8px; }}
  .group-head {{ display: flex; align-items: baseline; gap: 18px; margin-bottom: 6px; }}
  .group-name {{ font-family: var(--sans); font-weight: 500; font-size: 20px; margin: 0; letter-spacing: -0.01em; }}
  .group-rule {{ flex: 1; height: 1px; background: var(--line); align-self: center; }}
  .group-count {{ font-family: var(--sans); font-size: 13px; color: var(--faint); font-variant-numeric: tabular-nums; }}

  .entries {{ display: grid; grid-template-columns: 1fr 1fr; column-gap: 40px; }}
  .entry {{
    display: flex; align-items: baseline; justify-content: space-between; gap: 16px;
    padding: 15px 4px; text-decoration: none; color: var(--ink);
    border-bottom: 1px solid var(--line);
    transition: color .18s ease, padding-left .18s ease, background .18s ease;
  }}
  .entry-title {{ font-size: 16px; line-height: 1.45; }}
  .entry-go {{
    font-family: var(--sans); color: var(--clay); flex: none;
    opacity: 0; transform: translateX(-6px);
    transition: opacity .18s ease, transform .18s ease;
  }}
  .entry:hover, .entry:focus-visible {{
    color: var(--clay-deep); background: var(--hover);
    padding-left: 12px; outline: none;
  }}
  .entry:hover .entry-go, .entry:focus-visible .entry-go {{ opacity: 1; transform: translateX(0); }}
  .entry:focus-visible {{ box-shadow: inset 2px 0 0 var(--clay); }}

  footer {{
    border-top: 1px solid var(--line); margin-top: 24px;
    padding: 28px 0 56px; font-family: var(--sans);
    font-size: 12.5px; color: var(--faint); display: flex; justify-content: space-between; gap: 16px; flex-wrap: wrap;
  }}
  footer a {{ color: var(--muted); text-decoration: none; }}
  footer a:hover {{ color: var(--clay-deep); }}

  @media (max-width: 680px) {{
    .wrap {{ padding: 0 22px; }}
    .hero {{ padding: 60px 0 52px; }}
    .entries {{ grid-template-columns: 1fr; column-gap: 0; }}
  }}
  @media (prefers-reduced-motion: reduce) {{
    * {{ transition: none !important; }}
  }}
</style>
</head>
<body>
  <div class="wrap">
    <div class="topbar">
      <span class="brand"><span class="dot"></span>Paper Reading</span>
      <span class="meta">{total} 篇导读</span>
    </div>

    <header class="hero">
      <p class="eyebrow">论文导读 · Visual explainers</p>
      <h1>逐篇读懂前沿模型</h1>
      <p>把 arXiv 上的技术报告与论文，做成<em>图文并茂的中文导读</em>。按团队分组，点开任意一篇即可在线阅读。</p>
    </header>

    <main>
{sections_html}
    </main>

    <footer>
      <span>共 {total} 篇 · 按团队整理</span>
      <span>由 <a href="src/build_index.py">build_index.py</a> 自动生成</span>
    </footer>
  </div>
</body>
</html>
"""


def main():
    groups = collect()
    OUTPUT.write_text(render(groups), encoding="utf-8")
    total = sum(len(v) for v in groups.values())
    print(f"已生成 {OUTPUT.relative_to(ROOT)}，收录 {total} 篇报告，{len(groups)} 个分组。")


if __name__ == "__main__":
    main()
