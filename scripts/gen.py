"""Gera os SVGs do README no mundo visual do portfólio.

Espiral quadrada de cantos arredondados, molduras de 3px com notch, grade de
pontos e menta só em detalhe. Títulos em Rubik Medium (OFL) já convertidos em
contorno (scripts/glyphs.json, gerado por build_glyphs.py), então não dependem
de fonte instalada em quem abre o README.

    python scripts/gen.py [pasta_de_saida]
"""
import base64, json, math, os, random, sys

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
    .tw    {{ animation:tw 3.4s ease-in-out infinite; }}
    .drift {{ transform-box:fill-box; transform-origin:center; animation:drift 16s ease-in-out infinite alternate; }}
    .fade  {{ animation:fade .7s {EASE} backwards; }}
    @keyframes tw     {{ 50%{{opacity:.12}} }}
    @keyframes drift  {{ to{{transform:scale(1.09) translate(-1.5%,-1%)}} }}
    @keyframes fade   {{ from{{opacity:0}} }}
    @media (prefers-reduced-motion: reduce) {{ * {{ animation:none !important; }} }}
  </style>"""


# Do README antigo: o traço "fervendo" de nanquim, em todas as bordas, espirais e teclas.
# Sem granulação: todo fundo é o mesmo INK, sem clarear um card mais que outro.
FILTERS = """
    <filter id="tick" filterUnits="userSpaceOnUse" x="-100" y="-100" width="1200" height="1000">
      <feTurbulence type="fractalNoise" baseFrequency="0.035" numOctaves="2" seed="1" result="n">
        <animate attributeName="seed" values="1;7;13;21" dur="0.5s" calcMode="discrete" repeatCount="indefinite"/>
      </feTurbulence>
      <feDisplacementMap in="SourceGraphic" in2="n" scale="3"/>
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


def spiral(size, x, y, cls="", stroke=PAPER, lead=0, weight=7):
    """Espiral quadrada nas proporções do logo do portfólio, com traço de pincel.

    Proporções do logo (lado 80): volta a cada 15, traço 7, canto 7. O traço é
    uniforme no corpo e só afina nas pontas: entra levemente e sai numa ponta fina.
    A forma é um contorno preenchido; a animação (desenhar / sumir) roda numa
    máscara com a linha central.
    """
    gap, sw, r = size * 15 / 80, size * weight / 80, size * 7 / 80
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
# O README mora numa coluna de ~840px no perfil: tudo aqui é desenhado pensando nessa
# escala (~0.84). Traço de 2px e cantos de 14px, para não pesar.
RX, STROKE = 14, 2
NOTCH = {"tr": lambda w, h: (w - 36 - 22, -4, 22, 10), "rb": lambda w, h: (w - 7, h - 36 - 22, 10, 22),
         "bl": lambda w, h: (36, h - 7, 22, 10), "lt": lambda w, h: (-4, 36, 10, 22)}
IMG = os.path.join(HERE, "..", "assets", "img")


def card(w, h, uid, notch="tr", rx=RX, dots=True):
    defs = (f'\n    <clipPath id="clip-{uid}"><rect x="5" y="5" width="{w - 10}" height="{h - 10}" rx="{rx - 5}"/></clipPath>'
            f'\n    <pattern id="dots-{uid}" width="22" height="22" patternUnits="userSpaceOnUse">'
            f'<circle cx="11" cy="11" r="1" fill="{PAPER}" fill-opacity=".08"/></pattern>')
    body = f'  <rect x="5" y="5" width="{w - 10}" height="{h - 10}" rx="{rx - 5}" fill="{INK}"/>\n'
    if dots:
        body += f'  <rect width="{w}" height="{h}" fill="url(#dots-{uid})" clip-path="url(#clip-{uid})"/>\n'
    return defs, body


