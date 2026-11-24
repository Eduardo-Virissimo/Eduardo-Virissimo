// Gera os painéis SVG do README.
// Vibe do README antigo (preto e branco, traço surreal, árvore monoespaçada) num layout de painéis.
// Texto em Geist / Geist Mono já convertido em contorno (scripts/glyphs-*.json), então renderiza
// igual em qualquer máquina.
//
//   node scripts/gen.mjs [pasta_de_saida]
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const HERE = path.dirname(fileURLToPath(import.meta.url));
const OUT = process.argv[2] || path.join(HERE, "..", "assets");
fs.mkdirSync(OUT, { recursive: true });

const INK = "#0b0b0b", PAPER = "#f2f2f0", MUTE = "#8a8a86", LINE = "#2a2a2e", EDGE = "#d6d6d2";
const EASE = "cubic-bezier(.16,1,.3,1)";
const r = (v) => (Math.round(v * 10) / 10).toString();

class Font {
  constructor(name) {
    const d = JSON.parse(fs.readFileSync(path.join(HERE, `glyphs-${name}.json`), "utf8"));
    Object.assign(this, { name, upm: d.upm, g: d.glyphs });
  }
  width(s, size, tr = 0) {
    return [...s].reduce((a, c) => a + this.glyph(c).adv, 0) * size / this.upm + tr * (s.length - 1);
  }
  glyph(c) {
    const g = this.g[c];
    if (!g) throw new Error(`sem glifo para "${c}" em ${this.name}`);
    return g;
  }
  // y é a linha de base
  text(ctx, s, x, y, size, { fill = PAPER, tr = 0, anchor = "start" } = {}) {
    const k = size / this.upm;
    if (anchor === "end") x -= this.width(s, size, tr);
    if (anchor === "middle") x -= this.width(s, size, tr) / 2;
    let cx = 0, uses = "";
    for (const c of s) {
      const g = this.glyph(c);
      if (g.d) {
        const id = this.name[0] + c.codePointAt(0).toString(16);
        ctx.set(id, g.d);
        uses += `<use href="#${id}" x="${r(cx)}"/>`;
      }
      cx += g.adv + tr / k;
    }
    return `<g fill="${fill}" transform="translate(${r(x)} ${r(y)}) scale(${k.toFixed(5)} ${(-k).toFixed(5)})">${uses}</g>`;
  }
}
const SANS = new Font("sans"), MONO = new Font("mono");

function write(name, w, h, { label, body, style = "", defs = "", ctx }) {
  const glyphs = [...ctx].map(([id, d]) => `<path id="${id}" d="${d}"/>`).join("");
  const out = `<svg xmlns="http://www.w3.org/2000/svg" width="${w}" height="${h}" viewBox="0 0 ${w} ${h}" role="img" aria-label="${label}">
  <defs>${glyphs}${defs}</defs>
  <style>${style}
    @media (prefers-reduced-motion: reduce) { * { animation:none !important; } }
  </style>
${body}
</svg>
`;
  fs.writeFileSync(path.join(OUT, `${name}.svg`), out);
  console.log(`${name}.svg  ${(out.length / 1024).toFixed(1)} KB`);
}

const panel = (w, h, fill = INK) =>
  `<rect x="6" y="6" width="${w - 12}" height="${h - 12}" rx="16" fill="${fill}" stroke="${fill === INK ? LINE : EDGE}" stroke-width="1.5"/>`;
const clip = (id, w, h) => `<clipPath id="${id}"><rect x="6" y="6" width="${w - 12}" height="${h - 12}" rx="16"/></clipPath>`;
// painel em forma de janela: barra com três bolinhas e o nome do "arquivo" no meio
const win = (ctx, w, h, title) => `${panel(w, h)}
  <path d="M6 52 H${w - 6}" stroke="${LINE}" stroke-width="1.5"/>
  <g fill="none" stroke="${MUTE}" stroke-width="1.5"><circle cx="34" cy="29" r="5.5"/><circle cx="54" cy="29" r="5.5"/><circle cx="74" cy="29" r="5.5"/></g>
  ${MONO.text(ctx, title, w / 2, 34, 13, { fill: MUTE, anchor: "middle" })}`;

// entrada: sobe e aparece uma vez; o estado final é o estado de base (sem animação continua visível)
const IN = `
    .in { animation:in .9s ${EASE} backwards; }
    @keyframes in { from { opacity:0; transform:translateY(14px); } }`;
const delay = (s) => `style="animation-delay:${s}s"`;

// espiral quadrada de cantos arredondados (o logo do portfólio), em 0..100
const LOGO = "M10 10 L83 10 Q90 10 90 17 L90 83 Q90 90 83 90 L17 90 Q10 90 10 83 L10 32 Q10 25 17 25 " +
  "L68 25 Q75 25 75 32 L75 68 Q75 75 68 75 L32 75 Q25 75 25 68 L25 47 Q25 40 32 40 L53 40 " +
  "Q60 40 60 47 L60 53 Q60 60 53 60 L40 60";

