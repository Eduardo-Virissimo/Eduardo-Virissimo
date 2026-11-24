"""Gera os SVGs do README no mundo visual do portfólio.

Espiral quadrada de cantos arredondados, molduras de 3px com notch, grade de
pontos e menta só em detalhe. Títulos em Rubik Bold (OFL) já convertidos em
contorno (scripts/glyphs.json, gerado por build_glyphs.py), então não dependem
de fonte instalada em quem abre o README.

    python scripts/gen.py [pasta_de_saida]
"""
import base64, json, math, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "..", "assets")
os.makedirs(OUT, exist_ok=True)

# ---------- tokens (os mesmos do portfólio) ----------
INK, PAPER, MUTE, DIM, LINE, MINT = "#08080a", "#f4f4f1", "#8e8e89", "#3d3d3a", "#26262b", "#c2ebd0"
MONO = "ui-monospace,'JetBrains Mono',SFMono-Regular,Menlo,Consolas,monospace"
EASE = "cubic-bezier(.16,1,.3,1)"

with open(os.path.join(HERE, "glyphs.json"), encoding="utf-8") as f:
    FONT = json.load(f)

STYLE = f"""
  <style>
    .draw  {{ stroke-dasharray:1; animation:draw 2.8s {EASE} .15s backwards; }}
    .cur   {{ animation:blink 1.1s steps(1) infinite; }}
    .type  {{ animation:type 2.4s steps(40) .8s backwards; }}
    @keyframes draw   {{ from{{stroke-dashoffset:1}} }}
    @keyframes blink  {{ 50%{{opacity:0}} }}
    @keyframes type   {{ from{{clip-path:inset(0 100% 0 0)}} }}
    @media (prefers-reduced-motion: reduce) {{ * {{ animation:none !important; }} }}
  </style>"""


# Do README antigo: o traço "fervendo" de nanquim, em todas as bordas, espirais e teclas.
# Sem granulação: todo fundo é o mesmo INK, sem clarear um card mais que outro.
FILTERS = """
    <filter id="tick" filterUnits="userSpaceOnUse" x="-100" y="-100" width="1200" height="1000">
      <feTurbulence type="fractalNoise" baseFrequency="0.035" numOctaves="2" seed="1" result="n">
        <animate attributeName="seed" values="1;7;13;21" dur="0.5s" calcMode="discrete" repeatCount="indefinite"/>
      </feTurbulence>
      <feDisplacementMap in="SourceGraphic" in2="n" scale="4"/>
    </filter>"""

TICKING = 'filter="url(#tick)"'


def svg(w, h, body, defs=""):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" '
            f'font-family="{MONO}">\n  <defs>{FILTERS}{defs}\n  </defs>{STYLE}\n{body}\n</svg>\n')


def save(name, content):
    with open(os.path.join(OUT, name), "w", encoding="utf-8", newline="\n") as f:
        f.write(content)


def f1(v):
    return f"{v:.1f}".rstrip("0").rstrip(".")


# ---------- texto em contorno ----------
def text_width(s, size, tracking=0):
    k = size / FONT["upm"]
    return sum(FONT["glyphs"][c]["adv"] for c in s) * k + tracking * (len(s) - 1)


def text_path(s, x, y, size, fill=PAPER, tracking=0, anchor="start"):
    """Texto em Rubik Bold como <path>; y é a linha de base."""
    k = size / FONT["upm"]
    if anchor == "middle":
        x -= text_width(s, size, tracking) / 2
    parts, cx = [], 0.0
    for c in s:
        g = FONT["glyphs"][c]
        if g["d"]:
            parts.append(f'<path transform="translate({f1(cx / k)} 0)" d="{g["d"]}"/>')
        cx += g["adv"] * k + tracking
    return (f'<g fill="{fill}" transform="translate({f1(x)} {f1(y)}) scale({k:.5f} {-k:.5f})">'
            + "".join(parts) + "</g>")


# ---------- espiral quadrada ----------
def spiral_points(x, y, w, h, gap, lead=0):
    L, T, R, B = x, y, x + w, y + h
    pts = [(L - lead, T)]
    while True:
        if R - L < gap:
            break
        pts.append((R, T))
        if B - T < gap:
            break
        pts += [(R, B), (L, B)]
        if B - (T + gap) < gap:
            break
        pts.append((L, T + gap))
        T, R, B, L = T + gap, R - gap, B - gap, L + gap
    return pts


_mask_ids = iter(range(10_000))


