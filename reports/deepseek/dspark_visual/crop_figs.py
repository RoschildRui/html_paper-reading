import fitz, io
from PIL import Image

doc = fitz.open('DSpark_paper.pdf')
Z = 6.0

# pidx -> list of (name, caption_y0). Figures are ABOVE their caption.
caps = {
    4:  [('fig1_arch', 361.0)],
    11: [('fig2_position', 213.0)],
    12: [('fig3_depth', 260.6), ('fig4_proposal', 436.6)],
    14: [('fig5_threshold', 241.9), ('fig6_calib', 447.0)],
    17: [('fig7_pareto', 267.3)],
    18: [('fig8_load', 491.6)],
}

XPAD = 4
for pidx, figs in caps.items():
    pg = doc[pidx]
    draws = [dr['rect'] for dr in pg.get_drawings()]
    pix = pg.get_pixmap(matrix=fitz.Matrix(Z, Z))
    img = Image.open(io.BytesIO(pix.tobytes('png')))
    prev_bottom = 0
    for name, cap_y in figs:
        # graphics belonging to this figure: above caption, below previous caption
        band = [r for r in draws if r.y1 < cap_y - 1 and r.y0 > prev_bottom + 1]
        if not band:
            prev_bottom = cap_y + 15
            continue
        top = min(r.y0 for r in band)
        bottom = max(r.y1 for r in band)
        bottom = min(bottom, cap_y - 2)
        left = max(0, min(r.x0 for r in band) - XPAD)
        right = max(r.x1 for r in band) + XPAD
        box = (left*Z, (top-3)*Z, right*Z, (bottom+3)*Z)
        crop = img.crop(box)
        crop.save(f'dspark_visual/assets/{name}.png')
        print(f'{name}: pts y[{top:.0f},{bottom:.0f}] x[{left:.0f},{right:.0f}] -> {crop.size}')
        prev_bottom = cap_y + 15
