// Gera os painéis SVG do README. Parente do portfólio (coluna escura, faixa de pixels, nome em
// itálico, Kiara no contato), mas com cara própria: um redemoinho de LED, o player do Spotify caindo
// em cima da onda da música em LED, a stack como constelações e pixels pingando no topo e no
// rodapé, com uma estrela cadente atravessando o topo.
//
// Layout (larguras em 1000): topo 100 · sobre 66 + música 34 · stack 100 · redemoinho 34 + contato 66
// · três links · rodapé 100. Painéis lado a lado têm a mesma altura.
//
// Todo o texto vira contorno (scripts/glyphs-*.json, gerados por build-glyphs.mjs), então o README
// renderiza igual em qualquer máquina. Imagens vão embutidas (data URI): o GitHub não deixa um SVG
// dentro de <img> carregar arquivo de fora.
//
//   node scripts/gen.mjs [pasta_de_saida]
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const HERE = path.dirname(fileURLToPath(import.meta.url));
const OUT = process.argv[2] || path.join(HERE, "..", "assets");
fs.mkdirSync(OUT, { recursive: true });

// As cores do portfólio (tema escuro) e o "papel" do gráfico de git.
const C = {
  col: "#0b0b0e",
  border: "#26262c",
  rule: "#1d1d22",
  line: "#2a2a31",
  strong: "#3a3a42",
  text: "#f4f4f1",
  dim: "#a1a19b",
  mute: "#86867f",
  chip: "#15151a",
  paper: "#f2f2f0",
  ink: "#0b0b0b",
  edge: "#d6d6d2",
};
const PAD = 44; // margem interna
const CONTACT_H = 350; // o contato e o redemoinho, lado a lado, têm a mesma altura
const EASE = "cubic-bezier(.16,1,.3,1)";
const r = (v) => (Math.round(v * 10) / 10).toString();
const esc = (s) => s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/"/g, "&quot;");

// ---------- texto em contorno ----------
class Font {
  constructor(name) {
    const d = JSON.parse(fs.readFileSync(path.join(HERE, `glyphs-${name}.json`), "utf8"));
    Object.assign(this, { name, upm: d.upm, g: d.glyphs });
  }
  glyph(c) {
    const g = this.g[c];
    if (!g) throw new Error(`sem glifo para "${c}" em ${this.name}`);
    return g;
  }
  width(s, size) {
    return ([...s].reduce((a, c) => a + this.glyph(c).adv, 0) * size) / this.upm;
  }
  // y é a linha de base
  text(ctx, s, x, y, size, { fill = C.text, anchor = "start" } = {}) {
    const k = size / this.upm;
    if (anchor === "end") x -= this.width(s, size);
    if (anchor === "middle") x -= this.width(s, size) / 2;
    let cx = 0;
    let uses = "";
    for (const c of s) {
      const g = this.glyph(c);
      if (g.d) {
        const id = `${this.name}-${c.codePointAt(0).toString(16)}`;
        ctx.set(id, g.d);
        uses += `<use href="#${id}" x="${r(cx)}"/>`;
      }
      cx += g.adv;
    }
    return `<g fill="${fill}" transform="translate(${r(x)} ${r(y)}) scale(${k.toFixed(5)} ${(-k).toFixed(5)})">${uses}</g>`;
  }
}
const SANS = new Font("sans");
const BOLD = new Font("bold");
const MONO = new Font("mono");
const SERIF = new Font("serif");
const HAND = new Font("hand");

/**
 * Parágrafo com quebra de linha automática. `{Nome}` no texto sai na cor principal (como as
 * tecnologias citadas no "Sobre mim" do portfólio). Devolve o SVG e a altura ocupada.
 */
function para(ctx, text, x, y, size, maxW, { font = SANS, fill = C.dim, hi = C.text, lh = 1.6 } = {}) {
  const words = [];
  for (const [i, part] of text.split(/\{([^}]+)\}/).entries()) {
    for (const w of part.split(/(\s+)/)) if (w) words.push({ w, hi: i % 2 === 1 });
  }
  const space = (w) => /^\s+$/.test(w);
  const lines = [[]];
  let lineW = 0;
  for (const word of words) {
    const ww = font.width(word.w, size);
    if (space(word.w)) {
      if (lines.at(-1).length) {
        lines.at(-1).push(word);
        lineW += ww;
      }
      continue;
    }
    // Pontuação nunca começa uma linha: fica grudada na palavra de antes.
    const glued = /^[,.;:!?)]/.test(word.w);
    if (lineW + ww > maxW && lines.at(-1).length && !glued) {
      while (lines.at(-1).length && space(lines.at(-1).at(-1).w)) lines.at(-1).pop();
      lines.push([]);
      lineW = 0;
    }
    lines.at(-1).push(word);
    lineW += ww;
  }
  let svg = "";
  lines.forEach((line, li) => {
    let cx = x;
    const by = y + li * size * lh;
    for (const word of line) {
      if (!space(word.w)) svg += font.text(ctx, word.w, cx, by, size, { fill: word.hi ? hi : fill });
      cx += font.width(word.w, size);
    }
  });
  return { svg, height: lines.length * size * lh };
}

