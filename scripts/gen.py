"""Gera os SVGs animados (estilo nanquim P&B) do README."""
import os, sys

OUT = sys.argv[1] if len(sys.argv) > 1 else "assets"
os.makedirs(OUT, exist_ok=True)
FONT = "'JetBrains Mono','Fira Code',Consolas,'Courier New',monospace"

DEFS = """
  <defs>
    <filter id="boil" x="-5%" y="-5%" width="110%" height="110%">
      <feTurbulence type="fractalNoise" baseFrequency="0.035" numOctaves="2" seed="1" result="n">
        <animate attributeName="seed" values="1;7;13;21" dur="0.5s" calcMode="discrete" repeatCount="indefinite"/>
      </feTurbulence>
      <feDisplacementMap in="SourceGraphic" in2="n" scale="{scale}"/>
    </filter>
    <filter id="grain">
      <feTurbulence type="fractalNoise" baseFrequency="0.9" seed="2">
        <animate attributeName="seed" values="2;5;8;11;14" dur="0.4s" calcMode="discrete" repeatCount="indefinite"/>
      </feTurbulence>
      <feColorMatrix values="0 0 0 0 1  0 0 0 0 1  0 0 0 0 1  0 0 0 .07 0"/>
    </filter>
  </defs>
  <style>
    .spin  {{ transform-box:fill-box; transform-origin:center; animation:spin 12s linear infinite; }}
    .spinR {{ transform-box:fill-box; transform-origin:center; animation:spin 8s linear infinite reverse; }}
    .br    {{ transform-box:fill-box; transform-origin:center; animation:br 3s ease-in-out infinite; }}
    .wave  {{ animation:wave 2.4s ease-in-out infinite alternate; }}
    .cur   {{ animation:blink 1s steps(1) infinite; }}
    .in    {{ opacity:0; animation:in .4s steps(3) forwards; }}
    @keyframes spin  {{ to{{transform:rotate(360deg)}} }}
    @keyframes br    {{ 0%,100%{{transform:scale(1)}} 50%{{transform:scale(.75)}} }}
    @keyframes wave  {{ from{{transform:translateY(-6px)}} to{{transform:translateY(6px)}} }}
    @keyframes blink {{ 50%{{opacity:0}} }}
    @keyframes in    {{ to{{opacity:1}} }}
  </style>"""


def svg(w, h, body, scale=3):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" '
            f'font-family="{FONT}">{DEFS.format(scale=scale)}\n'
            f'  <rect width="{w}" height="{h}" fill="#000"/>\n{body}\n'
            f'  <rect width="{w}" height="{h}" filter="url(#grain)"/>\n</svg>\n')


def save(name, content):
    with open(os.path.join(OUT, name), "w", encoding="utf-8") as f:
        f.write(content)


# ---------- botões de navegação ----------
NAV = [("projetos", "PROJETOS"), ("stack", "STACK"), ("andamento", "EM ANDAMENTO"),
       ("atividade", "ATIVIDADE"), ("contato", "CONTATO")]
for i, (slug, label) in enumerate(NAV):
    w, h = 190, 52
    body = f"""
  <rect x="5" y="5" width="{w-10}" height="{h-10}" rx="4" fill="none" stroke="#fff" stroke-width="1.8" filter="url(#boil)"/>
  <g transform="translate(26 {h/2})" fill="none" stroke="#fff" filter="url(#boil)">
    <circle r="8" stroke-width="1.4" stroke-dasharray="3 3" class="spin" style="animation-delay:-{i}s"/>
    <circle r="2.5" fill="#fff"/>
  </g>
  <text x="{(w+30)/2}" y="{h/2+5}" text-anchor="middle" fill="#fff" font-size="13" font-weight="700" letter-spacing="2">{label}</text>"""
    save(f"nav-{slug}.svg", svg(w, h, body, scale=2.5))

# ---------- títulos de seção ----------
SECTIONS = [("projetos", "01", "PROJETOS EM DESTAQUE"), ("stack", "02", "STACK &amp; FERRAMENTAS"),
            ("andamento", "03", "EM ANDAMENTO"), ("atividade", "04", "ATIVIDADE"), ("contato", "05", "CONTATO")]
for slug, num, title in SECTIONS:
    w, h = 1000, 90
    body = f"""
  <text x="20" y="58" fill="#fff" font-size="34" font-weight="800" filter="url(#boil)">{num}</text>
  <text x="90" y="56" fill="#fff" font-size="20" font-weight="700" letter-spacing="5">{title}</text>
  <line x1="20" y1="74" x2="900" y2="74" stroke="#fff" stroke-width="1.8" filter="url(#boil)"/>
  <g transform="translate(950 45)" fill="none" stroke="#fff" filter="url(#boil)">
    <circle r="28" stroke-width="1.2" stroke-dasharray="2 5" class="spin"/>
    <circle r="18" stroke-width="2" stroke-dasharray="10 6" class="spinR"/>
    <circle r="6" fill="#fff" class="br"/>
  </g>"""
    save(f"title-{slug}.svg", svg(w, h, body))

