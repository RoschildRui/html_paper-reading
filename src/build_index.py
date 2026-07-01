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
    # 已知机构在前，其它在最后
    order = [k for k in GROUP_NAMES if k in groups] + [
        k for k in sorted(groups) if k not in GROUP_NAMES
    ]

    sections = []
    for key in order:
        items = sorted(groups[key], key=lambda x: x["title"].lower())
        name = GROUP_NAMES.get(key, key)
        cards = "\n".join(
            f'          <a class="card" href="{html.escape(it["href"])}">'
            f'<span class="card-title">{html.escape(it["title"])}</span></a>'
            for it in items
        )
        sections.append(
            f'      <section class="group">\n'
            f'        <h2>{html.escape(name)} <span class="count">{len(items)}</span></h2>\n'
            f'        <div class="cards">\n{cards}\n        </div>\n'
            f'      </section>'
        )
    sections_html = "\n".join(sections)

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>论文阅读 · HTML 导读合集</title>
<style>
  :root {{
    --bg: #0f1116; --panel: #171a21; --border: #262b36;
    --text: #e6e8ec; --muted: #9aa3b2; --accent: #6ea8fe;
  }}
  * {{ box-sizing: border-box; }}
  body {{
    margin: 0; background: var(--bg); color: var(--text);
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC",
      "Hiragino Sans GB", "Microsoft YaHei", sans-serif; line-height: 1.6;
  }}
  header {{
    padding: 56px 24px 32px; text-align: center;
    border-bottom: 1px solid var(--border);
    background: radial-gradient(1200px 400px at 50% -10%, #1c2230 0%, var(--bg) 70%);
  }}
  header h1 {{ margin: 0 0 8px; font-size: 30px; letter-spacing: .5px; }}
  header p {{ margin: 0; color: var(--muted); font-size: 15px; }}
  main {{ max-width: 1080px; margin: 0 auto; padding: 24px 20px 80px; }}
  .group {{ margin-top: 36px; }}
  .group h2 {{
    font-size: 18px; margin: 0 0 14px; display: flex; align-items: center; gap: 10px;
    color: var(--text);
  }}
  .count {{
    font-size: 12px; color: var(--muted); background: var(--panel);
    border: 1px solid var(--border); border-radius: 999px; padding: 1px 9px; font-weight: 400;
  }}
  .cards {{
    display: grid; gap: 12px;
    grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  }}
  .card {{
    display: block; padding: 14px 16px; text-decoration: none; color: var(--text);
    background: var(--panel); border: 1px solid var(--border); border-radius: 12px;
    transition: border-color .15s, transform .15s, background .15s;
  }}
  .card:hover {{ border-color: var(--accent); transform: translateY(-2px); background: #1b1f28; }}
  .card-title {{ font-size: 14.5px; }}
  footer {{ text-align: center; color: var(--muted); font-size: 13px; padding: 24px; }}
</style>
</head>
<body>
  <header>
    <h1>论文阅读 · HTML 导读合集</h1>
    <p>共 {total} 篇 · 点击卡片查看对应报告</p>
  </header>
  <main>
{sections_html}
  </main>
  <footer>由 <code>src/build_index.py</code> 自动生成</footer>
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