// ---------- ícones (os mesmos do portfólio: Lucide nos títulos, simple-icons nas ferramentas) ----------
const ICONS = JSON.parse(fs.readFileSync(path.join(HERE, "icons.json"), "utf8"));
function lucide(name, x, y, size, color = C.text, sw = 1.6) {
  const k = size / 24;
  const nodes = ICONS.lucide[name]
    .map(([tag, attrs]) => `<${tag} ${Object.entries(attrs).map(([a, v]) => `${a}="${v}"`).join(" ")}/>`)
    .join("");
  return `<g transform="translate(${r(x)} ${r(y)}) scale(${k})" fill="none" stroke="${color}" stroke-width="${r(sw / k)}" stroke-linecap="round" stroke-linejoin="round">${nodes}</g>`;
}
function brand(name, x, y, size, color = C.dim) {
  return `<path transform="translate(${r(x)} ${r(y)}) scale(${size / 24})" fill="${color}" d="${ICONS.brands[name]}"/>`;
}

// ---------- peças comuns ----------
/** O painel: a "coluna" escura do portfólio, com a borda fina. */
const panel = (w, h, fill = C.col, stroke = C.border) =>
  `<rect x="1" y="1" width="${w - 2}" height="${h - 2}" rx="18" fill="${fill}" stroke="${stroke}" stroke-width="1.5"/>`;
const clipPanel = (id, w, h) => `<clipPath id="${id}"><rect x="1" y="1" width="${w - 2}" height="${h - 2}" rx="18"/></clipPath>`;

/** Título de seção: ícone, nome e um dado curto à direita (como no portfólio). */
function head(ctx, w, y, icon, title, aside) {
  let s = lucide(icon, PAD, y - 21, 25) + BOLD.text(ctx, title, PAD + 38, y, 25);
  if (aside) s += SANS.text(ctx, aside, w - PAD, y - 2, 15, { fill: C.mute, anchor: "end" });
  return s;
}

// Entrada: cada bloco sobe e aparece uma vez; sem animação, o estado final é o de base.
const IN = `
    .in { animation: in .9s ${EASE} backwards; }
    @keyframes in { from { opacity: 0; transform: translateY(12px); } }`;
const delay = (s) => `style="animation-delay:${s}s"`;

// Pixels que piscam (a faixa do topo e os brilhinhos dos cantos).
const TWINKLE = `
    .t1 { animation: tw 3.2s ease-in-out infinite; }
    .t2 { animation: tw 4.1s ease-in-out .7s infinite; }
    .t3 { animation: tw 2.6s ease-in-out 1.3s infinite; }
    .t4 { animation: tw 5s ease-in-out 2s infinite; }
    @keyframes tw { 50% { opacity: .2; } }`;

function write(name, w, h, { label, body, style = "", defs = "", ctx }) {
  const glyphs = [...ctx].map(([id, d]) => `<path id="${id}" d="${d}"/>`).join("");
  const out = `<svg xmlns="http://www.w3.org/2000/svg" width="${w}" height="${h}" viewBox="0 0 ${w} ${h}" role="img" aria-label="${esc(label)}">
  <defs>${glyphs}${defs}</defs>
  <style>${style}
    @media (prefers-reduced-motion: reduce) { * { animation: none !important; } }
  </style>
${body}
</svg>
`;
  fs.writeFileSync(path.join(OUT, `${name}.svg`), out);
  console.log(`${name}.svg  ${w}x${h}  ${(out.length / 1024).toFixed(1)} KB`);
}

const embed = (file, type) =>
  `data:image/${type};base64,${fs.readFileSync(path.join(HERE, file)).toString("base64")}`;

// ---------- aleatório determinístico e ruído (o mesmo desenho a cada geração) ----------
function rng(seed) {
  let s = seed >>> 0 || 1;
  return () => {
    s ^= s << 13;
    s ^= s >>> 17;
    s ^= s << 5;
    return (s >>> 0) / 4294967296;
  };
}
function noise2(seed) {
  const hash = (x, y) => {
    let h = (x * 374761393 + y * 668265263 + seed * 2654435761) >>> 0;
    h = Math.imul(h ^ (h >>> 13), 1274126177);
    return ((h ^ (h >>> 16)) >>> 0) / 4294967296;
  };
  const smooth = (t) => t * t * (3 - 2 * t);
  return (x, y) => {
    const xi = Math.floor(x), yi = Math.floor(y);
    const xf = smooth(x - xi), yf = smooth(y - yi);
    const a = hash(xi, yi), b = hash(xi + 1, yi), c = hash(xi, yi + 1), d = hash(xi + 1, yi + 1);
    return a + (b - a) * xf + (c - a) * yf + (a - b - c + d) * xf * yf;
  };
}
const BAYER = [0, 8, 2, 10, 12, 4, 14, 6, 3, 11, 1, 9, 15, 7, 13, 5].map((v) => (v + 0.5) / 16);
const TONES = ["#2a2a30", "#3a3a40", "#55555a", "#77777a", "#9a9a98", "#c4c4c0"];

/**
 * A faixa de pixels (a mesma ideia do PixelDrip do portfólio): `rows` linhas escorrendo do topo do
 * painel (ou subindo do pé, com `up`), com nuvens de ruído, pontilhado Bayer, pixels piscando, um
 * brilho atravessando e gotas caindo.
 */