// ---------- player de música ----------
// Entra uma vez quando a página abre: cai lá de cima passando por cima do perfil.md (que espreme) e
// aterrissa no lugar do grafo de git, esmagando o grafo pra baixo. O hero e o grafo são imagens
// separadas, então cada uma desenha a sua parte da queda com o mesmo tempo.
// Sem animação (prefers-reduced-motion) fica direto o estado final.
const SONG = { title: "Be Yourself", artist: "Audioslave", len: 273, at: 72 };   // 4:33, começa em 1:12
// capa do álbum já reduzida (scripts/capa.jpg), embutida no SVG: imagem dentro de <img> não carrega arquivo externo
const CAPA = "data:image/jpeg;base64," + fs.readFileSync(path.join(HERE, "capa.jpg")).toString("base64");
const PW = 328, PH = 124;                   // tamanho do player
const PX = 666, PY = 376;                   // onde ele termina, em coordenadas da página (1000 de largura)
// hit: o player encosta no grafo; land: termina de espremer; dur: fim do quique (segundos)
const FALL = { delay: 0.9, from: -150, hit: 0.85, land: 1.4, dur: 1.72 };
// O hero e o grafo carregam em momentos um pouco diferentes no GitHub (até ~100ms). A passagem de uma
// imagem pra outra acontece enquanto o player espreme o grafo, que é a parte lenta da queda, então
// essa diferença vira no máximo um desalinhamento pequeno em vez do player sumir por um instante.
const GIT_Y = 370, HIT_Y = GIT_Y - PH;      // topo do grafo na página; y do player quando encosta nele
const BOUNCE = 8;
const fp = (t) => r((t / FALL.dur) * 100);
const IMPACT = "cubic-bezier(.5,0,.9,.5)", PRESS = "cubic-bezier(.3,.5,.5,1)", SOFT = "ease-in-out";
// queda em coordenadas da página; a imagem subtrai o próprio deslocamento vertical
const fallKeys = (oy) => {
  const y = (v) => `translateY(${r(v - oy)}px)`;
  return `0% { transform:${y(FALL.from)}; animation-timing-function:${IMPACT}; }
      ${fp(FALL.hit)}% { transform:${y(HIT_Y)}; animation-timing-function:${PRESS}; }
      ${fp(FALL.land)}% { transform:${y(PY)}; animation-timing-function:${SOFT}; }
      ${fp(FALL.land + 0.15)}% { transform:${y(PY - BOUNCE)}; animation-timing-function:${SOFT}; }
      100% { transform:${y(PY)}; }`;
};
const mmss = (t) => `${Math.floor(t / 60)}:${String(t % 60).padStart(2, "0")}`;
// m:ss contando: cada dígito é uma fita vertical que sobe um número por vez, recortada numa janelinha
function clock(ctx) {
  const x = 122, y = 93, size = 10, adv = MONO.width("0", size), step = 12;
  const tape = (cls, digits, cx) => `<g clip-path="url(#clk)"><g class="${cls}">${digits.map((d, i) => MONO.text(ctx, String(d), cx, y + i * step, size, { fill: MUTE })).join("")}</g></g>`;
  return `<clipPath id="clk"><rect x="${x - 1}" y="${y - 9}" width="${r(adv * 4 + 2)}" height="11"/></clipPath>
    ${tape("dm", [0, 1, 2, 3, 4], x)}${MONO.text(ctx, ":", x + adv, y, size, { fill: MUTE })}${tape("dt", [0, 1, 2, 3, 4, 5], x + adv * 2)}${tape("du", [0, 1, 2, 3, 4, 5, 6, 7, 8, 9], x + adv * 3)}`;
}
function player(ctx) {
  const tSize = Math.min(16, 16 * 170 / SANS.width(SONG.title, 16));
  const eq = [0, 1, 2, 3].map((i) => `<rect class="eq" style="animation-duration:${(0.7 + i * 0.17).toFixed(2)}s;animation-delay:-${(i * 0.23).toFixed(2)}s" x="${294 + i * 6}" y="28" width="3.5" height="14" rx="1.5" fill="${PAPER}"/>`).join("");
  return `<rect width="${PW}" height="${PH}" rx="14" fill="${INK}" stroke="${LINE}" stroke-width="1.5"/>
    <clipPath id="capa"><rect x="14" y="16" width="92" height="92" rx="8"/></clipPath>
    <image href="${CAPA}" x="14" y="16" width="92" height="92" preserveAspectRatio="xMidYMid slice" clip-path="url(#capa)"/>
    ${SANS.text(ctx, SONG.title, 122, 42, tSize)}
    ${SANS.text(ctx, SONG.artist, 122, 62, 13, { fill: MUTE })}
    ${eq}
    <rect x="122" y="74" width="192" height="4" rx="2" fill="#2a2a2e"/>
    <rect class="prog" x="122" y="74" width="192" height="4" rx="2" fill="${PAPER}"/>
    <circle class="knob" cx="122" cy="76" r="5" fill="${PAPER}"/>
    ${clock(ctx)}${MONO.text(ctx, mmss(SONG.len), 314, 93, 10, { fill: MUTE, anchor: "end" })}
    <g fill="${PAPER}">
      <path d="M181 101 V113" stroke="${PAPER}" stroke-width="2.2" stroke-linecap="round"/><path d="M193 101 L184 107 L193 113Z"/>
      <circle cx="218" cy="107" r="11"/><rect x="213.5" y="102" width="3" height="10" rx="1" fill="${INK}"/><rect x="219.5" y="102" width="3" height="10" rx="1" fill="${INK}"/>
      <path d="M255 101 V113" stroke="${PAPER}" stroke-width="2.2" stroke-linecap="round"/><path d="M243 101 L252 107 L243 113Z"/>
    </g>`;
}
const PLAYER_STYLE = `
    .eq    { transform-box:fill-box; transform-origin:center bottom; animation-name:eq; animation-timing-function:ease-in-out; animation-iteration-count:infinite; animation-direction:alternate; }
    .prog  { transform-box:fill-box; transform-origin:left center; transform:scaleX(${r((SONG.at / SONG.len) * 1000) / 1000}); animation:prog ${SONG.len}s linear -${SONG.at}s infinite; }
    .knob  { transform:translateX(${r((SONG.at / SONG.len) * 192)}px); animation:knob ${SONG.len}s linear -${SONG.at}s infinite; }
    .du    { transform:translateY(-${(SONG.at % 10) * 12}px); animation:du 10s steps(10, end) -${SONG.at % 10}s infinite; }
    .dt    { transform:translateY(-${Math.floor((SONG.at % 60) / 10) * 12}px); animation:dt 60s steps(6, end) -${SONG.at % 60}s infinite; }
    .dm    { transform:translateY(-${Math.floor(SONG.at / 60) * 12}px); animation:dm ${SONG.len}s step-end -${SONG.at}s infinite; }
    @keyframes eq   { from { transform:scaleY(.25); } to { transform:scaleY(1); } }
    @keyframes prog { from { transform:scaleX(0); } to { transform:scaleX(1); } }
    @keyframes knob { from { transform:translateX(0); } to { transform:translateX(192px); } }
    @keyframes du   { from { transform:translateY(0); } to { transform:translateY(-120px); } }
    @keyframes dt   { from { transform:translateY(0); } to { transform:translateY(-72px); } }
    @keyframes dm   { ${[0, 1, 2, 3, 4].map((m) => `${r((m * 60 / SONG.len) * 100)}% { transform:translateY(-${m * 12}px); }`).join(" ")} 100% { transform:translateY(-48px); } }`;
