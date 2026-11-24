"""Prepara as imagens embutidas nos SVGs (rodar uma vez; precisa de Pillow).

    pip install pillow
    python scripts/prep_images.py <pasta_com_as_ilustracoes>

A pasta de origem tem as ilustrações do portfólio (cidade.webp, hero-hands.webp,
dragon-scene.webp, kiara-scene-v2.webp, gato.webp, character-talking.webp) e o
avatar.jpg na raiz do repositório. Saída em assets/img/: recortes pequenos, em
escala de cinza, com o preto puro trocado pelo #08080a dos cards.
"""
import os, sys
from PIL import Image, ImageDraw, ImageFilter

SRC = sys.argv[1]
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "assets", "img")
os.makedirs(OUT, exist_ok=True)
INK = 8


def gray(im):
    g = im.convert("L")
    return g.point(lambda v: INK if v < 14 else v)


def crop_to(im, box, size):
    return im.crop(box).resize(size, Image.LANCZOS)


def save_jpg(im, name, q=62):
    im.convert("RGB").save(os.path.join(OUT, name), quality=q, optimize=True, progressive=True)


def matte(im, close=21, shrink=13, side=0.45):
    """Recorta o fundo preto de uma ilustração com contorno branco (flood fill pelas bordas)."""
    g = im.convert("L")
    w, h = g.size
    b = g.point(lambda v: 0 if v < 70 else 255).filter(ImageFilter.MaxFilter(close))
    for x in range(0, w, 6):
        if b.getpixel((x, 0)) == 0:
            ImageDraw.floodfill(b, (x, 0), 128, thresh=0)
    # lado direito inteiro; o esquerdo só em cima, porque o moletom encosta nessa borda
    seeds = [(w - 1, y) for y in range(0, h, 6)] + [(0, y) for y in range(0, int(h * side), 6)]
    for x, y in seeds:
        if b.getpixel((x, y)) == 0:
            ImageDraw.floodfill(b, (x, y), 128, thresh=0)
    bg = b.point(lambda v: 255 if v == 128 else 0).filter(ImageFilter.MaxFilter(shrink))
    alpha = bg.point(lambda v: 0 if v else 255).filter(ImageFilter.GaussianBlur(1.2))
    out = gray(im).convert("RGBA")
    out.putalpha(alpha)
    return out


def src(name):
    return Image.open(os.path.join(SRC, name))


# quadros da faixa de mangá (proporção de cada quadro do SVG, em 1.4x)
PANEL = (336, 294)
panels = {
    "panel-hands.jpg": ("hero-hands.webp", (0, 170, 640, 730)),
    "panel-dragon.jpg": ("dragon-scene.webp", (0, 40, 640, 600)),
    "panel-kiara.jpg": ("kiara-scene-v2.webp", (40, 60, 600, 550)),
    "panel-cat.jpg": ("gato.webp", (2080, 880, 2880, 1580)),
}
for out, (name, box) in panels.items():
    save_jpg(crop_to(gray(src(name)), box, PANEL), out, q=58)

# cidade à noite para o fechamento (faixa larga)
city = gray(src("cidade.webp"))
save_jpg(crop_to(city, (0, 960, 3344, 1882), (1000, 276)), "city.jpg", q=55)

# personagem falando, sem fundo, para ficar na frente da cidade
talk = matte(src("character-talking.webp")).crop((0, 40, 640, 700)).resize((300, 309), Image.LANCZOS)
talk.quantize(colors=40, method=Image.Quantize.FASTOCTREE).save(os.path.join(OUT, "talking.png"), optimize=True)

for f in sorted(os.listdir(OUT)):
    print(f, os.path.getsize(os.path.join(OUT, f)))