def _spiral_geometry(x, y, w, h, gap, r, lead=0):
    """Linha central da espiral: o `d` do path e amostras (ponto, tangente)."""
    pts = spiral_points(x, y, w, h, gap, lead)
    segs, cur = [], pts[0]
    for (ax, ay), (px, py), (cx, cy) in zip(pts, pts[1:], pts[2:]):
        l1, l2 = math.dist((ax, ay), (px, py)), math.dist((px, py), (cx, cy))
        rr = min(r, l1 / 2, l2 / 2)
        p1 = (px - (px - ax) / l1 * rr, py - (py - ay) / l1 * rr)
        p2 = (px + (cx - px) / l2 * rr, py + (cy - py) / l2 * rr)
        segs += [("L", cur, p1), ("Q", p1, (px, py), p2)]
        cur = p2
    segs.append(("L", cur, pts[-1]))

    d = f"M{f1(pts[0][0])} {f1(pts[0][1])}"
    samples = []
    for kind, *p in segs:
        if kind == "L":
            (ax, ay), (bx, by) = p
            d += f" L{f1(bx)} {f1(by)}"
            ln = math.dist((ax, ay), (bx, by))
            if ln == 0:
                continue
            tx, ty = (bx - ax) / ln, (by - ay) / ln
            n = max(1, int(ln / 4))
            samples += [((ax + (bx - ax) * i / n, ay + (by - ay) * i / n), (tx, ty)) for i in range(n)]
        else:
            (ax, ay), (qx, qy), (bx, by) = p
            d += f" Q{f1(qx)} {f1(qy)} {f1(bx)} {f1(by)}"
            for i in range(8):
                t = i / 8
                px_ = (1 - t) ** 2 * ax + 2 * (1 - t) * t * qx + t * t * bx
                py_ = (1 - t) ** 2 * ay + 2 * (1 - t) * t * qy + t * t * by
                dx = 2 * (1 - t) * (qx - ax) + 2 * t * (bx - qx)
                dy = 2 * (1 - t) * (qy - ay) + 2 * t * (by - qy)
                dl = math.hypot(dx, dy) or 1
                samples.append(((px_, py_), (dx / dl, dy / dl)))
    last = segs[-1]
    samples.append((last[2], samples[-1][1]))
    return d, samples


def spiral(size, x, y, cls="", stroke=PAPER, lead=0):
    """Espiral quadrada nas proporções do logo do portfólio, com traço de pincel.

    Proporções do logo (lado 80): volta a cada 15, traço 7, canto 7. O traço é
    uniforme no corpo e só afina nas pontas: entra levemente e sai numa ponta fina.
    A forma é um contorno preenchido; a animação (desenhar / sumir) roda numa
    máscara com a linha central.
    """
    gap, sw, r = size * 15 / 80, size * 7 / 80, size * 7 / 80
    d, samples = _spiral_geometry(x, y, size, size, gap, r, lead)
    acc, total = [0.0], 0.0
    for (a, _), (b, _) in zip(samples, samples[1:]):
        total += math.dist(a, b)
        acc.append(total)

    l_in, l_out = min(total * .06, sw * 2.5), (total - lead) * .3

    def width(s):
        if s < l_in:                                   # entrada: pincel encostando
            return sw * (.55 + .45 * math.sin(math.pi / 2 * s / l_in))
        if s > total - l_out:                          # saída: afina até a ponta
            u = min(1.0, (s - (total - l_out)) / l_out)
            return max(sw * .04, sw * math.cos(math.pi / 2 * u) ** .8)
        return sw

    left, right = [], []
    for ((px, py), (tx, ty)), s in zip(samples, acc):
        half = width(s) / 2
        nx, ny = -ty, tx
        left.append((px + nx * half, py + ny * half))
        right.append((px - nx * half, py - ny * half))
    ring = left + right[::-1]
    sx, sy = samples[0][0]
    shape = (f'<circle cx="{f1(sx)}" cy="{f1(sy)}" r="{f1(width(0) / 2)}" fill="{stroke}"/>'
             f'<polygon fill="{stroke}" points="{" ".join(f"{f1(a)},{f1(b)}" for a, b in ring)}"/>')
    if not cls:
        return shape
    mid = f"sp{next(_mask_ids)}"
    return (f'<mask id="{mid}" maskUnits="userSpaceOnUse" x="-100" y="-100" width="1200" height="1000">'
            f'<path d="{d}" pathLength="1" class="{cls}" fill="none" stroke="#fff" stroke-width="{sw + 8}" '
            f'stroke-linecap="round" stroke-linejoin="round"/></mask>'
            f'<g mask="url(#{mid})">{shape}</g>')