function pixelStrip({ id, w, rows, up = false, seed = 7, height }) {
  const CELL = 8, SIZE = 6;
  const cols = w / CELL;
  const rand = rng(seed);
  const cloud = noise2(seed);
  const depth = Array.from({ length: cols }, (_, x) =>
    rand() < 0.1 ? rows : rows * (0.5 + 0.35 * cloud(x * 0.18, 3.7)),
  );
  // Os pixels que caem (ou sobem) saem das colunas que escorrem até o fim. Para a animação acontecer
  // na faixa inteira, e não só num lado, ela é dividida em trechos e cada trecho tem uma coluna
  // dessas (se o sorteio não deu nenhuma ali, uma coluna do trecho passa a escorrer até o fim).
  // Sorteio próprio, para não mudar o resto do desenho da faixa.
  const pick = rng(seed + 1000);
  const SEGMENTS = 10;
  const dropCols = [];
  for (let s = 0; s < SEGMENTS; s++) {
    const a = Math.floor((s * cols) / SEGMENTS), b = Math.floor(((s + 1) * cols) / SEGMENTS);
    const longs = [];
    for (let x = a; x < b; x++) if (depth[x] >= rows) longs.push(x);
    const col = longs.length ? longs[Math.floor(pick() * longs.length)] : a + Math.floor(pick() * (b - a));
    depth[col] = rows;
    dropCols.push(col);
  }
  const yOf = (row) => (up ? height - (row + 1) * CELL + 1 : row * CELL + 1);
  let rects = "";
  for (let x = 0; x < cols; x++) {
    for (let y = 0; y < rows; y++) {
      const v = 1 - Math.min(1, y / depth[x]) ** 2.2;
      const density = v * (0.45 + 0.8 * cloud(x * 0.09, y * 0.17));
      if (density * 1.15 < BAYER[((y & 3) << 2) | (x & 3)]) continue;
      const tone = Math.min(TONES.length - 1, Math.floor(density * TONES.length * (0.7 + rand() * 0.5)));
      const fill = rand() < 0.012 ? "#ffffff" : TONES[tone];
      const cls = rand() < 0.16 ? ` class="t${1 + Math.floor(rand() * 4)}"` : "";
      rects += `<rect x="${x * CELL + 1}" y="${yOf(y)}" width="${SIZE}" height="${SIZE}" rx="1" fill="${fill}"${cls}/>`;
    }
  }
  // Um pixel caindo por trecho, com atrasos sorteados (senão eles iriam em fila da esquerda para a
  // direita).
  let drops = "";
  dropCols.forEach((x) => {
    drops += `<rect class="drop" x="${x * CELL + 1}" y="${yOf(rows - 1)}" width="${SIZE}" height="${SIZE}" rx="1" fill="#e9e9e4" style="animation-delay:${(pick() * 3.6).toFixed(1)}s"/>`;
  });
  const bandTop = up ? height - rows * CELL : 0;
  const svg = `<g id="${id}">${rects}</g>
  <g mask="url(#${id}-m)"><rect class="glint" x="-300" y="${bandTop}" width="220" height="${rows * CELL}" fill="url(#${id}-g)"/></g>
  ${drops}`;
  const defs = `<mask id="${id}-m"><use href="#${id}"/></mask><linearGradient id="${id}-g" x1="0" x2="1"><stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset=".5" stop-color="#fff" stop-opacity=".6"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>`;
  const style = `${TWINKLE}
    .glint { animation: glint 7s ${EASE} 1s infinite; }
    @keyframes glint { 0% { transform: translateX(0); } 60%, 100% { transform: translateX(${w + 400}px); } }
    .drop { opacity: 0; animation: drop 3.6s ease-in infinite; }
    @keyframes drop { 0% { opacity: 0; transform: translateY(0); } 15% { opacity: 1; } 100% { opacity: 0; transform: translateY(${up ? -40 : 40}px); } }`;
  return { svg, defs, style };
}


// ======================================================================================
// Topo: a faixa de pixels, o nome em itálico e "Dev Full Stack". Só isso.
// ======================================================================================
{
  const ctx = new Map();
  const W = 1000, H = 420;
  const strip = pixelStrip({ id: "px", w: W, rows: 27, seed: 11, height: H });
  const body = `${panel(W, H)}
  <g clip-path="url(#hc)">${strip.svg}</g>
  <g class="in" ${delay(0.1)}>${SERIF.text(ctx, "Eduardo T. Viríssimo", PAD + 2, 328, 76)}</g>
  <g class="in" ${delay(0.3)}>${MONO.text(ctx, "Dev Full Stack", PAD + 6, 376, 20, { fill: C.dim })}</g>
  <g class="star">${[0, 1, 2, 3, 4, 5].map((i) => `<rect x="${-i * 8}" y="${-i * 4}" width="6" height="6" rx="1" fill="#fff" opacity="${r(1 - i * 0.17)}"/>`).join("")}</g>`;
  write("panel-hero", W, H, {
    label: "Eduardo T. Viríssimo. Dev Full Stack.",
    body,
    ctx,
    defs: clipPanel("hc", W, H) + strip.defs,
    style:
      IN +
      strip.style +
      `
    /* Estrela cadente: atravessa o topo em diagonal de vez em quando. */
    .star { opacity: 0; animation: star 11s linear 2.5s infinite; }
    @keyframes star { 0% { opacity: 0; transform: translate(120px, 20px); } 1% { opacity: 1; } 9% { opacity: 1; } 12%, 100% { opacity: 0; transform: translate(${W - 140}px, 230px); } }`,
  });
}