def frame(w, h, uid, notch="tr", rx=RX):
    """Moldura tremendo; vai por último para ficar por cima de imagens."""
    defs, stroke = "", f'fill="none" stroke="{PAPER}" stroke-width="{STROKE}"'
    if notch:
        nx, ny, nw, nh = NOTCH[notch](w, h)
        defs = (f'\n    <mask id="notch-{uid}"><rect x="-10" y="-10" width="{w + 20}" height="{h + 20}" fill="#fff"/>'
                f'<rect x="{nx}" y="{ny}" width="{nw}" height="{nh}" fill="#000"/></mask>')
        stroke += f' mask="url(#notch-{uid})"'
    return defs, f'  <g {TICKING}><rect x="5" y="5" width="{w - 10}" height="{h - 10}" rx="{rx - 5}" {stroke}/></g>\n'


def framed(w, h, uid, inner, notch="tr", dots=True):
    d1, b1 = card(w, h, uid, notch, dots=dots)
    d2, b2 = frame(w, h, uid, notch)
    return d1 + d2, b1 + inner + b2


def embed(name):
    with open(os.path.join(IMG, name), "rb") as f:
        data = base64.b64encode(f.read()).decode()
    kind = "png" if name.endswith(".png") else "jpeg"
    return f"data:image/{kind};base64,{data}"


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


def stars(n, x0, y0, x1, y1, seed, mint=1):
    """Céu da noite: estrelas piscando fora de fase (visíveis mesmo sem animação)."""
    rnd = random.Random(seed)
    out = []
    for i in range(n):
        x, y = rnd.uniform(x0, x1), rnd.uniform(y0, y1)
        r = rnd.choice((0.8, 1, 1.2, 1.6))
        color = MINT if i < mint else PAPER
        out.append(f'<circle cx="{f1(x)}" cy="{f1(y)}" r="{r}" fill="{color}" fill-opacity="{rnd.choice((.45, .6, .8))}" '
                   f'class="tw" style="animation-delay:-{f1(rnd.uniform(0, 3.4))}s"/>')
    return "".join(out)


# ---------- header: céu, avatar, nome, apresentação e a espiral ----------
w, h = 1000, 230
# estrelas só onde não há texto: à direita do bloco de texto e numa faixa acima do nome
inner = f'  {stars(22, 600, 16, 990, 214, seed=3)}{stars(8, 240, 14, 600, 40, seed=5, mint=0)}\n'
inner += f'  <g {TICKING}>{spiral(112, w - 62 - 112, (h - 112) // 2, cls="draw", weight=5.5)}</g>\n'
tx = 252
inner += "  " + text_path("Eduardo", tx - 3, 104, 64, tracking=-0.8) + "\n"
inner += (f'  <text x="{tx}" y="142" fill="{MUTE}" font-size="16">Técnico em Desenvolvimento de Sistemas</text>\n'
          f'  <text x="{tx}" y="166" fill="{MUTE}" font-size="16">SESI SENAI SC · dev. full stack</text>\n'
          f'  <g class="type"><text x="{tx}" y="200" fill="{PAPER}" font-size="16">&gt; trying to be better'
          f'<tspan fill="{MINT}" class="cur"> █</tspan></text></g>\n')
defs, body = framed(w, h, "hd", inner)
# avatar por cima da borda de baixo (o moletom "senta" na borda)
with open(os.path.join(HERE, "..", "assets", "avatar.png"), "rb") as f:
    avatar = base64.b64encode(f.read()).decode()
ah = 214
aw = round(ah * 440 / 550)
body += f'  <image href="data:image/png;base64,{avatar}" x="40" y="{h - ah}" width="{aw}" height="{ah}"/>\n'
save("header.svg", svg(w, h, body, defs))