const fallAnim = (cls, oy) => `
    .${cls} { animation:${cls} ${FALL.dur}s ${FALL.delay}s both; }
    @keyframes ${cls} { ${fallKeys(oy)} }`;

// ---------- hero ----------
{
  // perfil.md: o código-fonte é digitado (cursor acompanhando), some, e entra a versão renderizada.
  // Sem animação (prefers-reduced-motion), fica só a versão renderizada.
  const ctx = new Map(), W = 1000, H = 370, D = 15, size = 20, x0 = 76;
  const pct = (t) => r((t / D) * 100);
  const SOFT = "#c9c9c4";
  const src = [
    [["# ", MUTE], ["Eduardo", PAPER]],
    [["**", MUTE], ["dev. full stack", PAPER], ["**", MUTE]],
    [],
    [["Formado em Análise e Desenvolvimento de Sistemas", SOFT]],
  ];
  const ys = [140, 182, 224, 266];
  let t = 0.4;
  const timing = src.map((toks) => {
    const n = toks.map((x) => x[0]).join("").length, s = t, e = t + 0.018 * n + 0.15;
    t = e + 0.15;
    return [s, e, n];
  });
  const SWAP = t + 0.5;                       // fim da digitação + pausa: troca pro preview
  const OUT = D - 1;                          // começa a sumir pra recomeçar o loop

  let code = "", carets = "", nums = "", style = `${IN}
    .src { opacity:0; animation:src ${D}s linear infinite; }
    @keyframes src { 0%,${pct(SWAP)}% { opacity:1; } ${pct(SWAP + 0.4)}%,100% { opacity:0; } }
    .blink { animation:blink 1.1s steps(1) infinite; }
    @keyframes blink { 50% { opacity:0; } }`;
  src.forEach((toks, i) => {
    const y = ys[i], [s, e, n] = timing[i], last = i === src.length - 1;
    let x = x0;
    for (const [tx, c] of toks) { code += MONO.text(ctx, tx, x, y, size, { fill: c }); x += MONO.width(tx, size); }
    const w = x - x0, next = last ? pct(SWAP) : pct(timing[i + 1][0]);
    nums += MONO.text(ctx, String(i + 1), 52, y, 13, { fill: "#4a4a48", anchor: "end" });
    carets += `\n      <g class="cv${i}">${w ? `<rect x="${r(x - 0.5)}" y="${y - 22}" width="${r(w + 30)}" height="30" fill="${INK}"/>` : ""}` +
      `<g class="cu${i}"><rect${last ? ' class="blink"' : ""} x="${r(x + 3)}" y="${y - 17}" width="11" height="22" fill="${PAPER}"/></g></g>`;
    style += `
    .cv${i} { animation:cv${i} ${D}s infinite; }
    @keyframes cv${i} { 0%,${pct(s)}% { transform:translateX(-${r(w)}px); animation-timing-function:steps(${Math.max(n, 1)}, end); } ${pct(e)}%,100% { transform:translateX(0); } }
    .cu${i} { opacity:0; animation:cu${i} ${D}s step-end infinite; }
    @keyframes cu${i} { 0% { opacity:0; } ${pct(s)}% { opacity:1; } ${next}% { opacity:0; } 100% { opacity:0; } }`;
  });

  // versão renderizada: entra em sequência depois da troca
  const outs = [
    SANS.text(ctx, "Eduardo", 40, 206, 136, { tr: -5 }),
    MONO.text(ctx, "dev. full stack", 48, 256, 24),
    SANS.text(ctx, "Formado em Análise e Desenvolvimento de Sistemas", 48, 306, 19, { fill: SOFT }),
  ];
  const rendered = outs.map((g, i) => `<g class="o${i}">${g}</g>`).join("\n  ");
  outs.forEach((_, i) => {
    const a = SWAP + 0.3 + i * 0.15;
    style += `
    .o${i} { animation:o${i} ${D}s ${EASE} infinite; }
    @keyframes o${i} { 0%,${pct(a)}% { opacity:0; transform:translateY(16px); } ${pct(a + 0.8)}%,${pct(OUT)}% { opacity:1; transform:translateY(0); } ${pct(OUT + 0.5)}%,100% { opacity:0; transform:translateY(0); } }`;
  });

  // chave "md / preview" na barra da janela, trocando junto
  const mdW = MONO.width("md", 12), pvW = MONO.width("preview", 12);
  const pvX = W - 40 - pvW, mdX = pvX - 22 - mdW;
  style += `
    .pill { animation:pill ${D}s ${EASE} infinite; }
    @keyframes pill { 0%,${pct(SWAP)}% { transform:translateX(${r(mdX - pvX)}px); width:${r(mdW + 18)}px; } ${pct(SWAP + 0.5)}%,100% { transform:translateX(0); width:${r(pvW + 18)}px; } }`;
  const toggle = `<rect class="pill" x="${r(pvX - 9)}" y="18" width="${r(pvW + 18)}" height="22" rx="11" fill="none" stroke="${MUTE}" stroke-width="1.2"/>
  ${MONO.text(ctx, "md", mdX, 33, 12, { fill: MUTE })}${MONO.text(ctx, "preview", pvX, 33, 12, { fill: MUTE })}`;

  const body = `  ${win(ctx, W, H, "perfil.md")}
  ${toggle}
  <g class="src" clip-path="url(#pc)">
    ${nums}
    ${code}${carets}
  </g>
  ${rendered}`;
  const heroBody = `  <g class="squish">${body}</g>
  <g transform="translate(${PX} 0)"><g class="fallh" style="transform:translateY(${H + 40}px)">${player(ctx)}</g></g>`;
  const heroStyle = style + PLAYER_STYLE + fallAnim("fallh", 0) + `
    .squish { transform-origin:${W / 2}px ${H / 2}px; animation:squish ${FALL.dur}s ${FALL.delay}s both; }
    @keyframes squish { 0%,${fp(0.33)}% { transform:scale(1,1); } ${fp(0.57)}% { transform:scale(.99,.955); } ${fp(0.75)}% { transform:scale(1.004,1.012); } ${fp(0.9)}% { transform:scale(.999,.996); } ${fp(1.02)}%,100% { transform:scale(1,1); } }`;
  write("panel-hero", W, H, {
    label: "Eduardo. dev. full stack. Formado em Análise e Desenvolvimento de Sistemas.", body: heroBody, style: heroStyle, ctx,
    defs: `<clipPath id="pc"><rect x="20" y="60" width="${W - 40}" height="${H - 72}"/></clipPath>`,
  });
}