// ======================================================================================
// Redemoinho (34%, à esquerda do contato): um painel de LED com os pixels cinza da faixa do topo e
// um vórtice de dois braços girando e puxando para o centro, como um ralo. Cada LED acende quando
// um braço passa por ele (a fase dele no redemoinho vira o atraso da animação), então os braços
// têm a mesma espessura em toda parte e giram sem sair da grade. O miolo fica escuro, como um
// buraco, e a borda vai apagando.
// ======================================================================================
{
  const W = 340, H = CONTACT_H;
  const CELL = 8, SIZE = 6;
  const COLS = Math.floor((W - 16) / CELL), ROWS = Math.floor((H - 16) / CELL);
  const GX0 = (W - COLS * CELL) / 2, GY0 = (H - ROWS * CELL) / 2;
  const ccx = (COLS - 1) / 2, ccy = (ROWS - 1) / 2;
  const RMAX = Math.min(COLS, ROWS) / 2; // raio útil, em células

  const T = 3.2; // segundos para um braço dar a volta da fase
  const PHASES = 32; // quantos atrasos diferentes (classes p0..p31)
  const ARMS = 2;
  const TWIST = 1.45; // quanto os braços se enrolam (espiral logarítmica)
  // Faixas de raio: o brilho máximo de cada LED depende de onde ele está (buraco escuro no meio,
  // mais claro no anel do meio, apagando na borda).
  const BANDS = ["#3a3a42", "#77777a", "#c4c4c0", "#e9e9e4", "#c4c4c0", "#9a9a98", "#6a6a6e", "#3a3a42"];

  let leds = "";
  for (let gy = 0; gy < ROWS; gy++) {
    for (let gx = 0; gx < COLS; gx++) {
      const dx = gx - ccx, dy = gy - ccy;
      const rho = Math.hypot(dx, dy);
      const x = r(GX0 + gx * CELL + (CELL - SIZE) / 2), y = r(GY0 + gy * CELL + (CELL - SIZE) / 2);
      // O buraco: no miolo, só LEDs apagados.
      if (rho < 1.6 || rho > RMAX + 2) {
        leds += `<rect x="${x}" y="${y}" width="${SIZE}" height="${SIZE}" rx="1"/>`;
        continue;
      }
      const th = Math.atan2(dy, dx);
      // Fase no redemoinho (0..1): ao longo dos braços ela é constante; anda com o raio (log) e o ângulo.
      let phase = (TWIST * Math.log(rho) - (ARMS * th) / (2 * Math.PI)) % 1;
      if (phase < 0) phase += 1;
      const p = Math.floor(phase * PHASES) % PHASES;
      const band = Math.min(BANDS.length - 1, Math.floor((rho / (RMAX + 2)) * BANDS.length));
      leds += `<rect class="p${p} b${band}" x="${x}" y="${y}" width="${SIZE}" height="${SIZE}" rx="1"/>`;
    }
  }

  let style = `
    /* O LED acende no tom da faixa dele quando o braço passa e vai apagando atrás. */
    .v rect[class] { animation: arm ${T}s linear infinite; }
    @keyframes arm { 0%, 10% { fill: var(--hi); } 26% { fill: var(--mid); } 44%, 100% { fill: #141418; } }`;
  // Atrasos: o pico anda para dentro com o tempo (o redemoinho puxa para o centro).
  for (let p = 0; p < PHASES; p++) style += `
    .v rect.p${p} { animation-delay: -${r((((PHASES - p) % PHASES) / PHASES) * T * 100) / 100}s; }`;
  BANDS.forEach((hi, b) => {
    style += `\n    .b${b} { --hi: ${hi}; --mid: ${b === 0 || b === BANDS.length - 1 ? "#1f1f24" : "#2e2e34"}; }`;
  });

  const body = `${panel(W, H)}
  <g class="v" fill="#141418">${leds}</g>`;
  write("panel-spiral", W, H, { label: "", body, ctx: new Map(), style, defs: "" });
}

