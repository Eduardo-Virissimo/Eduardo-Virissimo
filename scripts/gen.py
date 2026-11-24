"""Gera os SVGs do README: limpo, no mundo visual do portfólio.

Preto #08080a, papel #f4f4f1, menta só em detalhe, cantos de 14px com notch e o
traço "tremendo" de nanquim nas bordas. Texto em Geist / Geist Mono (OFL) já
convertido em contorno (scripts/glyphs-*.json, gerados por build_glyphs.py): cada
letra usada vira um <path> nos <defs> e é reaproveitada com <use>.

    python scripts/gen.py [pasta_de_saida]
"""
import json, math, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "..", "assets")
os.makedirs(OUT, exist_ok=True)

# ---------- tokens (os mesmos do portfólio) ----------
INK, PAPER, MUTE, LINE, MINT, CHIP = "#08080a", "#f4f4f1", "#8e8e89", "#26262b", "#c2ebd0", "#19191d"
EASE = "cubic-bezier(.16,1,.3,1)"
RX, STROKE = 14, 2
W = 1000                      # largura dos cards (o README mostra em ~840px: escala ~0.84)

STYLE = f"""
  <style>
    .draw {{ stroke-dasharray:1; animation:draw 2.4s {EASE} .2s backwards; }}
    .cur  {{ animation:blink 1.1s steps(1) infinite; }}
    .type {{ animation:type 2s steps(28) .9s backwards; }}
    @keyframes draw  {{ from{{stroke-dashoffset:1}} }}
    @keyframes blink {{ 50%{{opacity:0}} }}
    @keyframes type  {{ from{{clip-path:inset(0 100% 0 0)}} }}
    @media (prefers-reduced-motion: reduce) {{ * {{ animation:none !important; }} }}
  </style>"""

# o "tique" de nanquim da primeira versão do README, só nas bordas e no logo
TICK = """
    <filter id="tick" filterUnits="userSpaceOnUse" x="-50" y="-50" width="1100" height="600">
      <feTurbulence type="fractalNoise" baseFrequency="0.035" numOctaves="2" seed="1" result="n">
        <animate attributeName="seed" values="1;7;13;21" dur="0.5s" calcMode="discrete" repeatCount="indefinite"/>
      </feTurbulence>
      <feDisplacementMap in="SourceGraphic" in2="n" scale="3"/>
    </filter>"""
TICKING = 'filter="url(#tick)"'


def f1(v):
    return f"{v:.1f}".rstrip("0").rstrip(".")


# ---------- texto em contorno ----------
class Font:
    def __init__(self, name):
        with open(os.path.join(HERE, f"glyphs-{name}.json"), encoding="utf-8") as f:
            data = json.load(f)
        self.name, self.upm, self.glyphs = name, data["upm"], data["glyphs"]

    def width(self, s, size, tracking=0):
        return sum(self.glyphs[c]["adv"] for c in s) * size / self.upm + tracking * (len(s) - 1)

    def text(self, s, x, y, size, fill=PAPER, tracking=0, anchor="start"):
        """Texto como <use> dos glifos; y é a linha de base."""
        k = size / self.upm
        if anchor == "end":
            x -= self.width(s, size, tracking)
        uses, cx = [], 0.0
        for c in s:
            g = self.glyphs[c]
            if g["d"]:
                gid = f"{self.name[0]}{ord(c):x}"
                USED[gid] = g["d"]
                uses.append(f'<use href="#{gid}" x="{f1(cx)}"/>')
            cx += g["adv"] + tracking / k
        return f'<g fill="{fill}" transform="translate({f1(x)} {f1(y)}) scale({k:.5f} {-k:.5f})">{"".join(uses)}</g>'


SANS, MONO = Font("sans"), Font("mono")
USED = {}


def svg(w, h, body, defs="", tick=True):
    glyphs = "".join(f'<path id="{gid}" d="{d}"/>' for gid, d in USED.items())
    USED.clear()
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">\n'
            f'  <defs>{TICK if tick else ""}{defs}\n    {glyphs}\n  </defs>{STYLE}\n{body}\n</svg>\n')


def save(name, content):
    with open(os.path.join(OUT, name), "w", encoding="utf-8", newline="\n") as f:
        f.write(content)