# ---------- links: portfólio, LinkedIn e email numa linha só ----------
LINKS = [("portfolio", "Portfólio", "tr"), ("linkedin", "LinkedIn", None), ("email", "Email", "bl")]
for slug, name, notch in LINKS:
    w, h = 333, 72
    inner = (f'  {text_path(name, 26, 44, 20, tracking=-0.2)}\n'
             f'  <g {TICKING}>{arrow(w - 44, 28, 14, sw=2.4, color=MINT)}</g>\n')
    defs, body = framed(w, h, f"l-{slug}", inner, notch, dots=False)
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
    if len(lines) > 1:                     # linhas equilibradas, sem palavra sobrando sozinha
        lines = wrap(desc, math.ceil(len(desc) / len(lines)) + 6)
    w = 1000
    tag_y = 92 + 24 * len(lines) + 8
    h = tag_y + 30
    inner = (f'  {text_path(name, 38, 58, 28, tracking=-0.3)}\n'
             f'  <g {TICKING}>{arrow(w - 54, 34, 15, sw=2.4, color=MINT)}</g>\n')
    for i, line in enumerate(lines):
        inner += f'  <text x="40" y="{92 + i * 24}" fill="{PAPER}" font-size="16">{line}</text>\n'
    inner += (f'  <text x="40" y="{tag_y}" fill="{MUTE}" font-size="14">&gt; {tag}'
              f'<tspan fill="{MINT}" class="cur"> █</tspan></text>\n')
    defs, body = framed(w, h, f"p{num}", inner, notch)
    save(f"project-{num}.svg", svg(w, h, body, defs))

# ---------- faixa de mangá: quatro quadros com as ilustrações do portfólio ----------
# Quadros inclinados como numa página de mangá; cada ilustração faz um zoom lento de
# câmera, fora de fase com as outras.
w, h = 1000, 236
top, bot = 8, h - 8
PANELS = [("panel-hands.jpg", 272), ("panel-dragon.jpg", 214), ("panel-kiara.jpg", 246), ("panel-cat.jpg", 226)]
gutter, slant = 14, 14
# divisórias entre quadros: cada uma inclinada para um lado (x no topo, x embaixo)
total = sum(pw for _, pw in PANELS)
splits, acc = [], 6
for k, (_, pw) in enumerate(PANELS[:-1]):
    acc += pw * (w - 12) / total
    o = slant if k % 2 == 0 else -slant
    splits.append((acc + o, acc - o))
lefts = [(6, 6)] + [(t + gutter / 2, b + gutter / 2) for t, b in splits]
rights = [(t - gutter / 2, b - gutter / 2) for t, b in splits] + [(w - 6, w - 6)]
defs, body = "", ""
for i, (img, _) in enumerate(PANELS):
    (lt, lb), (rt, rb) = lefts[i], rights[i]
    pts = f"{f1(lt)},{top} {f1(rt)},{top} {f1(rb)},{bot} {f1(lb)},{bot}"
    bx0, bx1 = min(lt, lb), max(rt, rb)
    defs += f'\n    <clipPath id="pn{i}"><polygon points="{pts}"/></clipPath>'
    body += (f'  <g clip-path="url(#pn{i})"><rect x="{f1(bx0)}" y="{top}" width="{f1(bx1 - bx0)}" height="{bot - top}" fill="{INK}"/>'
             f'<image href="{embed(img)}" x="{f1(bx0)}" y="{top}" width="{f1(bx1 - bx0)}" height="{bot - top}" '
             f'preserveAspectRatio="xMidYMid slice" class="drift" style="animation-delay:-{i * 4}s"/></g>\n'
             f'  <g {TICKING}><polygon points="{pts}" fill="none" stroke="{PAPER}" stroke-width="{STROKE}" '
             f'stroke-linejoin="round"/></g>\n')
save("strip.svg", svg(w, h, body, defs))

# ---------- stack: um card só, três colunas de teclas sem borda ----------
CHIP = "#1b1b1f"
GROUPS = [("Front-end", [("HTML5", 0), ("CSS3", 0), ("Tailwind", 0), ("TypeScript", 1), ("JavaScript", 1), ("React", 1)]),
          ("Back-end", [("Node.js", 1), ("PHP", 1), ("MySQL", 0)]),
          ("Ferramentas", [("Git", 0), ("GitHub", 0), ("Linux", 0), ("Shell", 0), ("Docker", 0), ("CI/CD", 0),
                           ("Figma", 0), ("UI/UX", 0)])]