// ======================================================================================
// Sobre mim (66%): o "Oi!", duas frases diretas e a formação.
// ======================================================================================
let ABOUT_H;
{
  const ctx = new Map();
  const W = 660, TW = W - PAD * 2;
  let y = 72;
  let body = head(ctx, W, y, "user-round", "Sobre mim");
  y += 62;
  body += `<g class="in" ${delay(0.1)}>${SERIF.text(ctx, "Oi!", PAD, y, 44)}</g>`;
  y += 46;
  // Curto de propósito: quem eu sou e o que fiz. A stack inteira está no painel de baixo.
  const intro = para(
    ctx,
    "Sou o Eduardo, dev full stack de Florianópolis. Passei dois anos na {UDESC} criando e mantendo sistemas internos em {PHP} e {JavaScript}, do banco de dados até a tela.",
    PAD,
    y + 6,
    18,
    TW,
    { lh: 1.55 },
  );
  body += `<g class="in" ${delay(0.2)}>${intro.svg}</g>`;
  y += 6 + intro.height + 30;
  let edu = BOLD.text(ctx, "Formação", PAD, y, 16.5);
  y += 14;
  for (const [name, meta] of [
    ["Tecnólogo em Análise e Desenvolvimento de Sistemas", "SESI SENAI · 2024 – 2026"],
    ["Técnico em Desenvolvimento de Sistemas", "SESI SENAI · concluído"],
    ["Curso.dev", "Filipe Deschamps · em andamento"],
  ]) {
    edu += `<path d="M${PAD} ${y} H${W - PAD}" stroke="${C.rule}" stroke-width="1.2"/>`;
    edu += SANS.text(ctx, name, PAD, y + 26, 15, { fill: C.text });
    edu += SANS.text(ctx, meta, W - PAD, y + 26, 13.5, { fill: C.mute, anchor: "end" });
    y += 40;
  }
  body += `<g class="in" ${delay(0.3)}>${edu}</g>`;
  const H = Math.round(y + 20);
  ABOUT_H = H;
  write("panel-about", W, H, {
    label: "Sobre mim. Oi! Sou o Eduardo, dev full stack de Florianópolis. Passei dois anos na UDESC criando e mantendo sistemas internos em PHP e JavaScript. Formação: Tecnólogo em ADS (SESI SENAI, 2024 a 2026), Técnico em Desenvolvimento de Sistemas (concluído), Curso.dev (em andamento).",
    body: panel(W, H) + body,
    ctx,
    style: IN + TWINKLE,
  });
}

