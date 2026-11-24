"""Extrai contornos de uma fonte variável (OFL) para scripts/glyphs-<nome>.json.

Todo o texto dos SVGs vira <path>/<use>, então renderiza igual em qualquer máquina,
sem depender de fonte instalada em quem abre o README.

    pip install fonttools
    python scripts/build_glyphs.py Geist[wght].ttf 500 sans
    python scripts/build_glyphs.py GeistMono[wght].ttf 400 mono
"""
import json, os, sys
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont
from fontTools.pens.svgPathPen import SVGPathPen

path, weight, name = sys.argv[1], int(sys.argv[2]), sys.argv[3]
CHARS = "".join(chr(c) for c in range(32, 127)) + "·áàâãéêíóôõúçÁÀÂÃÉÊÍÓÔÕÚÇ"

font = instantiateVariableFont(TTFont(path), {"wght": weight})
cmap, gs = font.getBestCmap(), font.getGlyphSet()
out = {"upm": font["head"].unitsPerEm, "glyphs": {}}
for ch in CHARS:
    g = cmap.get(ord(ch))
    if not g:
        continue
    pen = SVGPathPen(gs, lambda v: f"{v:.0f}")
    gs[g].draw(pen)
    out["glyphs"][ch] = {"adv": gs[g].width, "d": pen.getCommands()}

dst = os.path.join(os.path.dirname(os.path.abspath(__file__)), f"glyphs-{name}.json")
with open(dst, "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, separators=(",", ":"))
print(f"{len(out['glyphs'])} glifos -> {dst}")
