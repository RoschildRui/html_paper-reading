"""批量把 reports/ 下的 HTML 报告导成单页长图式 PDF（页高=内容实际高度，保留背景）。

用法：
    python src/html_to_pdf.py            # 转换 reports/ 下全部 HTML
    python src/html_to_pdf.py <path...>  # 只转换指定的 HTML 文件
"""

import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(line_buffering=True)

ROOT = Path(__file__).resolve().parent.parent
REPORTS_DIR = ROOT / "reports"

VIEWPORT_WIDTH = 1280          # 桌面渲染宽度
MAX_PDF_HEIGHT_PX = 19000      # Chromium 单页高度上限约 200 英寸(~19200px)，留些余量


def collect_html_files(args):
    if args:
        return [Path(a).resolve() for a in args]
    return sorted(REPORTS_DIR.rglob("*.html"))


def output_pdf_path(html: Path) -> Path:
    # index.html 用其父目录名命名，其余用文件名
    stem = html.parent.name if html.stem == "index" else html.stem
    return html.parent / f"{stem}.pdf"


def convert(page, html: Path) -> Path:
    page.goto(html.as_uri(), wait_until="domcontentloaded", timeout=60000)
    page.emulate_media(media="screen")
    # 等待图片加载完成，但整体最多等 8 秒，避免个别图片永不触发导致死等
    page.evaluate(
        """() => Promise.race([
            Promise.all(
                Array.from(document.images)
                    .filter(img => !img.complete)
                    .map(img => new Promise(res => { img.onload = img.onerror = res; }))
            ),
            new Promise(res => setTimeout(res, 8000))
        ])"""
    )
    page.wait_for_timeout(600)  # 给字体/布局一点时间
    height = page.evaluate(
        "() => Math.ceil(Math.max("
        "document.body.scrollHeight, document.documentElement.scrollHeight,"
        "document.body.offsetHeight, document.documentElement.offsetHeight))"
    )
    clipped = height > MAX_PDF_HEIGHT_PX
    if clipped:
        height = MAX_PDF_HEIGHT_PX

    out = output_pdf_path(html)
    page.pdf(
        path=str(out),
        width=f"{VIEWPORT_WIDTH}px",
        height=f"{height}px",
        print_background=True,
        margin={"top": "0", "right": "0", "bottom": "0", "left": "0"},
    )
    return out, clipped


def main():
    files = collect_html_files(sys.argv[1:])
    if not files:
        print("没有找到 HTML 文件")
        return

    print(f"共 {len(files)} 个文件，开始转换...\n")
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": VIEWPORT_WIDTH, "height": 1080})
        page.set_default_timeout(60000)
        ok = 0
        for i, html in enumerate(files, 1):
            rel = html.relative_to(ROOT) if ROOT in html.parents else html
            try:
                out, clipped = convert(page, html)
                warn = "  [超高已截断]" if clipped else ""
                print(f"[{i}/{len(files)}] {rel} -> {out.relative_to(ROOT)}{warn}")
                ok += 1
            except Exception as e:
                print(f"[{i}/{len(files)}] 失败 {rel}: {e}")
        browser.close()
    print(f"\n完成：{ok}/{len(files)} 个成功。")


if __name__ == "__main__":
    main()