// ======================================================================================
// Player + onda sonora (34%, ao lado do sobre). O player do Spotify cai lá de cima uma vez,
// quando a página abre, e aterrissa em cima da onda da música em LED, que dá um pico com o impacto.
// ======================================================================================
{
  const ctx = new Map();
  const W = 340, H = ABOUT_H;
  const SONG = { title: "Be Yourself", artist: "Audioslave", len: 273, at: 72 }; // 4:33, começa em 1:12
  const CAPA = embed("capa.jpg", "jpeg");
  const PW = 316, PH = 124, PX = 12, PY = 12;
  const BW = 168; // largura da barra de progresso
  const mmss = (t) => `${Math.floor(t / 60)}:${String(t % 60).padStart(2, "0")}`;

  // m:ss contando: cada dígito é uma fita vertical que sobe um número por vez, numa janelinha.
  const clock = () => {
    const x = 122, y = 93, size = 10, adv = MONO.width("0", size), step = 12;
    const tape = (cls, digits, cx) =>
      `<g clip-path="url(#clk)"><g class="${cls}">${digits.map((d, i) => MONO.text(ctx, String(d), cx, y + i * step, size, { fill: C.mute })).join("")}</g></g>`;
    return `<clipPath id="clk"><rect x="${x - 1}" y="${y - 9}" width="${r(adv * 4 + 2)}" height="11"/></clipPath>
      ${tape("dm", [0, 1, 2, 3, 4], x)}${MONO.text(ctx, ":", x + adv, y, size, { fill: C.mute })}${tape("dt", [0, 1, 2, 3, 4, 5], x + adv * 2)}${tape("du", [0, 1, 2, 3, 4, 5, 6, 7, 8, 9], x + adv * 3)}`;
  };
  const eq = [0, 1, 2, 3]
    .map((i) => `<rect class="eq" style="animation-duration:${(0.7 + i * 0.17).toFixed(2)}s;animation-delay:-${(i * 0.23).toFixed(2)}s" x="${PW - 34 + i * 6}" y="28" width="3.5" height="14" rx="1.5" fill="${C.text}"/>`)
    .join("");
  const player = `<rect width="${PW}" height="${PH}" rx="14" fill="${C.chip}" stroke="${C.line}" stroke-width="1.5"/>
    <clipPath id="capa"><rect x="14" y="16" width="92" height="92" rx="8"/></clipPath>
    <image href="${CAPA}" x="14" y="16" width="92" height="92" preserveAspectRatio="xMidYMid slice" clip-path="url(#capa)"/>
    ${SANS.text(ctx, SONG.title, 122, 42, 16)}
    ${SANS.text(ctx, SONG.artist, 122, 62, 13, { fill: C.mute })}
    ${eq}
    <rect x="122" y="74" width="${BW}" height="4" rx="2" fill="${C.line}"/>
    <rect class="prog" x="122" y="74" width="${BW}" height="4" rx="2" fill="${C.text}"/>
    <circle class="knob" cx="122" cy="76" r="5" fill="${C.text}"/>
    ${clock()}${MONO.text(ctx, mmss(SONG.len), 122 + BW, 93, 10, { fill: C.mute, anchor: "end" })}
    <g fill="${C.text}">
      <path d="M175 101 V113" stroke="${C.text}" stroke-width="2.2" stroke-linecap="round"/><path d="M187 101 L178 107 L187 113Z"/>
      <circle cx="206" cy="107" r="11"/><rect x="201.5" y="102" width="3" height="10" rx="1" fill="${C.chip}"/><rect x="207.5" y="102" width="3" height="10" rx="1" fill="${C.chip}"/>
      <path d="M237 101 V113" stroke="${C.text}" stroke-width="2.2" stroke-linecap="round"/><path d="M225 101 L234 107 L225 113Z"/>
    </g>`;

  // A onda: colunas de pixels espelhadas em volta de uma linha, andando para a esquerda sem emenda
  // (o desenho se repete duas vezes e a faixa anda exatamente uma largura).
  const top = PY + PH + 16, bottom = H - 16;
  const mid = (top + bottom) / 2;
  const CELL = 8, SIZE = 6;
  const maxRows = Math.floor((bottom - top) / 2 / CELL) - 1;
  const cols = 40;
  const cloud = noise2(44);
  const heights = Array.from({ length: cols }, (_, i) => {
    // Batidas: um envelope lento com picos rápidos, que fecha a volta no começo (sem emenda).
    const a = 0.5 + 0.5 * Math.sin((i / cols) * Math.PI * 2 * 3);
    const n = cloud(i * 0.7, 1.3);
    return Math.max(1, Math.round(maxRows * (0.15 + 0.85 * a * n)));
  });
  let wave = "";
  for (let copy = 0; copy < 2; copy++) {
    heights.forEach((h, i) => {
      const x = 12 + (copy * cols + i) * CELL;
      for (let k = 0; k < h; k++) {
        const tone = k >= h - 1 ? "#e9e9e4" : k >= h - 3 ? "#9a9a98" : "#55555a";
        wave += `<rect x="${x}" y="${r(mid - (k + 1) * CELL + 1)}" width="${SIZE}" height="${SIZE}" rx="1" fill="${tone}"/>`;
        wave += `<rect x="${x}" y="${r(mid + k * CELL + 1)}" width="${SIZE}" height="${SIZE}" rx="1" fill="${tone}" opacity=".55"/>`;
      }
    });
  }

  const FALL = { delay: 0.9, dur: 1.7 };
  const body = `${panel(W, H)}
  <g clip-path="url(#wc)"><g class="bump"><g class="wave">${wave}</g></g></g>
  <path d="M12 ${r(mid + 0.5)} H${W - 12}" stroke="${C.line}" stroke-width="1"/>
  <g clip-path="url(#pc)"><g transform="translate(${PX} ${PY})"><g class="fall">${player}</g></g></g>`;
  const style = `
    .wave { animation: wave 9s linear infinite; }
    @keyframes wave { from { transform: translateX(0); } to { transform: translateX(-${cols * CELL}px); } }
    /* O pico do impacto: a onda inteira estica na vertical e volta. */
    .bump { transform-origin: ${W / 2}px ${r(mid)}px; animation: bump ${FALL.dur}s ${FALL.delay}s both; }
    @keyframes bump { 0%, 46% { transform: scaleY(1); } 54% { transform: scaleY(1.55); } 70% { transform: scaleY(.85); } 86%, 100% { transform: scaleY(1); } }
    .eq { transform-box: fill-box; transform-origin: center bottom; animation-name: eq; animation-timing-function: ease-in-out; animation-iteration-count: infinite; animation-direction: alternate; }
    @keyframes eq { from { transform: scaleY(.25); } to { transform: scaleY(1); } }
    .prog { transform-box: fill-box; transform-origin: left center; animation: prog ${SONG.len}s linear -${SONG.at}s infinite; }
    @keyframes prog { from { transform: scaleX(0); } to { transform: scaleX(1); } }
    .knob { animation: knob ${SONG.len}s linear -${SONG.at}s infinite; }
    @keyframes knob { from { transform: translateX(0); } to { transform: translateX(${BW}px); } }
    .du { animation: du 10s steps(10, end) -${SONG.at % 10}s infinite; }
    @keyframes du { from { transform: translateY(0); } to { transform: translateY(-120px); } }
    .dt { animation: dt 60s steps(6, end) -${SONG.at % 60}s infinite; }
    @keyframes dt { from { transform: translateY(0); } to { transform: translateY(-72px); } }
    .dm { animation: dm ${SONG.len}s step-end -${SONG.at}s infinite; }
    @keyframes dm { ${[0, 1, 2, 3, 4].map((m) => `${r(((m * 60) / SONG.len) * 100)}% { transform: translateY(-${m * 12}px); }`).join(" ")} 100% { transform: translateY(-48px); } }
    /* A queda: entra por cima, afunda um pouco no impacto, quica e assenta. */
    .fall { animation: fall ${FALL.dur}s ${FALL.delay}s both; }
    @keyframes fall {
      0% { transform: translateY(-${PH + PY + 20}px); animation-timing-function: cubic-bezier(.5,0,.9,.5); }
      50% { transform: translateY(14px); animation-timing-function: cubic-bezier(.3,.5,.5,1); }
      72% { transform: translateY(-8px); animation-timing-function: ease-in-out; }
      100% { transform: translateY(0); } }`;
  write("panel-music", W, H, {
    label: `Tocando agora: ${SONG.title}, de ${SONG.artist}.`,
    body,
    ctx,
    defs: clipPanel("pc", W, H) + `<clipPath id="wc"><rect x="12" y="${top}" width="${W - 24}" height="${bottom - top}"/></clipPath>`,
    style,
  });
}