w, col_w, key_h, gap = 1000, 284, 32, 8
cols, bottom, n = [], 0, 0
for ci, (title, items) in enumerate(GROUPS):
    x0 = 40 + ci * 312
    out = [text_path(title, x0, 88, 20, tracking=-0.2)]
    x, y = x0, 106
    for label, adv in items:
        kw = round(len(label) * 8.6 + 26 + (14 if adv else 0))
        if x + kw > x0 + col_w:
            x, y = x0, y + key_h + gap
        d = f' style="animation-delay:{f1(.3 + n * .04)}s"'
        out.append(f'<g class="fade"{d}><rect x="{x}" y="{y}" width="{kw}" height="{key_h}" rx="7" fill="{CHIP}"/>')
        tx_ = x + 13
        if adv:
            out.append(f'<circle cx="{x + 15}" cy="{y + key_h / 2}" r="3.2" fill="{MINT}"/>')
            tx_ += 13
        out.append(f'<text x="{tx_}" y="{y + 21}" fill="{MINT if adv else PAPER}" font-size="14">{label}</text></g>')
        x += kw + 7
        n += 1
    bottom = max(bottom, y + key_h)
    cols.append(out)
h = bottom + 60
inner = f'  <text x="40" y="46" fill="{MUTE}" font-size="14">~/stack</text>\n'
for ci, out in enumerate(cols):
    if ci:
        lx = 40 + ci * 312 - 16
        inner += f'  <line x1="{lx}" y1="68" x2="{lx}" y2="{bottom}" stroke="{LINE}" stroke-width="1.5" stroke-linecap="round"/>\n'
    inner += "  " + "\n  ".join(out) + "\n"
inner += (f'  <circle cx="45" cy="{h - 31}" r="3.2" fill="{MINT}"/>\n'
          f'  <text x="56" y="{h - 26}" fill="{MUTE}" font-size="13">estudos avançados</text>\n')
defs, body = framed(w, h, "st", inner)
save("stack.svg", svg(w, h, body, defs))

# ---------- fechamento: a cidade à noite e o personagem puxando conversa ----------
w, h = 1000, 260
inner = (f'  <image href="{embed("city.jpg")}" x="5" y="5" width="{w - 10}" height="{h - 10}" '
         f'preserveAspectRatio="xMidYMax slice" clip-path="url(#clip-cl)" opacity=".85"/>\n'
         f'  <rect x="5" y="5" width="{w - 10}" height="{h - 10}" fill="url(#shade)" clip-path="url(#clip-cl)"/>\n'
         f'  {stars(10, 300, 16, 980, 90, seed=11, mint=0)}\n')
# balão de fala com a frase do portfólio, digitada linha por linha
bx, by, bw, bh = 292, 46, 408, 96
inner += (f'  <g {TICKING}><path d="M{bx + 14} {by} H{bx + bw - 14} Q{bx + bw} {by} {bx + bw} {by + 14} '
          f'V{by + bh - 14} Q{bx + bw} {by + bh} {bx + bw - 14} {by + bh} H{bx + 46} L{bx - 34} {by + bh + 22} '
          f'L{bx + 20} {by + bh} H{bx + 14} Q{bx} {by + bh} {bx} {by + bh - 14} V{by + 14} Q{bx} {by} {bx + 14} {by} Z" '
          f'fill="{INK}" stroke="{PAPER}" stroke-width="{STROKE}" stroke-linejoin="round"/></g>\n'
          f'  <g class="type"><text x="{bx + 24}" y="{by + 40}" fill="{PAPER}" font-size="17">Tem um problema chato?</text></g>\n'
          f'  <g class="type" style="animation-delay:3.2s"><text x="{bx + 24}" y="{by + 68}" fill="{PAPER}" font-size="17">'
          f'Me chama no <tspan fill="{MINT}">LinkedIn</tspan>.<tspan fill="{MINT}" class="cur"> █</tspan></text></g>\n')
defs, body = framed(w, h, "cl", inner, "bl", dots=False)
defs += (f'\n    <linearGradient id="shade" x1="0" x2="1"><stop offset="0" stop-color="{INK}" stop-opacity=".2"/>'
         f'<stop offset=".55" stop-color="{INK}" stop-opacity=".55"/><stop offset="1" stop-color="{INK}" stop-opacity=".15"/>'
         f'</linearGradient>')
th = 232
tw_ = round(th * 300 / 309)
body += f'  <image href="{embed("talking.png")}" x="34" y="{h - th}" width="{tw_}" height="{th}"/>\n'
save("closing.svg", svg(w, h, body, defs))
print("ok")
