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
    .marq  {{ animation:marq 18s linear infinite; }}
    @keyframes draw   {{ from{{stroke-dashoffset:1}} }}
    @keyframes blink  {{ 50%{{opacity:0}} }}
    @keyframes type   {{ from{{clip-path:inset(0 100% 0 0)}} }}
    @keyframes marq   {{ to{{transform:translateX(-50%)}} }}
    @media (prefers-reduced-motion: reduce) {{ * {{ animation:none !important; }} }}
  </style>"""


# Do README antigo: o traço "fervendo" de nanquim e a granulação animada.
# Só nos desenhos (espirais, raios, ilustrações); molduras e texto ficam limpos como no portfólio.
FILTERS = """
    <filter id="boil" filterUnits="userSpaceOnUse" x="-100" y="-100" width="1200" height="1000">
      <feTurbulence type="fractalNoise" baseFrequency="0.026" numOctaves="2" seed="1" result="n">
        <animate attributeName="seed" values="1;7;13;21" dur="0.6s" calcMode="discrete" repeatCount="indefinite"/>
      </feTurbulence>
      <feDisplacementMap in="SourceGraphic" in2="n" scale="2.6"/>
    </filter>
    <filter id="tick" filterUnits="userSpaceOnUse" x="-100" y="-100" width="1200" height="1000">
      <feTurbulence type="fractalNoise" baseFrequency="0.035" numOctaves="2" seed="1" result="n">
        <animate attributeName="seed" values="1;7;13;21" dur="0.5s" calcMode="discrete" repeatCount="indefinite"/>
      </feTurbulence>
      <feDisplacementMap in="SourceGraphic" in2="n" scale="4"/>
    </filter>
    <filter id="grain">
      <feTurbulence type="fractalNoise" baseFrequency="0.9" seed="2">
        <animate attributeName="seed" values="2;5;8;11;14" dur="0.5s" calcMode="discrete" repeatCount="indefinite"/>
      </feTurbulence>
      <feColorMatrix values="0 0 0 0 1  0 0 0 0 1  0 0 0 0 1  0 0 0 .06 0"/>
      <feComposite in2="SourceGraphic" operator="in"/>
    </filter>"""

INKED = 'filter="url(#boil)"'
# o "tique" das bordas da primeira versão, agora nas espirais: mais forte e mais rápido
TICKING = 'filter="url(#tick)"'


def svg(w, h, body, defs="", grain=False):
    g = (f'\n  <rect x="5" y="5" width="{w - 10}" height="{h - 10}" rx="23" filter="url(#grain)" pointer-events="none"/>'
         if grain else "")
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" '
            f'font-family="{MONO}">\n  <defs>{FILTERS}{defs}\n  </defs>{STYLE}\n{body}{g}\n</svg>\n')


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


def logo(x, y, size, sw_px=3, dot=MINT):
    """Logo do portfólio (viewBox 0..100) escalado para `size` px."""
    k = size / 100
    path = ('M10 10 L83 10 Q90 10 90 17 L90 83 Q90 90 83 90 L17 90 Q10 90 10 83 L10 32 Q10 25 17 25 '
            'L68 25 Q75 25 75 32 L75 68 Q75 75 68 75 L32 75 Q25 75 25 68 L25 47 Q25 40 32 40 L53 40 '
            'Q60 40 60 47 L60 53 Q60 60 53 60 L40 60')
    out = (f'<g transform="translate({f1(x)} {f1(y)}) scale({k:.4f})" fill="none" stroke="{PAPER}" '
           f'stroke-width="{f1(sw_px / k)}" stroke-linecap="round" stroke-linejoin="round"><path d="{path}"/>')
    if dot:
        out += f'<circle cx="40" cy="60" r="{f1(sw_px / k * .9)}" fill="{dot}" stroke="none"/>'
    return out + "</g>"


# ---------- cartão: fundo, grade de pontos, moldura com notch ----------
NOTCH = {"tr": lambda w, h: (w - 48 - 28, -4, 28, 12), "rb": lambda w, h: (w - 8, h - 48 - 28, 12, 28),
         "bl": lambda w, h: (48, h - 8, 28, 12), "lt": lambda w, h: (-4, 48, 12, 28)}


def card(w, h, uid, notch="tr", rx=28, dots=True):
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


# ---------- header ----------
w, h = 1000, 300
defs, body = card(w, h, "hd", "tr")
body += f'  <g {TICKING}>{spiral(176, w - 60 - 176, (h - 176) // 2, cls="draw")}</g>\n'
tx = 300
body += "  " + text_path("Eduardo", tx - 4, 146, 100, tracking=-1) + "\n"
body += f'  <text x="{tx}" y="194" fill="{MUTE}" font-size="15" letter-spacing="5">DEV. FULL STACK</text>\n'
body += (f'  <g class="type"><text x="{tx}" y="236" fill="{PAPER}" font-size="16">&gt; front · back · tools · always looping'
         f'<tspan fill="{MINT}" class="cur"> █</tspan></text></g>\n')
# avatar (assets/avatar.png, fundo recortado), grande e sem moldura, à esquerda,
# desenhado por cima da borda de baixo: o moletom "senta" na borda do header.
with open(os.path.join(HERE, "..", "assets", "avatar.png"), "rb") as f:
    avatar = base64.b64encode(f.read()).decode()
ah = 276
aw = round(ah * 440 / 550)
body += (f'  <image href="data:image/png;base64,{avatar}" x="36" y="{h - ah}" width="{aw}" height="{ah}"/>\n')
save("header.svg", svg(w, h, body, defs, grain=True))

# ---------- botões de navegação ----------
NAV = [("projetos", "projetos"), ("stack", "stack"), ("atividade", "atividade"), ("contato", "contato")]
for slug, label in NAV:
    w, h = 190, 52
    body = (f'  <rect width="{w}" height="{h}" rx="16" fill="{INK}"/>\n'
            f'  <g {TICKING}><rect x="4" y="4" width="{w - 8}" height="{h - 8}" rx="13" fill="none" '
            f'stroke="{PAPER}" stroke-width="2"/></g>\n'
            f'  <text x="{w / 2}" y="{h / 2 + 5}" text-anchor="middle" fill="{PAPER}" font-size="16" '
            f'font-weight="700">{label}</text>')
    save(f"nav-{slug}.svg", svg(w, h, body))

# ---------- títulos de seção ----------
SECTIONS = [("projetos", "Projetos em destaque"), ("stack", "Stack & ferramentas"),
            ("atividade", "Atividade"), ("contato", "Contato")]
for slug, title in SECTIONS:
    w, h = 1000, 84
    # uma pincelada só: sai do título como sublinhado, corre até a direita e enrola
    # numa espiral quadrada. Espiral espelhada na vertical para a linha entrar por baixo.
    tw = text_width(title, 34, -0.3)
    ss, sy = 46, 17                       # espiral de 46px; a linha fica em y = sy + ss
    sx = w - 32 - ss
    lead = sx - (32 + tw + 22)
    body = (f'  <rect width="{w}" height="{h}" rx="22" fill="{INK}"/>\n'
            f'  {text_path(title, 32, 55, 34, tracking=-0.3)}\n'
            f'  <g {TICKING}><g transform="translate(0 {2 * sy + ss}) scale(1 -1)">'
            f'{spiral(ss, sx, sy, lead=lead)}</g></g>')
    save(f"title-{slug}.svg", svg(w, h, body))


# ---------- banners de projeto ----------
PROJECTS = [("01", "Vanish", "vanish", "electron · typescript", "tr"),
            ("02", "Analyst SQL", "analyst-sql", "next.js · typescript · mysql", "rb"),
            ("03", "PrintScream", "PrintScream", "typescript · puppeteer", "bl")]
for num, name, repo, tag, notch in PROJECTS:
    w, h = 1000, 220
    defs, body = card(w, h, f"p{num}", notch)
    body += (f'  <text x="48" y="58" fill="{MUTE}" font-size="14">Eduardo-Virissimo/{repo}</text>\n'
             f'  {text_path(name, 46, 124, 56, tracking=-0.5)}\n'
             f'  <text x="48" y="170" fill="{MUTE}" font-size="16">&gt; {tag}<tspan fill="{MINT}" class="cur"> █</tspan></text>')
    save(f"project-{num}.svg", svg(w, h, body, defs, grain=True))

# ---------- painel da stack ----------
w, h = 440, 740
defs, body = card(w, h, "st", "tr")
defs += f'\n    <clipPath id="marq"><rect x="24" y="{h - 70}" width="{w - 48}" height="40"/></clipPath>'
body += (f'  <text x="36" y="48" fill="{MUTE}" font-size="15">~/stack.loop</text>\n'
         f'  <line x1="24" y1="72" x2="{w - 24}" y2="72" stroke="{LINE}" stroke-width="2"/>\n')
GROUPS = [("Front-end", [("HTML5", 0), ("CSS3 / Tailwind", 0), ("TypeScript / JS / React", 1)]),
          ("Back-end", [("Node.js", 1), ("PHP", 1), ("MySQL", 0)]),
          ("Ferramentas", [("Git / GitHub", 0), ("Linux / Shell", 0), ("Docker / CI/CD", 0), ("Figma / UI/UX", 0)])]
y = 126
for title, items in GROUPS:
    body += f"  {text_path(title, 36, y, 26, tracking=-0.2)}\n"
    top, y = y + 12, y + 40
    for label, adv in items:
        body += (f'  <path d="M46 {top} V{y - 11} Q46 {y - 6} 51 {y - 6} H62" fill="none" stroke="{DIM}" '
                 f'stroke-width="2" stroke-linecap="round"/>\n'
                 f'  <circle cx="69" cy="{y - 6}" r="4" fill="{MINT if adv else DIM}"/>\n'
                 f'  <text x="84" y="{y}" fill="{PAPER}" font-size="18">{label}</text>\n')
        top, y = y - 6, y + 32
    y += 34
phrase = "".join(f'{t} <tspan fill="{MINT}">✦</tspan> ' for t in ("FRONT-END", "BACK-END", "TOOLS", "ALWAYS LEARNING"))
body += (f'  <circle cx="42" cy="{h - 100}" r="4" fill="{MINT}"/>\n'
         f'  <text x="56" y="{h - 94}" fill="{MUTE}" font-size="15">estudos avançados</text>\n'
         f'  <line x1="24" y1="{h - 70}" x2="{w - 24}" y2="{h - 70}" stroke="{PAPER}" stroke-width="1.8" {INKED}/>\n'
         f'  <line x1="24" y1="{h - 30}" x2="{w - 24}" y2="{h - 30}" stroke="{PAPER}" stroke-width="1.8" {INKED}/>\n'
         f'  <g clip-path="url(#marq)"><g class="marq">'
         f'<text x="24" y="{h - 44}" fill="{PAPER}" font-size="14" font-weight="700" letter-spacing="3">{phrase}{phrase}</text>'
         f'</g></g>')
save("panel.svg", svg(w, h, body, defs, grain=True))

# ---------- rodapé ----------
w, h = 1000, 150
defs, body = card(w, h, "ft", "bl")
body += (f'  <g {TICKING}>{logo(466, 41, 68, 4.4)}</g>\n'
         f'  <text x="80" y="80" fill="{MUTE}" font-size="13" letter-spacing="4">THANKS FOR STOPPING BY</text>\n'
         f'  <text x="920" y="80" text-anchor="end" fill="{MUTE}" font-size="13" letter-spacing="4">'
         f'KEEP LOOPING <tspan fill="{MINT}">✦</tspan></text>')
save("footer.svg", svg(w, h, body, defs, grain=True))
print("ok")