// ======================================================================================
// Stack (100%): um céu de constelações. Cada tecnologia é uma estrela de pixel com o ícone e o
// nome ao lado; as estrelas de um grupo se ligam por linhas finas (desenhadas quando o painel
// aparece) e o nome do grupo fica embaixo. As estrelas piscam devagar, cada uma no seu ritmo.
// ======================================================================================
{
  const ctx = new Map();
  const W = 1000, H = 470;
  // [nome, ícone, x, y, lado do rótulo]
  const groups = [
    {
      label: "front-end",
      cx: 185,
      stars: [["JavaScript", "javascript", 100, 172, "r"], ["React", "react", 245, 150, "r"], ["CSS", "css", 205, 262, "r"], ["HTML", "html", 88, 300, "r"], ["Tailwind", "tailwind", 268, 362, "r"]],
      edges: [[0, 1], [0, 3], [3, 2], [2, 1], [2, 4]],
    },
    {
      label: "back-end",
      cx: 460,
      stars: [["PHP", "php", 436, 176, "r"], ["Node.js", "nodejs", 392, 300, "r"], ["Java", "java", 528, 248, "r"]],
      edges: [[0, 1], [0, 2], [1, 2]],
    },
    {
      label: "banco",
      cx: 676,
      stars: [["SQL", "sql", 640, 206, "r"], ["MySQL", "sql", 700, 328, "r"]],
      edges: [[0, 1]],
    },
    {
      label: "ferramentas",
      cx: 872,
      stars: [["Git", "github", 830, 166, "r"], ["Trello", "trello", 912, 258, "l"], ["Jira", "jira", 842, 350, "r"]],
      edges: [[0, 1], [1, 2]],
    },
  ];

  let body = head(ctx, W, 72, "code-xml", "Stack");

  // O céu: poeirinha de estrelas apagadas, algumas piscando.
  const rand = rng(77);
  let sky = "";
  for (let i = 0; i < 110; i++) {
    const x = 20 + rand() * (W - 40), y = 100 + rand() * (H - 130);
    const s = rand() < 0.15 ? 3 : 2;
    const cls = rand() < 0.3 ? ` class="t${1 + Math.floor(rand() * 4)}"` : "";
    sky += `<rect x="${r(x)}" y="${r(y)}" width="${s}" height="${s}" fill="${TONES[1 + Math.floor(rand() * 3)]}"${cls}/>`;
  }
  body += sky;

  let lines = "";
  let stars = "";
  let style = "";
  let n = 0;
  groups.forEach((g, gi) => {
    g.edges.forEach(([a, b], ei) => {
      const [, , x1, y1] = g.stars[a];
      const [, , x2, y2] = g.stars[b];
      // A linha para um pouco antes de cada estrela, para não encostar no brilho.
      const len = Math.hypot(x2 - x1, y2 - y1), ux = (x2 - x1) / len, uy = (y2 - y1) / len, gap = 14;
      lines += `<path class="ln" pathLength="1" d="M${r(x1 + ux * gap)} ${r(y1 + uy * gap)} L${r(x2 - ux * gap)} ${r(y2 - uy * gap)}" stroke="${C.strong}" stroke-width="1.2" style="animation-delay:${(0.3 + gi * 0.25 + ei * 0.12).toFixed(2)}s"/>`;
    });
    g.stars.forEach(([name, icon, x, y, side], si) => {
      // A estrela: um pixel claro no meio, quatro braços mais apagados e um brilho bem leve em volta.
      const star = `<circle cx="${x}" cy="${y}" r="11" fill="#ffffff" opacity=".06"/>
        <g class="tw${n % 5}"><rect x="${x - 2}" y="${y - 9}" width="4" height="4" fill="${TONES[3]}"/><rect x="${x - 2}" y="${y + 5}" width="4" height="4" fill="${TONES[3]}"/><rect x="${x - 9}" y="${y - 2}" width="4" height="4" fill="${TONES[3]}"/><rect x="${x + 5}" y="${y - 2}" width="4" height="4" fill="${TONES[3]}"/></g>
        <rect x="${x - 3}" y="${y - 3}" width="6" height="6" fill="${C.text}"/>`;
      // O rótulo: ícone e nome, à direita da estrela (ou à esquerda, perto da borda).
      const nameW = SANS.width(name, 15);
      const lx = side === "r" ? x + 18 : x - 18 - 16 - 7 - nameW;
      // Um fundo da cor do céu atrás do rótulo: as linhas passam por trás do nome, não por cima.
      const label =
        `<rect x="${r(lx - 5)}" y="${y - 13}" width="${r(nameW + 33)}" height="26" rx="6" fill="${C.col}"/>` +
        brand(icon, lx, y - 8, 16, C.dim) +
        SANS.text(ctx, name, lx + 23, y + 5.5, 15, { fill: C.text });
      stars += `<g class="in" style="animation-delay:${(0.15 + gi * 0.25 + si * 0.08).toFixed(2)}s">${star}${label}</g>`;
      n++;
    });
    stars += MONO.text(ctx, g.label, g.cx, H - 34, 13, { fill: C.mute, anchor: "middle" });
  });
  body += `<g fill="none">${lines}</g>${stars}`;

  style += `
    .ln { stroke-dasharray: 1 1; stroke-dashoffset: 1; animation: ln 1.2s ${EASE} both; }
    @keyframes ln { to { stroke-dashoffset: 0; } }
    .tw0 { animation: tw 3.1s ease-in-out infinite; }
    .tw1 { animation: tw 4.3s ease-in-out .8s infinite; }
    .tw2 { animation: tw 2.7s ease-in-out 1.6s infinite; }
    .tw3 { animation: tw 5.2s ease-in-out .4s infinite; }
    .tw4 { animation: tw 3.8s ease-in-out 2.2s infinite; }`;
  write("panel-stack", W, H, {
    label: "Stack em constelações. Front-end: JavaScript, React, HTML, CSS, Tailwind. Back-end: PHP, Node.js, Java. Banco: SQL, MySQL. Ferramentas: Git, Trello, Jira.",
    body: panel(W, H) + body,
    ctx,
    style: IN + TWINKLE + style,
  });
}