# ---------- cartão: fundo, grade de pontos, moldura com notch ----------
# Cantos de 16px: mais quadrados que antes, sem perder o arredondado do portfólio.
RX = 16
NOTCH = {"tr": lambda w, h: (w - 40 - 26, -4, 26, 12), "rb": lambda w, h: (w - 8, h - 40 - 26, 12, 26),
         "bl": lambda w, h: (40, h - 8, 26, 12), "lt": lambda w, h: (-4, 40, 12, 26)}


def card(w, h, uid, notch="tr", rx=RX, dots=True):
    defs = (f'\n    <clipPath id="clip-{uid}"><rect x="5" y="5" width="{w - 10}" height="{h - 10}" rx="{rx - 5}"/></clipPath>'
            f'\n    <pattern id="dots-{uid}" width="22" height="22" patternUnits="userSpaceOnUse">'
            f'<circle cx="11" cy="11" r="1.1" fill="{PAPER}" fill-opacity=".09"/></pattern>')
    body = f'  <rect x="5" y="5" width="{w - 10}" height="{h - 10}" rx="{rx - 5}" fill="{INK}"/>\n'
    if dots:
        body += f'  <rect width="{w}" height="{h}" fill="url(#dots-{uid})" clip-path="url(#clip-{uid})"/>\n'
    stroke = f'fill="none" stroke="{PAPER}" stroke-width="3"'
    if notch:
        nx, ny, nw, nh = NOTCH[notch](w, h)
        defs += (f'\n    <mask id="notch-{uid}"><rect x="-10" y="-10" width="{w + 20}" height="{h + 20}" fill="#fff"/>'
                 f'<rect x="{nx}" y="{ny}" width="{nw}" height="{nh}" fill="#000"/></mask>')
        stroke += f' mask="url(#notch-{uid})"'
    body += (f'  <g {TICKING}><rect x="5" y="5" width="{w - 10}" height="{h - 10}" rx="{rx - 5}" '
             f'{stroke}/></g>\n')
    return defs, body


def arrow(x, y, s, sw=2.2, color=PAPER):
    """Seta ↗ desenhada (a mesma dos cards do portfólio), canto superior esquerdo em (x, y)."""
    k = s / 10
    return (f'<path d="M{f1(x)} {f1(y + 10 * k)} L{f1(x + 10 * k)} {f1(y)} M{f1(x + 2 * k)} {f1(y)} '
            f'H{f1(x + 10 * k)} V{f1(y + 8 * k)}" fill="none" stroke="{color}" stroke-width="{sw}" '
            f'stroke-linecap="round" stroke-linejoin="round"/>')


def wrap(text, width):
    lines, cur = [], ""
    for word in text.split():
        if cur and len(cur) + 1 + len(word) > width:
            lines.append(cur)
            cur = word
        else:
            cur = f"{cur} {word}".strip()
    return lines + [cur]


# ---------- header: avatar, nome, apresentação e a espiral ----------
# A apresentação mora aqui dentro (antes era um parágrafo solto embaixo do header).
w, h = 1000, 300
defs, body = card(w, h, "hd", "tr")
body += f'  <g {TICKING}>{spiral(150, w - 64 - 150, (h - 150) // 2, cls="draw")}</g>\n'
tx = 300
body += "  " + text_path("Eduardo", tx - 4, 138, 100, tracking=-1) + "\n"
body += (f'  <text x="{tx}" y="186" fill="{MUTE}" font-size="18">Técnico em Desenvolvimento de Sistemas</text>\n'
         f'  <text x="{tx}" y="212" fill="{MUTE}" font-size="18">SESI SENAI SC · dev. full stack</text>\n'
         f'  <g class="type"><text x="{tx}" y="252" fill="{PAPER}" font-size="18">&gt; trying to be better'
         f'<tspan fill="{MINT}" class="cur"> █</tspan></text></g>\n')
# avatar (assets/avatar.png, fundo recortado), grande e sem moldura, à esquerda,
# desenhado por cima da borda de baixo: o moletom "senta" na borda do header.
with open(os.path.join(HERE, "..", "assets", "avatar.png"), "rb") as f:
    avatar = base64.b64encode(f.read()).decode()
ah = 276
aw = round(ah * 440 / 550)
body += f'  <image href="data:image/png;base64,{avatar}" x="36" y="{h - ah}" width="{aw}" height="{ah}"/>\n'
save("header.svg", svg(w, h, body, defs))

