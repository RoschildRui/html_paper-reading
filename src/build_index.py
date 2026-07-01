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
            f'          <a class="entry" href="{html.escape(it["href"])}" '
            f'data-search="{html.escape(f"{it['title']} {name} {key}".lower(), quote=True)}">'
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

    script_js = """
  <script>
  (function () {
    const input = document.getElementById('q');
    const clearBtn = document.getElementById('clear');
    const countEl = document.getElementById('count');
    const noResults = document.getElementById('no-results');
    const noResultsQ = document.getElementById('no-results-q');
    const groups = Array.from(document.querySelectorAll('.group'));
    const entries = Array.from(document.querySelectorAll('.entry'));
    const total = entries.length;

    entries.forEach(function (a) {
      const t = a.querySelector('.entry-title');
      t.dataset.orig = t.textContent;
    });

    function esc(s) {
      return s.replace(/[&<>]/g, function (c) {
        return { '&': '&amp;', '<': '&lt;', '>': '&gt;' }[c];
      });
    }
    function escRe(s) { return s.replace(/[.*+?^${}()|[\\]\\\\]/g, '\\\\$&'); }

    function highlight(text, tokens) {
      if (!tokens.length) return esc(text);
      const re = new RegExp(tokens.map(escRe).join('|'), 'ig');
      let out = '', last = 0, m;
      while ((m = re.exec(text)) !== null) {
        out += esc(text.slice(last, m.index)) + '<mark>' + esc(m[0]) + '</mark>';
        last = m.index + m[0].length;
        if (m.index === re.lastIndex) re.lastIndex++;
      }
      return out + esc(text.slice(last));
    }

    function apply() {
      const raw = input.value.trim();
      const tokens = raw.toLowerCase().split(/\\s+/).filter(Boolean);
      let visible = 0;
      entries.forEach(function (a) {
        const hit = tokens.every(function (t) { return a.dataset.search.indexOf(t) !== -1; });
        a.style.display = hit ? '' : 'none';
        const t = a.querySelector('.entry-title');
        t.innerHTML = highlight(t.dataset.orig, hit ? tokens : []);
        if (hit) visible++;
      });
      groups.forEach(function (g) {
        const shown = Array.from(g.querySelectorAll('.entry')).filter(function (a) {
          return a.style.display !== 'none';
        }).length;
        g.style.display = shown ? '' : 'none';
        g.querySelector('.group-count').textContent = String(shown).padStart(2, '0');
      });
      countEl.textContent = raw ? (visible + ' / ' + total) : (total + ' 篇');
      clearBtn.style.display = raw ? '' : 'none';
      noResults.classList.toggle('show', visible === 0);
      noResultsQ.textContent = raw ? ('“' + raw + '”') : '';
    }

    input.addEventListener('input', apply);
    clearBtn.addEventListener('click', function () { input.value = ''; apply(); input.focus(); });
    document.addEventListener('keydown', function (e) {
      if (e.key === '/' && document.activeElement !== input) { e.preventDefault(); input.focus(); }
      else if (e.key === 'Escape' && document.activeElement === input) { input.value = ''; apply(); input.blur(); }
    });
  })();
  </script>"""

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
  .hero {{ padding: 92px 0 40px; max-width: 720px; }}
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

  /* 搜索 */
  .search {{ margin: 0 0 30px; }}
  .search-box {{
    display: flex; align-items: center; gap: 12px;
    border: 1px solid var(--line); border-radius: 12px; background: #fff;
    padding: 13px 16px; transition: border-color .18s ease, box-shadow .18s ease;
  }}
  .search-box:focus-within {{ border-color: var(--clay); box-shadow: 0 0 0 3px rgba(217,119,87,.14); }}
  .search-icon {{ flex: none; width: 18px; height: 18px; color: var(--faint); }}
  .search input {{
    flex: 1; min-width: 0; border: none; outline: none; background: transparent;
    font-family: var(--sans); font-size: 15px; color: var(--ink); padding: 0;
  }}
  .search input::placeholder {{ color: var(--faint); }}
  .search input::-webkit-search-decoration,
  .search input::-webkit-search-cancel-button {{ -webkit-appearance: none; }}
  .search-count {{
    font-family: var(--sans); font-size: 12.5px; color: var(--faint);
    white-space: nowrap; font-variant-numeric: tabular-nums;
  }}
  .search-clear {{
    flex: none; border: none; background: transparent; cursor: pointer;
    color: var(--faint); font-size: 20px; line-height: 1; padding: 0 2px; display: none;
  }}
  .search-clear:hover {{ color: var(--clay-deep); }}
  .search-hint {{ font-family: var(--sans); font-size: 12px; color: var(--faint); margin: 11px 2px 0; }}
  .search-hint kbd {{
    font-family: var(--sans); font-size: 11px; color: var(--muted); background: #fff;
    border: 1px solid var(--line); border-bottom-width: 2px; border-radius: 5px; padding: 1px 6px;
  }}
  mark {{ background: rgba(217,119,87,.16); color: var(--clay-deep); border-radius: 3px; padding: 0 1px; }}
  .no-results {{ display: none; padding: 44px 4px; color: var(--muted); font-size: 17px; }}
  .no-results.show {{ display: block; }}
  .no-results b {{ color: var(--ink); font-weight: 500; }}

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

    <div class="search">
      <div class="search-box">
        <svg class="search-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" aria-hidden="true">
          <circle cx="11" cy="11" r="7"></circle><line x1="21" y1="21" x2="16.5" y2="16.5"></line>
        </svg>
        <input id="q" type="search" autocomplete="off" spellcheck="false"
               placeholder="搜索论文，如 R1、attention、prover、agent…" aria-label="按关键词搜索论文">
        <span class="search-count" id="count" aria-live="polite">{total} 篇</span>
        <button class="search-clear" id="clear" type="button" aria-label="清空搜索">&times;</button>
      </div>
      <p class="search-hint">实时筛选 · 空格分隔多个关键词 · 按 <kbd>/</kbd> 聚焦，<kbd>Esc</kbd> 清空</p>
    </div>

    <main>
{sections_html}
      <p class="no-results" id="no-results">没有匹配 <b id="no-results-q"></b> 的论文，换个关键词试试。</p>
    </main>

    <footer>
      <span>共 {total} 篇 · 按团队整理</span>
      <span>由 <a href="src/build_index.py">build_index.py</a> 自动生成</span>
    </footer>
  </div>
{script_js}
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