// ======================================================================================
// Contato (66%, à direita do redemoinho): a frase à esquerda e a Kiara sentada na borda de baixo, à
// direita (os links ficam logo embaixo).
// ======================================================================================
{
  const ctx = new Map();
  const W = 660, H = CONTACT_H;
  const TX = PAD;
  let body = head(ctx, W, 72, "mail", "Contato");
  body += `<g class="in" ${delay(0.1)}>`;
  body += BOLD.text(ctx, "Tem um problema", TX, 170, 31);
  body += BOLD.text(ctx, "chato?", TX, 210, 31);
  body += SERIF.text(ctx, "Me manda um e-mail.", TX, 262, 40, { fill: C.dim });
  body += "</g>";
  // A borda de baixo, mais forte: é o chão em que ela senta.
  body += `<path d="M20 ${H - 1} H${W - 20}" stroke="${C.strong}" stroke-width="1.5"/>`;
  // A imagem tem ~2% de folga transparente embaixo: desce um pouco para as patas tocarem a borda.
  const KW = 190, KH = Math.round((KW * 475) / 380);
  const ky = H - 1 - KH + Math.round(KH * 0.02);
  body += `<g clip-path="url(#cc)"><image class="in" href="${embed("kiara.webp", "webp")}" x="${W - PAD - KW}" y="${ky}" width="${KW}" height="${KH}" style="animation-delay:.3s;filter:brightness(.94)"/></g>`;
  write("panel-contact", W, H, {
    label: "Contato: tem um problema chato? Me manda um e-mail. (A Kiara, minha gata, sentada na borda.)",
    body: panel(W, H) + body,
    ctx,
    defs: clipPanel("cc", W, H),
    style: IN + TWINKLE,
  });
}

// ---------- os três links, logo abaixo do contato ----------
function linkCard(name, { title, sub, icon }) {
  const ctx = new Map();
  const LW = 333, H = 92;
  let body = `<rect x="1" y="1" width="${LW - 2}" height="${H - 2}" rx="16" fill="${C.col}" stroke="${C.border}" stroke-width="1.5"/>`;
  body += `<rect x="22" y="${H / 2 - 21}" width="42" height="42" rx="11" fill="${C.chip}"/>`;
  body += icon.lucide ? lucide(icon.lucide, 32, H / 2 - 11, 22, C.text, 1.7) : brand(icon.brand, 32, H / 2 - 11, 22, C.text);
  const subTop = sub.length > 1 ? H / 2 + 12 : H / 2 + 18;
  body += BOLD.text(ctx, title, 80, sub.length > 1 ? H / 2 - 10 : H / 2 - 4, 18);
  sub.forEach((line, i) => {
    body += SANS.text(ctx, line, 80, subTop + i * 17, 13.5, { fill: C.mute });
  });
  body += lucide("arrow-up-right", LW - 42, H / 2 - 9, 18, C.mute, 1.6);
  const out = `<svg xmlns="http://www.w3.org/2000/svg" width="${LW}" height="${H}" viewBox="0 0 ${LW} ${H}" role="img" aria-label="${esc(`${title}: ${sub.join("")}`)}">
  <defs>${[...ctx].map(([id, d]) => `<path id="${id}" d="${d}"/>`).join("")}</defs>
${body}
</svg>
`;
  fs.writeFileSync(path.join(OUT, `${name}.svg`), out);
  console.log(`${name}.svg  ${(out.length / 1024).toFixed(1)} KB`);
}
linkCard("link-portfolio", { title: "Portfólio", sub: ["portfolio-xi-orcin-59.vercel.app"], icon: { lucide: "globe" } });
linkCard("link-linkedin", { title: "LinkedIn", sub: ["in/eduardo-teixeira-virissimo"], icon: { brand: "linkedin" } });
linkCard("link-email", { title: "E-mail", sub: ["eduardoteixeiravirissimo", "@gmail.com"], icon: { lucide: "mail" } });

// ======================================================================================
// Rodapé: o ano e o nome em letra de mão, e os pixels subindo do fundo.
// ======================================================================================
{
  const ctx = new Map();
  const W = 1000, H = 210;
  const strip = pixelStrip({ id: "pf", w: W, rows: 11, up: true, seed: 5, height: H });
  let body = `${panel(W, H)}<g clip-path="url(#fc)">${strip.svg}</g>`;
  body += SANS.text(ctx, "© 2026", PAD, 58, 16, { fill: C.mute });
  const sx = PAD + 70;
  body += `<g transform="rotate(-4 ${sx} 50)">${HAND.text(ctx, "Eduardo Viríssimo", sx, 62, 38, { fill: C.dim })}</g>`;
  body += MONO.text(ctx, "trying to be better", W - PAD, 58, 14, { fill: C.mute, anchor: "end" });
  write("panel-footer", W, H, {
    label: "© 2026 Eduardo Viríssimo. trying to be better",
    body,
    ctx,
    defs: clipPanel("fc", W, H) + strip.defs,
    style: strip.style,
  });
}