// ---------- sobre ----------
{
  // janela de editor: um objeto "eduardo" digitado linha a linha uma vez só, e fica pra ser lido
  const ctx = new Map(), W = 660, H = 300, size = 15.5, lh = 28, x0 = 76, y0 = 98;
  const K = MUTE, S = "#c9c9c4", P = PAPER;                     // palavra-chave/pontuação, string, chave
  const lines = [
    [["const ", K], ["eduardo", P], [" = {", K]],
    [["  codandoDesde", P], [": ", K], ["2021", S], [",", K]],
    [["  maisUsa", P], [": ", K], ['"TypeScript"', S], [",", K]],
    [["  estudando", P], [": [", K], ['"React"', S], [", ", K], ['"Node.js"', S], [", ", K], ['"PHP"', S], ["],", K]],
    [["  foco", P], [": ", K], ['"do banco de dados à interface"', S], [",", K]],
    [["  contato", P], [": ", K], ['"tem um problema chato? me chama no LinkedIn"', S], [",", K]],
    [["};", K]],
  ];
  // Cada linha tem uma "capa" da cor do fundo que anda junto com o cursor, um caractere por vez,
  // escondendo o que ainda não foi digitado. O cursor só aparece na linha que está sendo digitada.
  const timing = [];
  let t = 0.5;
  for (const toks of lines) {
    const n = toks.map((x) => x[0]).join("").length, e = t + 0.018 * n + 0.12;
    timing.push([t, e, n]);
    t = e + 0.15;
  }
  const D = +r(t), pct = (t) => r((t / D) * 100);   // a animação toda dura só a digitação
  let body = `  ${win(ctx, W, H, "sobre.ts")}`, code = "", carets = "";
  let style = `
    .blink { animation:blink 1.1s steps(1) infinite; }
    @keyframes blink { 50% { opacity:0; } }`;
  lines.forEach((toks, i) => {
    const y = y0 + i * lh, [s, e, n] = timing[i], last = i === lines.length - 1;
    let x = x0;
    for (const [tx, c] of toks) { code += MONO.text(ctx, tx, x, y, size, { fill: c }); x += MONO.width(tx, size); }
    const w = x - x0, next = last ? 100 : pct(timing[i + 1][0]);
    body += `\n  ${MONO.text(ctx, String(i + 1), 50, y, 12, { fill: "#4a4a48", anchor: "end" })}`;
    carets += `\n    <g class="cv${i}"><rect x="${r(x - 0.5)}" y="${y - 18}" width="${r(w + 24)}" height="25" fill="${INK}"/>` +
      `<g class="cu${i}"><rect${last ? ' class="blink"' : ""} x="${r(x + 3)}" y="${y - 14}" width="9" height="18" fill="${PAPER}"/></g></g>`;
    style += `
    .cv${i} { animation:cv${i} ${D}s both; }
    @keyframes cv${i} { 0%,${pct(s)}% { transform:translateX(-${r(w)}px); animation-timing-function:steps(${n}, end); } ${pct(e)}%,100% { transform:translateX(0); } }
    .cu${i} { opacity:${last ? 1 : 0}; animation:cu${i} ${D}s step-end both; }
    @keyframes cu${i} { 0% { opacity:0; } ${pct(s)}% { opacity:1; } ${next}% { opacity:${last ? 1 : 0}; } 100% { opacity:${last ? 1 : 0}; } }`;
  });
  body += `\n  <g class="code" clip-path="url(#ac)">${code}${carets}\n  </g>`;
  write("panel-about", W, H, {
    label: "Sobre: programando desde 2021, mais usa TypeScript, estudando React, Node.js e PHP. Foco: do banco de dados à interface. Tem um problema chato? Me chama no LinkedIn.",
    body, style, ctx,
    defs: `<clipPath id="ac"><rect x="${x0 - 4}" y="60" width="${W - x0 - 4}" height="${H - 70}"/></clipPath>`,
  });
}