# ---------- peças ----------
NOTCH = {"tr": lambda w, h: (w - 36 - 22, -4, 22, 10), "rb": lambda w, h: (w - 7, h - 36 - 22, 10, 22),
         "bl": lambda w, h: (36, h - 7, 22, 10)}


def card(w, h, uid, inner, notch="tr"):
    """Fundo, conteúdo e a moldura tremendo (com o notch do portfólio) por cima."""
    defs, stroke = "", f'fill="none" stroke="{PAPER}" stroke-width="{STROKE}"'
    if notch:
        nx, ny, nw, nh = NOTCH[notch](w, h)
        defs = (f'\n    <mask id="n-{uid}"><rect x="-10" y="-10" width="{w + 20}" height="{h + 20}" fill="#fff"/>'
                f'<rect x="{nx}" y="{ny}" width="{nw}" height="{nh}" fill="#000"/></mask>')
        stroke += f' mask="url(#n-{uid})"'
    body = (f'  <rect x="5" y="5" width="{w - 10}" height="{h - 10}" rx="{RX - 5}" fill="{INK}"/>\n'
            f'{inner}'
            f'  <g {TICKING}><rect x="5" y="5" width="{w - 10}" height="{h - 10}" rx="{RX - 5}" {stroke}/></g>')
    return defs, body


def arrow(x, y, s, color=MINT, sw=2.2):
    """Seta ↗ (a mesma dos cards do portfólio), canto superior esquerdo em (x, y)."""
    k = s / 10
    return (f'<path d="M{f1(x)} {f1(y + 10 * k)} L{f1(x + 10 * k)} {f1(y)} M{f1(x + 2 * k)} {f1(y)} '
            f'H{f1(x + 10 * k)} V{f1(y + 8 * k)}" fill="none" stroke="{color}" stroke-width="{sw}" '
            f'stroke-linecap="round" stroke-linejoin="round"/>')


def cursor(x, y, size):
    return f'<rect class="cur" x="{f1(x)}" y="{f1(y - size * .78)}" width="{f1(size * .55)}" height="{f1(size * .95)}" fill="{MINT}"/>'


def logo(x, y, size, sw=2.6, cls=""):
    """Logo do portfólio (espiral quadrada), escalado para `size` px."""
    k = size / 100
    d = ('M10 10 L83 10 Q90 10 90 17 L90 83 Q90 90 83 90 L17 90 Q10 90 10 83 L10 32 Q10 25 17 25 '
         'L68 25 Q75 25 75 32 L75 68 Q75 75 68 75 L32 75 Q25 75 25 68 L25 47 Q25 40 32 40 L53 40 '
         'Q60 40 60 47 L60 53 Q60 60 53 60 L40 60')
    c = f' class="{cls}"' if cls else ""
    return (f'<g transform="translate({f1(x)} {f1(y)}) scale({k:.4f})"><path d="{d}" pathLength="1"{c} fill="none" '
            f'stroke="{PAPER}" stroke-width="{f1(sw / k)}" stroke-linecap="round" stroke-linejoin="round"/></g>')


def wrap(text, width):
    lines, cur = [], ""
    for word in text.split():
        if cur and len(cur) + 1 + len(word) > width:
            lines.append(cur)
            cur = word
        else:
            cur = f"{cur} {word}".strip()
    lines.append(cur)
    if len(lines) > 1:                       # linhas equilibradas, sem palavra sobrando
        return wrap_once(text, math.ceil(len(text) / len(lines)) + 6)
    return lines


def wrap_once(text, width):
    lines, cur = [], ""
    for word in text.split():
        if cur and len(cur) + 1 + len(word) > width:
            lines.append(cur)
            cur = word
        else:
            cur = f"{cur} {word}".strip()
    return lines + [cur]


# ---------- header ----------
h = 168
typed = "> trying to be better"
inner = (f'  <g {TICKING}>{logo(36, 34, 52, cls="draw")}</g>\n'
         f'  {SANS.text("Eduardo", 104, 77, 46, tracking=-1)}\n'
         f'  {MONO.text("dev. full stack · Técnico em Desenvolvimento de Sistemas · SESI SENAI SC", 40, 118, 15, MUTE)}\n'
         f'  <g class="type">{MONO.text(typed, 40, 145, 15)}</g>\n'
         f'  {cursor(40 + MONO.width(typed + " ", 15), 145, 15)}\n')