# ---------- banners de projeto ----------
def art_rings():
    return """
  <g transform="translate(840 110)" fill="none" stroke="#fff" filter="url(#boil)">
    <circle r="80" stroke-width="1.2" stroke-dasharray="2 7" class="spin"/>
    <circle r="62" stroke-width="2" stroke-dasharray="24 10" class="spinR"/>
    <circle r="44" stroke-width="1.3" stroke-dasharray="4 4" class="spin"/>
    <g class="br"><circle r="26" stroke-width="2"/><circle r="9" fill="#fff"/></g>
  </g>"""

def art_waves():
    lines = []
    for k in range(7):
        y = 50 + k * 20
        d = f"M720 {y} " + " ".join(f"q 20 {(-14 if j % 2 == 0 else 14)} 40 0" for j in range(6))
        lines.append(f'<path d="{d}" class="wave" style="animation-delay:-{k*0.3:.1f}s"/>')
    return f"""
  <g fill="none" stroke="#fff" stroke-width="1.8" stroke-linecap="round" filter="url(#boil)">
    {''.join(lines)}
  </g>"""

def art_eye():
    return """
  <g transform="translate(840 110)" fill="none" stroke="#fff" stroke-width="2" filter="url(#boil)">
    <path d="M-110 0 Q0 -80 110 0 Q0 80 -110 0 Z"/>
    <circle r="34" stroke-dasharray="6 4" class="spin"/>
    <g class="br"><circle r="18" fill="#fff"/></g>
    <g class="spinR"><line x1="0" y1="-92" x2="0" y2="-76"/><line x1="0" y1="92" x2="0" y2="76"/>
      <line x1="-60" y1="-70" x2="-52" y2="-58"/><line x1="60" y1="-70" x2="52" y2="-58"/>
      <line x1="-60" y1="70" x2="-52" y2="58"/><line x1="60" y1="70" x2="52" y2="58"/></g>
  </g>"""

PROJECTS = [("01", "VANISH", "limpeza segura de temporários do Windows", art_rings),
            ("02", "ANALYST-SQL", "agente de IA que responde em SQL", art_waves),
            ("03", "PRINTSCREAM", "gera PDFs de páginas web a partir da URL", art_eye)]
for num, name, tag, art in PROJECTS:
    w, h = 1000, 220
    body = f"""
  <rect x="8" y="8" width="{w-16}" height="{h-16}" rx="6" fill="none" stroke="#fff" stroke-width="2" filter="url(#boil)"/>
  <text x="44" y="96" fill="none" stroke="#fff" stroke-width="2" font-size="80" font-weight="800" filter="url(#boil)">{num}</text>
  <text x="46" y="148" fill="#fff" font-size="30" font-weight="800" letter-spacing="3" class="in" style="animation-delay:.2s">{name}</text>
  <text x="46" y="182" fill="#9a9a9a" font-size="15" letter-spacing="1" class="in" style="animation-delay:.5s">&gt; {tag}<tspan fill="#fff" class="cur"> █</tspan></text>
  {art()}"""
    save(f"project-{num}.svg", svg(w, h, body))

# ---------- rodapé ----------
w, h = 1000, 150
body = """
  <line x1="20" y1="20" x2="980" y2="20" stroke="#fff" stroke-width="1.8" filter="url(#boil)"/>
  <g transform="translate(500 82)" fill="none" stroke="#fff" filter="url(#boil)">
    <g class="spin" stroke-width="2.5" stroke-linecap="round">
      <line x1="0" y1="-50" x2="0" y2="-38"/><line x1="0" y1="50" x2="0" y2="38"/>
      <line x1="-50" y1="0" x2="-38" y2="0"/><line x1="50" y1="0" x2="38" y2="0"/>
      <line x1="35" y1="35" x2="27" y2="27"/><line x1="-35" y1="-35" x2="-27" y2="-27"/>
      <line x1="35" y1="-35" x2="27" y2="-27"/><line x1="-35" y1="35" x2="-27" y2="27"/>
    </g>
    <g class="br"><circle r="22" stroke-width="2"/><circle r="8" fill="#fff"/></g>
  </g>
  <text x="80" y="90" fill="#9a9a9a" font-size="14" letter-spacing="4">THANKS FOR STOPPING BY</text>
  <text x="920" y="90" text-anchor="end" fill="#9a9a9a" font-size="14" letter-spacing="4">KEEP LOOPING ✦</text>"""
save("footer.svg", svg(w, h, body))
print("ok")