// ---------- grafo de git (papel) ----------
{
  // main com duas branches saindo e voltando em merge, desenhado commit a commit, em loop
  const ctx = new Map(), W = 340, H = 300, D = 9;
  const pct = (t) => r((t / D) * 100);
  const ink = `fill="none" stroke="${INK}" stroke-width="3" stroke-linecap="round"`;
  const lines = [
    ["M40 150 H300", 0.3, 3.4],
    ["M90 150 C116 150 114 96 140 96 H196 C222 96 222 150 248 150", 1.0, 3.0],
    ["M150 150 C176 150 174 206 200 206 H244 C266 206 268 150 292 150", 1.7, 3.6],
  ];
  const commits = [[40, 150, 0.3], [90, 150, 0.9], [150, 150, 1.5], [140, 96, 1.4], [196, 96, 2.1], [200, 206, 2.2], [244, 206, 2.9], [248, 150, 3.1], [292, 150, 3.7]];
  const R = 16, L = 6, Rt = W - 6, B = H - 6, MID = B - R - (L + R);   // MID: altura do meio esticável
  const edge = `stroke="${EDGE}" stroke-width="1.5" fill="none"`;
  const shell = `<g class="gtop">
    <path d="M${L} ${L + R + 1} V${L + R} A${R} ${R} 0 0 1 ${L + R} ${L} H${Rt - R} A${R} ${R} 0 0 1 ${Rt} ${L + R} V${L + R + 1} Z" fill="${PAPER}"/>
    <path d="M${L} ${L + R + 0.5} V${L + R} A${R} ${R} 0 0 1 ${L + R} ${L} H${Rt - R} A${R} ${R} 0 0 1 ${Rt} ${L + R} V${L + R + 0.5}" ${edge}/>
  </g>
  <g class="gmid">
    <rect x="${L}" y="${L + R}" width="${Rt - L}" height="${MID}" fill="${PAPER}"/>
    <path d="M${L} ${L + R} V${B - R} M${Rt} ${L + R} V${B - R}" ${edge} vector-effect="non-scaling-stroke"/>
  </g>
  <path d="M${L} ${B - R - 1} V${B - R} A${R} ${R} 0 0 0 ${L + R} ${B} H${Rt - R} A${R} ${R} 0 0 0 ${Rt} ${B - R} V${B - R - 1} Z" fill="${PAPER}"/>
  <path d="M${L} ${B - R - 0.5} V${B - R} A${R} ${R} 0 0 0 ${L + R} ${B} H${Rt - R} A${R} ${R} 0 0 0 ${Rt} ${B - R} V${B - R - 0.5}" ${edge}/>`;
  let style = "", body = `  ${shell}\n  <g class="ggr"><g class="all">`;
  lines.forEach(([d, s, e], i) => {
    body += `\n    <path class="g${i}" pathLength="1" d="${d}" ${ink}/>`;
    style += `
    .g${i} { stroke-dasharray:1 1; animation:g${i} ${D}s ${EASE} infinite; }
    @keyframes g${i} { 0%,${pct(s)}% { stroke-dashoffset:1; } ${pct(e)}%,100% { stroke-dashoffset:0; } }`;
  });
  commits.forEach(([x, y, t], i) => {
    const merge = i >= commits.length - 2;
    body += `\n    <circle class="c${i}" cx="${x}" cy="${y}" r="${merge ? 9 : 7.5}" fill="${merge ? PAPER : INK}" stroke="${INK}" stroke-width="3"/>`;
    style += `
    .c${i} { transform-box:fill-box; transform-origin:center; animation:c${i} ${D}s ${EASE} infinite; }
    @keyframes c${i} { 0%,${pct(t)}% { transform:scale(0); } ${pct(t + 0.4)}%,100% { transform:scale(1); } }`;
  });
  body += `
    ${MONO.text(ctx, "main", 36, 182, 13, { fill: INK })}
    ${MONO.text(ctx, "feat/ui", 140, 76, 13, { fill: INK })}
    ${MONO.text(ctx, "fix/api", 200, 238, 13, { fill: INK })}
  </g></g>
  <g transform="translate(${PX - 660} 0)"><g class="fallg" style="transform:translateY(${PY - 370}px)">${player(ctx)}</g></g>`;
  style += `
    .all { animation:all ${D}s linear infinite; }
    @keyframes all { 0%,92% { opacity:1; } 97%,100% { opacity:0; } }`;
  // com o player em y: quanto a tampa desce e quanto o meio estica (os dois lineares em y, então
  // usando os mesmos tempos e curvas da queda a borda acompanha o player certinho)
  const drop = (y) => Math.max(0, y - (GIT_Y - PH));
  const midAt = (y) => +((MID - drop(y)) / MID).toFixed(4);
  const G = 0.68;
  const keys = (fn) => `0%,${fp(FALL.hit)}% { transform:${fn(GIT_Y - PH)}; animation-timing-function:${PRESS}; } ${fp(FALL.land)}% { transform:${fn(PY)}; animation-timing-function:${SOFT}; } ${fp(FALL.land + 0.15)}% { transform:${fn(PY - BOUNCE)}; animation-timing-function:${SOFT}; } 100% { transform:${fn(PY)}; }`;
  const tTop = (y) => `translateY(${drop(y)}px)`, tMid = (y) => `scaleY(${midAt(y)})`;
  // o desenho só encolhe por igual e fica centrado no espaço que sobra
  const tGr = (y) => drop(y) === 0 ? "translate(0,0) scale(1)" : `translate(0,${r((drop(y) + 6 + B) / 2 - 152)}px) scale(${G})`;
  style += PLAYER_STYLE + fallAnim("fallg", GIT_Y) + `
    .gtop { transform:${tTop(PY)}; animation:gtop ${FALL.dur}s ${FALL.delay}s both; }
    @keyframes gtop { ${keys(tTop)} }
    .gmid { transform-origin:${W / 2}px ${B - R}px; transform:${tMid(PY)}; animation:gmid ${FALL.dur}s ${FALL.delay}s both; }
    @keyframes gmid { ${keys(tMid)} }
    .ggr { transform-origin:168px 152px; transform:${tGr(PY)}; animation:ggr ${FALL.dur}s ${FALL.delay}s both; }
    @keyframes ggr { ${keys(tGr)} }`;
  write("panel-git", W, H, { label: `Tocando agora: ${SONG.title}, de ${SONG.artist}.`, body, style, ctx });
}