defs, body = card(W, h, "hd", inner)
save("header.svg", svg(W, h, body, defs))

# ---------- links ----------
for slug, name, notch in [("portfolio", "Portfólio", "tr"), ("linkedin", "LinkedIn", None), ("email", "Email", "bl")]:
    w, h = 333, 64
    inner = (f'  {SANS.text(name, 24, 39, 18, tracking=-0.2)}\n'
             f'  <g {TICKING}>{arrow(w - 42, 26, 12)}</g>\n')
    defs, body = card(w, h, f"l{slug}", inner, notch)
    save(f"link-{slug}.svg", svg(w, h, body, defs))

# ---------- projetos ----------
PROJECTS = [("01", "Vanish", "electron · typescript", "tr",
             "Limpa temporários e caches do Windows, mostrando antes exatamente quais pastas vão sumir."),
            ("02", "Analyst SQL", "next.js · typescript · mysql", "rb",
             "Agente de IA que responde perguntas em português gerando, validando e executando SQL somente leitura."),
            ("03", "PrintScream", "typescript · puppeteer", "bl",
             "Gera PDFs de páginas web a partir de uma URL usando Puppeteer.")]
for num, name, tag, notch, desc in PROJECTS:
    lines = wrap(desc, 96)
    tag_y = 88 + 23 * len(lines) + 6
    h = tag_y + 30
    inner = (f'  {SANS.text(name, 38, 54, 24, tracking=-0.4)}\n'
             f'  <g {TICKING}>{arrow(W - 52, 32, 13)}</g>\n')
    for i, line in enumerate(lines):
        inner += f'  {MONO.text(line, 40, 88 + i * 23, 15.5)}\n'
    inner += f'  {MONO.text("> " + tag, 40, tag_y, 13.5, MUTE)}\n'
    defs, body = card(W, h, f"p{num}", inner, notch)
    save(f"project-{num}.svg", svg(W, h, body, defs))

# ---------- stack ----------
GROUPS = [("Front-end", [("HTML5", 0), ("CSS3", 0), ("Tailwind", 0), ("TypeScript", 1), ("JavaScript", 1), ("React", 1)]),
          ("Back-end", [("Node.js", 1), ("PHP", 1), ("MySQL", 0)]),
          ("Ferramentas", [("Git", 0), ("GitHub", 0), ("Linux", 0), ("Shell", 0), ("Docker", 0), ("CI/CD", 0),
                           ("Figma", 0), ("UI/UX", 0)])]
col_w, key_h, size = 286, 31, 13.5
cols, bottom = [], 0
for ci, (title, items) in enumerate(GROUPS):
    x0 = 40 + ci * 312
    out = [SANS.text(title, x0, 84, 17, tracking=-0.2)]
    x, y = x0, 102
    for label, adv in items:
        kw = round(MONO.width(label, size) + 24 + (12 if adv else 0))
        if x + kw > x0 + col_w:
            x, y = x0, y + key_h + 7
        out.append(f'<rect x="{x}" y="{y}" width="{kw}" height="{key_h}" rx="6" fill="{CHIP}"/>')
        tx = x + 12
        if adv:
            out.append(f'<circle cx="{x + 14}" cy="{y + key_h / 2}" r="3" fill="{MINT}"/>')
            tx += 12
        out.append(MONO.text(label, tx, y + 19.5, size, MINT if adv else PAPER))
        x += kw + 6
    bottom = max(bottom, y + key_h)
    cols.append(out)
h = bottom + 56
inner = f'  {MONO.text("~/stack", 40, 46, 12.5, MUTE)}\n'
for ci, out in enumerate(cols):
    if ci:
        lx = 40 + ci * 312 - 16
        inner += f'  <line x1="{lx}" y1="66" x2="{lx}" y2="{bottom}" stroke="{LINE}" stroke-width="1.5" stroke-linecap="round"/>\n'
    inner += "  " + "\n  ".join(out) + "\n"
inner += (f'  <circle cx="44" cy="{h - 30}" r="3" fill="{MINT}"/>\n'
          f'  {MONO.text("estudos avançados", 54, h - 26, 12, MUTE)}\n')
defs, body = card(W, h, "st", inner)
save("stack.svg", svg(W, h, body, defs))
print("ok")
