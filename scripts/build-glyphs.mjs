// Extrai os contornos das fontes do portfólio para scripts/glyphs-<nome>.json.
//
// Todo o texto dos SVGs vira <path>/<use>, então o README renderiza igual em qualquer máquina, sem
// depender de fonte instalada em quem abre. Só precisa rodar de novo para acrescentar um caractere.
//
//   mkdir fonttool && cd fonttool && npm init -y
//   npm i opentype.js @fontsource/geist-sans @fontsource/geist-mono @fontsource/instrument-serif @fontsource/caveat
//   node <caminho>/scripts/build-glyphs.mjs        (rodando de dentro de fonttool)
import fs from "node:fs";
import path from "node:path";
import { createRequire } from "node:module";
import { fileURLToPath } from "node:url";

const HERE = path.dirname(fileURLToPath(import.meta.url));
// opentype.js e as fontes vêm do node_modules da pasta de onde o script é chamado.
const require = createRequire(path.join(process.cwd(), "noop.js"));
const opentype = require("opentype.js");
const fontFile = (pkg, file) => path.join(path.dirname(require.resolve(`${pkg}/package.json`)), "files", file);

const FONTS = {
  sans: fontFile("@fontsource/geist-sans", "geist-sans-latin-400-normal.woff"),
  bold: fontFile("@fontsource/geist-sans", "geist-sans-latin-600-normal.woff"),
  mono: fontFile("@fontsource/geist-mono", "geist-mono-latin-400-normal.woff"),
  serif: fontFile("@fontsource/instrument-serif", "instrument-serif-latin-400-italic.woff"),
  hand: fontFile("@fontsource/caveat", "caveat-latin-400-normal.woff"),
};

// Tudo o que o texto do README usa: ASCII, acentos do português e um pouco de pontuação.
const CHARS =
  Array.from({ length: 95 }, (_, i) => String.fromCharCode(32 + i)).join("") +
  "áàâãäéêèíìîóòôõöúùûüçñÁÀÂÃÉÊÍÓÔÕÚÇ–—·©…“”‘’";

for (const [name, file] of Object.entries(FONTS)) {
  const font = opentype.parse(fs.readFileSync(file).buffer);
  const glyphs = {};
  for (const char of CHARS) {
    const glyph = font.charToGlyph(char);
    if (!glyph || glyph.index === 0) continue;
    // `glyph.path` está em unidades da fonte, com y para cima (o gerador inverte ao desenhar).
    glyphs[char] = { adv: glyph.advanceWidth, d: glyph.path.commands.length ? outline(glyph) : "" };
  }
  const out = { upm: font.unitsPerEm, glyphs };
  fs.writeFileSync(path.join(HERE, `glyphs-${name}.json`), JSON.stringify(out));
  console.log(`glyphs-${name}.json  ${Object.keys(glyphs).length} glifos`);
}

/** O contorno do glifo com y para cima (como no arquivo da fonte), arredondado a 1 casa. */
function outline(glyph) {
  const r = (v) => Math.round(v * 10) / 10;
  return glyph.path.commands
    .map((c) => {
      switch (c.type) {
        case "M":
        case "L":
          return `${c.type}${r(c.x)} ${r(c.y)}`;
        case "Q":
          return `Q${r(c.x1)} ${r(c.y1)} ${r(c.x)} ${r(c.y)}`;
        case "C":
          return `C${r(c.x1)} ${r(c.y1)} ${r(c.x2)} ${r(c.y2)} ${r(c.x)} ${r(c.y)}`;
        case "Z":
          return "Z";
        default:
          return "";
      }
    })
    .join("");
}
