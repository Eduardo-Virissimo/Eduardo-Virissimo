"""Extrai contornos da Rubik (SIL Open Font License 1.1) para scripts/glyphs.json.

Os títulos dos SVGs viram <path>, então renderizam iguais em qualquer máquina,
sem depender de fonte instalada. Só precisa rodar de novo se mudar o peso ou
precisar de caracteres novos.

    pip install fonttools
    python scripts/build_glyphs.py caminho/para/Rubik[wght].ttf [peso, padrão 500]
"""
import json, os, sys
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont
from fontTools.pens.svgPathPen import SVGPathPen

WEIGHT = int(sys.argv[2]) if len(sys.argv) > 2 else 500
CHARS = ("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"
         " &-.,:!?'/áàâãéêíóôõúçÁÀÂÃÉÊÍÓÔÕÚÇ")

font = instantiateVariableFont(TTFont(sys.argv[1]), {"wght": WEIGHT})
cmap, gs = font.getBestCmap(), font.getGlyphSet()
out = {"upm": font["head"].unitsPerEm, "capHeight": font["OS/2"].sCapHeight,
       "xHeight": font["OS/2"].sxHeight, "glyphs": {}}
for ch in CHARS:
    name = cmap.get(ord(ch))
    if not name:
        continue
    pen = SVGPathPen(gs, lambda v: f"{v:.0f}")
    gs[name].draw(pen)
    out["glyphs"][ch] = {"adv": gs[name].width, "d": pen.getCommands()}

dst = os.path.join(os.path.dirname(os.path.abspath(__file__)), "glyphs.json")
with open(dst, "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, separators=(",", ":"))
print(f"{len(out['glyphs'])} glifos -> {dst}")