// ---------- minimapa ----------
{
  // a miniatura do arquivo na lateral do editor: linhas de código vistas de longe, sem texto,
  // e a faixa da área visível descendo e subindo devagar. Calmo de propósito.
  const ctx = new Map(), W = 340, H = 420;
  let seed = 7;
  const rnd = () => ((seed = (seed * 16807) % 2147483647) / 2147483647);
  // recuo de cada linha (-1 = linha em branco), no formato de funções e blocos
  const shape = [0, 1, 1, 2, 2, 1, 0, -1, 0, 1, 2, 3, 3, 2, 1, 1, 0, -1, 0, 1, 1, 2, 2, 2, 1, 0, -1, 0, 1, 2, 1, 0];
  const top = 40, step = 10.8, bars = [];
  shape.forEach((ind, i) => {
    if (ind < 0) return;
    const y = top + i * step, x = 40 + ind * 18;
    let cx = x;
    const parts = 1 + Math.floor(rnd() * 3);
    for (let p = 0; p < parts && cx < 290; p++) {
      const w = Math.min(290 - cx, 14 + rnd() * (p === 0 ? 70 : 50));
      const strong = p === 0 && rnd() < 0.35;
      bars.push(`<rect x="${r(cx)}" y="${r(y)}" width="${r(w)}" height="5" rx="2.5" fill="${strong ? PAPER : MUTE}" fill-opacity="${strong ? 0.55 : r(0.28 + rnd() * 0.22)}"/>`);
      cx += w + 6;
    }
  });
  const body = `  ${panel(W, H)}
  <g clip-path="url(#mc)">
    <rect class="view" x="22" y="30" width="${W - 44}" height="118" rx="6" fill="${PAPER}" fill-opacity=".05" stroke="${PAPER}" stroke-opacity=".14" stroke-width="1.2"/>
    ${bars.join("\n    ")}
  </g>`;
  const style = `
    .view { animation:view 14s ease-in-out infinite alternate; }
    @keyframes view { 0%,8% { transform:translateY(0); } 92%,100% { transform:translateY(${H - 118 - 30 - 34}px); } }`;
  write("panel-minimap", W, H, { label: "", body, style, ctx, defs: clip("mc", W, H) });
}

