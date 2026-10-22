// ---------------------------------------------------------------- themes
const THEME_DEF = { mode: "system", accent: "#5b5cf0", base: "light", tone: "warm", fs: 1, den: 1, rad: 1 };
const ACCENTS = ["#5b5cf0", "#2563eb", "#0891b2", "#16a34a", "#ca8a04", "#ea580c", "#dc2626", "#db2777"];
const TONES = {
  warm: {
    light: {
      bg: "#f4f4f1",
      paper: "#ffffff",
      soft: "#fafaf8",
      line: "#e7e6e1",
      line2: "#f0efeb",
      hover: "#f3f2ee",
      chip: "#efeee9",
      track: "#ebeae5",
      chip2: "#e4e3dd",
      mute: "#d9d7cf",
    },
    dark: {
      bg: "#13120f",
      paper: "#1c1a17",
      soft: "#171512",
      line: "#2e2a25",
      line2: "#24211d",
      hover: "#25221e",
      chip: "#2a2723",
      track: "#211e1a",
      chip2: "#332f2a",
      mute: "#433e37",
    },
  },
  cool: {
    light: {
      bg: "#f2f4f8",
      paper: "#ffffff",
      soft: "#f8f9fc",
      line: "#e2e6ee",
      line2: "#edf0f5",
      hover: "#eef1f6",
      chip: "#e9edf3",
      track: "#e4e8ef",
      chip2: "#dde2ea",
      mute: "#cdd3dd",
    },
    dark: {
      bg: "#0e1117",
      paper: "#161b24",
      soft: "#121620",
      line: "#252c38",
      line2: "#1c222c",
      hover: "#1d2430",
      chip: "#212834",
      track: "#1a2029",
      chip2: "#2a3240",
      mute: "#394252",
    },
  },
  neutral: {
    light: {
      bg: "#f4f4f4",
      paper: "#ffffff",
      soft: "#fafafa",
      line: "#e5e5e5",
      line2: "#efefef",
      hover: "#f1f1f1",
      chip: "#ececec",
      track: "#e8e8e8",
      chip2: "#e0e0e0",
      mute: "#d4d4d4",
    },
    dark: {
      bg: "#111111",
      paper: "#1a1a1a",
      soft: "#151515",
      line: "#2a2a2a",
      line2: "#202020",
      hover: "#222222",
      chip: "#262626",
      track: "#1e1e1e",
      chip2: "#303030",
      mute: "#404040",
    },
  },
};
function hexRgb(h) {
  h = h.replace("#", "");
  if (h.length === 3)
    h = h
      .split("")
      .map((c) => c + c)
      .join("");
  const n = parseInt(h, 16);
  return [(n >> 16) & 255, (n >> 8) & 255, n & 255];
}
function mix(a, b, t) {
  const x = hexRgb(a),
    y = hexRgb(b);
  return (
    "#" +
    x
      .map((v, i) =>
        Math.round(v + (y[i] - v) * t)
          .toString(16)
          .padStart(2, "0"),
      )
      .join("")
  );
}
function hexA(h, a) {
  const [r, g, b] = hexRgb(h);
  return `rgba(${r},${g},${b},${a})`;
}
function themeCfg() {
  return { ...THEME_DEF, ...LS.get("theme", {}) };
}
function applyTheme() {
  const t = themeCfg(),
    r = document.documentElement,
    sysDark = matchMedia("(prefers-color-scheme: dark)").matches;
  const dark = t.mode === "dark" || (t.mode === "system" && sysDark) || (t.mode === "custom" && t.base === "dark");
  r.dataset.theme = dark ? "dark" : "light";
  [
    "--bg",
    "--paper",
    "--soft",
    "--line",
    "--line2",
    "--hover",
    "--chip",
    "--track",
    "--chip2",
    "--mute",
    "--bgt",
    "--acc",
    "--acc-d",
    "--acc2",
    "--acc3",
    "--grad",
    "--fs",
    "--den",
    "--rad",
  ].forEach((p) => r.style.removeProperty(p));
  if (t.mode !== "custom") return;
  const P = TONES[t.tone] ? TONES[t.tone][dark ? "dark" : "light"] : TONES.warm.light;
  for (const [k, v] of Object.entries(P)) r.style.setProperty("--" + k, v);
  r.style.setProperty("--bgt", hexA(P.bg, 0.85));
  const a = /^#[0-9a-f]{6}$/i.test(t.accent) ? t.accent : THEME_DEF.accent,
    ac = dark ? mix(a, "#ffffff", 0.18) : a;
  r.style.setProperty("--acc", ac);
  r.style.setProperty("--acc-d", mix(a, "#000000", 0.15));
  r.style.setProperty("--acc2", dark ? hexA(a, 0.18) : mix(a, "#ffffff", 0.9));
  r.style.setProperty("--acc3", dark ? hexA(a, 0.36) : mix(a, "#ffffff", 0.72));
  r.style.setProperty("--grad", `linear-gradient(135deg,${a} 0%,${mix(a, "#c026d3", 0.35)} 100%)`);
  r.style.setProperty("--fs", t.fs);
  r.style.setProperty("--den", t.den);
  r.style.setProperty("--rad", t.rad);
}
let RTHEME = null;
function setTheme(patch) {
  LS.set("theme", { ...themeCfg(), ...patch });
  applyTheme();
}
// first start after the first screen: the theme chosen there, read before the first paint — no jump from light to dark
if (!LS.get("theme_set", false)) {
  try {
    const x = new XMLHttpRequest();
    x.open("GET", "/api/agent", false);
    x.setRequestHeader("X-Mnema-Token", TOKEN);
    x.send();
    const pt = ((JSON.parse(x.responseText) || {}).profile || {}).ui_theme;
    if (pt) {
      LS.set("theme", { ...themeCfg(), mode: pt });
      LS.set("theme_set", true);
    }
  } catch (e) {}
}
matchMedia("(prefers-color-scheme: dark)").addEventListener("change", applyTheme);
applyTheme();
function themeCard() {
  const t = themeCfg(),
    sg = (k, ch, v) =>
      `<div class="seg" data-th="${k}">${ch.map(([x, l]) => `<button data-v="${x}" class="${String(x) === String(v) ? "on" : ""}">${l}</button>`).join("")}</div>`;
  return `<div class="card" data-sec="app" id="themecard"><div class="set"><b>Оформление</b><div>${sg(
    "mode",
    [
      ["system", "Как в Windows"],
      ["light", "Светлая"],
      ["dark", "Тёмная"],
      ["custom", "Своя"],
    ],
    t.mode,
  )}</div></div>
   ${
     t.mode === "custom"
       ? `<div class="set"><b>Цвет</b><div class="swatches">${ACCENTS.map((c) => `<button class="sw8 ${c === t.accent ? "on" : ""}" data-acc="${c}" style="background:${c}" title="${c}"></button>`).join("")}<label class="swpick" title="Свой цвет"><input type="color" id="thcol" value="${esc(t.accent)}">+</label></div></div>
   <div class="set"><b>Основа</b><div>${sg(
     "base",
     [
       ["light", "Светлая"],
       ["dark", "Тёмная"],
     ],
     t.base,
   )}</div></div>
   <div class="set"><b>Фон</b><div>${sg(
     "tone",
     [
       ["warm", "Тёплый"],
       ["cool", "Холодный"],
       ["neutral", "Нейтральный"],
     ],
     t.tone,
   )}</div></div>
   <div class="set"><b>Текст</b><div>${sg(
     "fs",
     [
       [0.92, "Мельче"],
       [1, "Обычный"],
       [1.1, "Крупнее"],
     ],
     t.fs,
   )}</div></div>
   <div class="set"><b>Плотность</b><div>${sg(
     "den",
     [
       [0.8, "Плотнее"],
       [1, "Обычная"],
       [1.2, "Просторнее"],
     ],
     t.den,
   )}</div></div>
   <div class="set"><b>Углы</b><div>${sg(
     "rad",
     [
       [0.4, "Острее"],
       [1, "Обычные"],
       [1.5, "Мягче"],
     ],
     t.rad,
   )}</div></div>`
       : ""
   }</div>`;
}
function bindThemeCard(redraw) {
  const c = $("#themecard");
  if (!c) return;
  $$("[data-th]", c).forEach((g) =>
    $$("button", g).forEach(
      (b) =>
        (b.onclick = () => {
          const k = g.dataset.th,
            v = b.dataset.v;
          setTheme({ [k]: ["fs", "den", "rad"].includes(k) ? +v : v });
          redraw();
        }),
    ),
  );
  $$("[data-acc]", c).forEach(
    (b) =>
      (b.onclick = () => {
        setTheme({ accent: b.dataset.acc });
        redraw();
      }),
  );
  const col = $("#thcol", c);
  if (col)
    col.oninput = (e) => {
      setTheme({ accent: e.target.value });
    };
  if (col) col.onchange = () => redraw();
}