# ---------- links: portfólio, LinkedIn e email numa linha só ----------
# Três imagens de 1/3 da largura, sem espaço entre elas no README: a soma bate com a
# largura dos outros cards. Só o nome e a seta, para continuar legível no celular.
LINKS = [("portfolio", "Portfólio", "tr"), ("linkedin", "LinkedIn", None), ("email", "Email", "bl")]
for slug, name, notch in LINKS:
    w, h = 333, 112
    defs, body = card(w, h, f"l-{slug}", notch, dots=False)
    body += (f'  {text_path(name, 30, 70, 34, tracking=-0.4)}\n'
             f'  <g {TICKING}>{arrow(w - 56, 38, 22, sw=3.2, color=MINT)}</g>')
    save(f"link-{slug}.svg", svg(w, h, body, defs))

# ---------- projetos: nome em cima, descrição e tecnologias embaixo ----------
PROJECTS = [("01", "Vanish", "electron · typescript", "tr",
             "Limpa temporários e caches do Windows, mostrando antes exatamente quais pastas vão sumir."),
            ("02", "Analyst SQL", "next.js · typescript · mysql", "rb",
             "Agente de IA que responde perguntas em português gerando, validando e executando SQL somente leitura."),
            ("03", "PrintScream", "typescript · puppeteer", "bl",
             "Gera PDFs de páginas web a partir de uma URL usando Puppeteer.")]
for num, name, tag, notch, desc in PROJECTS:
    lines = wrap(desc, 70)
    w = 1000
    tag_y = 120 + 30 * len(lines) + 12
    h = tag_y + 40
    defs, body = card(w, h, f"p{num}", notch)
    body += (f'  {text_path(name, 42, 82, 48, tracking=-0.5)}\n'
             f'  <g {TICKING}>{arrow(w - 74, 42, 24, sw=3.2, color=MINT)}</g>\n')
    for i, line in enumerate(lines):
        body += f'  <text x="44" y="{122 + i * 30}" fill="{PAPER}" font-size="21">{line}</text>\n'
    body += (f'  <text x="44" y="{tag_y}" fill="{MUTE}" font-size="18">&gt; {tag}'
             f'<tspan fill="{MINT}" class="cur"> █</tspan></text>')
    save(f"project-{num}.svg", svg(w, h, body, defs))

# ---------- stack: um card só, três colunas de teclas sem borda ----------
# As teclas são preenchidas (sem contorno) para o card não virar um mar de bordas;
# as de estudo avançado ganham o texto e um ponto em menta.
CHIP = "#1d1d21"
GROUPS = [("Front-end", [("HTML5", 0), ("CSS3", 0), ("Tailwind", 0), ("TypeScript", 1), ("JavaScript", 1), ("React", 1)]),
          ("Back-end", [("Node.js", 1), ("PHP", 1), ("MySQL", 0)]),
          ("Ferramentas", [("Git", 0), ("GitHub", 0), ("Linux", 0), ("Shell", 0), ("Docker", 0), ("CI/CD", 0),
                           ("Figma", 0), ("UI/UX", 0)])]
w, col_w, key_h, gap = 1000, 280, 42, 10
cols, bottom = [], 0
for ci, (title, items) in enumerate(GROUPS):
    x0 = 44 + ci * 312
    out = [text_path(title, x0, 106, 30, tracking=-0.3)]
    x, y = x0, 128
    for label, adv in items:
        kw = len(label) * 10 + 32 + (16 if adv else 0)
        if x + kw > x0 + col_w:
            x, y = x0, y + key_h + gap
        out.append(f'<rect x="{x}" y="{y}" width="{kw}" height="{key_h}" rx="8" fill="{CHIP}"/>')
        tx_ = x + 16
        if adv:
            out.append(f'<circle cx="{x + 18}" cy="{y + key_h / 2}" r="4" fill="{MINT}"/>')
            tx_ += 16
        out.append(f'<text x="{tx_}" y="{y + 27}" fill="{MINT if adv else PAPER}" font-size="17">{label}</text>')
        x += kw + 8
    bottom = max(bottom, y + key_h)
    cols.append(out)
h = bottom + 74
defs, body = card(w, h, "st", "tr")
body += f'  <text x="44" y="56" fill="{MUTE}" font-size="16">~/stack</text>\n'
for ci, out in enumerate(cols):
    if ci:
        lx = 44 + ci * 312 - 18
        body += f'  <line x1="{lx}" y1="82" x2="{lx}" y2="{bottom}" stroke="{LINE}" stroke-width="2" stroke-linecap="round"/>\n'
    body += "  " + "\n  ".join(out) + "\n"
body += (f'  <circle cx="50" cy="{h - 40}" r="4" fill="{MINT}"/>\n'
         f'  <text x="64" y="{h - 34}" fill="{MUTE}" font-size="16">estudos avançados</text>')
save("stack.svg", svg(w, h, body, defs))
print("ok")