// ---------- stack ----------
{
  const ctx = new Map(), W = 660, H = 420, top = 108, step = 26;
  const groups = [
    ["FRONT-END", ["HTML5", "CSS3", "Tailwind", "TypeScript", "JavaScript", "React"]],
    ["BACK-END", ["Node.js", "PHP", "Java", "MySQL"]],
    ["FERRAMENTAS", ["Git", "GitHub", "Linux", "Shell", "Docker", "CI/CD", "Figma", "UI/UX", "Trello", "Jira"]],
  ];
  let body = `  ${win(ctx, W, H, "stack.yml")}`;
  let style = `${IN}
    .tree { stroke-dasharray:1; animation:draw 1.4s ${EASE} backwards; }
    .run  { animation:run 2.8s ease-in-out infinite; }
    @keyframes draw { from { stroke-dashoffset:1; } }
    @keyframes run  { 0% { transform:translateY(0); opacity:0; } 10%,80% { opacity:1; } 100% { transform:translateY(var(--len)); opacity:0; } }`;
  groups.forEach(([title, items], gi) => {
    const x = 44 + gi * 205, d0 = 0.15 + gi * 0.15;
    const last = top + 30 + (items.length - 1) * step;
    body += `\n  <g class="in" ${delay(d0)}>${MONO.text(ctx, title, x, top, 14, { fill: PAPER, tr: 1.5 })}</g>`;
    let tree = `M${x + 4} ${top + 12} V${last - 4}`;
    items.forEach((it, i) => {
      const y = top + 30 + i * step;
      tree += ` M${x + 4} ${y - 5} H${x + 18}`;
      body += `\n  <g class="in" ${delay(d0 + 0.2 + i * 0.06)}>${SANS.text(ctx, it, x + 26, y, 17)}</g>`;
    });
    body += `\n  <path class="tree" pathLength="1" style="animation-delay:${d0}s" d="${tree}" fill="none" stroke="${MUTE}" stroke-width="1.5"/>`;
    body += `\n  <circle class="run" style="--len:${last - 4 - (top + 12)}px;animation-delay:${gi * 0.9}s" cx="${x + 4}" cy="${top + 12}" r="3.5" fill="${PAPER}"/>`;
  });
  write("panel-stack", W, H, {
    label: "Stack. Front-end: HTML5, CSS3, Tailwind, TypeScript, JavaScript, React. Back-end: Node.js, PHP, Java, MySQL. Ferramentas: Git, GitHub, Linux, Shell, Docker, CI/CD, Figma, UI/UX, Trello, Jira.",
    body, style, ctx,
  });
}

// ---------- links ----------
const ICONS = {
  // o logo do portfólio
  portfolio: (x, y) => `<g transform="translate(${x - 2} ${y - 2}) scale(.4)"><path d="${LOGO}" fill="none" stroke="${PAPER}" stroke-width="7" stroke-linecap="round" stroke-linejoin="round"/></g>`,
  linkedin: (x, y) => `<rect x="${x}" y="${y}" width="34" height="34" rx="7" fill="none" stroke="${PAPER}" stroke-width="2.5"/>
  <circle cx="${x + 10}" cy="${y + 10}" r="2.6" fill="${PAPER}"/>
  <path d="M${x + 10} ${y + 15.5} V${y + 26} M${x + 16.5} ${y + 26} V${y + 15.5} M${x + 16.5} ${y + 20.5} C${x + 16.5} ${y + 15}, ${x + 25.5} ${y + 14}, ${x + 25.5} ${y + 20.5} V${y + 26}" fill="none" stroke="${PAPER}" stroke-width="3.6" stroke-linecap="round"/>`,
  email: (x, y) => `<rect x="${x}" y="${y + 4}" width="36" height="26" rx="5" fill="none" stroke="${PAPER}" stroke-width="2.5"/>
  <path d="M${x + 3} ${y + 8} L${x + 18} ${y + 19} L${x + 33} ${y + 8}" fill="none" stroke="${PAPER}" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>`,
};
for (const [name, icon, W, title, sub] of [
  ["panel-link-portfolio", "portfolio", 333, "Portfólio", "portfolio-xi-orcin-59.vercel.app"],
  ["panel-link-linkedin", "linkedin", 334, "LinkedIn", "in/eduardo-teixeira-virissimo"],
  ["panel-link-email", "email", 333, "Email", "eduardoteixeiravirissimo@gmail.com"],
]) {
  const ctx = new Map(), H = 150;
  const subSize = Math.min(13, (W - 84) / MONO.width(sub, 1));
  const body = `  ${panel(W, H)}
  ${ICONS[icon](32, 28)}
  ${SANS.text(ctx, title, 32, 102, 26, { tr: -0.5 })}
  ${MONO.text(ctx, sub, 34, 128, subSize, { fill: MUTE })}
  <g class="arr"><path d="M${W - 58} 58 L${W - 36} 36 M${W - 54} 36 H${W - 36} V54" fill="none" stroke="${PAPER}" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/></g>`;
  const style = `
    .arr { animation:nudge 2.2s ease-in-out infinite; }
    @keyframes nudge { 0%,60%,100% { transform:translate(0,0); } 30% { transform:translate(5px,-5px); } }`;
  write(name, W, H, { label: `${title}: ${sub}`, body, style, ctx });
}

// ---------- rodapé (papel) ----------
{
  // barra fina no fim do README, só com o lema digitado no meio (mesma digitação dos outros painéis)
  const ctx = new Map(), W = 1000, H = 76, D = 10, y = 39;
  const pct = (t) => r((t / D) * 100);
  const s = "trying to be better", size = 16, tw = MONO.width(s, size), x = (W - tw) / 2, n = s.length;
  const t0 = 0.6, t1 = t0 + 0.06 * n;
  const body = `  ${panel(W, H, PAPER)}
  <g class="code">
    ${MONO.text(ctx, s, x, y + 6, size, { fill: INK })}
    <g class="cv"><rect x="${r(x + tw - 0.5)}" y="${y - 14}" width="${r(tw + 24)}" height="26" fill="${PAPER}"/><rect class="blink" x="${r(x + tw + 3)}" y="${y - 10}" width="9" height="19" fill="${INK}"/></g>
  </g>`;
  const style = `
    .code  { animation:fade ${D}s linear infinite; }
    @keyframes fade { 0%,90% { opacity:1; } 96%,100% { opacity:0; } }
    .cv    { animation:cv ${D}s infinite; }
    @keyframes cv { 0%,${pct(t0)}% { transform:translateX(-${r(tw)}px); animation-timing-function:steps(${n}, end); } ${pct(t1)}%,100% { transform:translateX(0); } }
    .blink { animation:blink 1.1s steps(1) infinite; }
    @keyframes blink { 50% { opacity:0; } }`;
  write("panel-footer", W, H, { label: s, body, style, ctx });
}
