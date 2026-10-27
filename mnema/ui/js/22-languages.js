// ---------------------------------------------------------------- languages
// The page is written in Russian. For another language every visible text is looked up in /i18n/<lang>.json:
// exact phrases, and patterns with {} for values the code puts in ("{} файлов памяти"). Conversation, memory and
// anything the owner typed are never touched.
const LANGS = [
  ["ru", "Русский"],
  ["en", "English"],
  ["zh", "中文"],
  ["es", "Español"],
  ["hi", "हिन्दी"],
  ["pt", "Português"],
  ["fr", "Français"],
  ["de", "Deutsch"],
  ["ja", "日本語"],
];
const I18N = { lang: LS.get("lang", "en"), dict: {}, pats: [] };
const NO_I18N =
  ".md,.msg.user .b,.uq,textarea,code,pre,.facts li,.path,#ctitle,.citem .tr b,.hit,.ttip,.editor,[data-noi18n],.who,.spk,.conline,.pi b," +
  ".mtprev,.mth b,.mbub b,.mbub span,.mtlist,.rlq,.mtmh b";
async function loadLang() {
  if (!LANGS.some(([k]) => k === I18N.lang)) {
    // a language Mnema no longer has (Arabic was removed): English instead
    I18N.lang = "en";
    LS.set("lang", "en");
    post("/api/agent", { lang: "en" }).catch(() => {}); // the answers follow the interface again
  }
  const l = I18N.lang;
  document.documentElement.lang = l;
  document.documentElement.dir = "ltr";
  if (l === "ru") {
    I18N.dict = {};
    I18N.pats = [];
    return;
  }
  try {
    const d = await (await fetch("/i18n/" + l + ".json")).json();
    I18N.dict = d.exact || {};
    I18N.pats = Object.entries(d.patterns || {})
      .map(([src, dst]) => ({
        lit: src.replace(/\{\}/g, "").length,
        dst,
        re: new RegExp(
          "^" +
            src
              .split("{}")
              .map((x) => x.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"))
              .join("(.+?)") +
            "$",
          "s",
        ),
      }))
      .filter((p) => p.lit >= 4)
      .sort((a, b) => b.lit - a.lit);
  } catch (e) {
    I18N.dict = {};
    I18N.pats = [];
  }
}
function tr(text) {
  if (I18N.lang === "ru" || !text) return text;
  const k = String(text).replace(/\s+/g, " ").trim();
  if (!k || !/[А-Яа-яЁё]/.test(k)) return text;
  const v = I18N.dict[k];
  if (v) return String(text).replace(String(text).trim(), v);
  for (const p of I18N.pats) {
    const m = p.re.exec(k);
    if (m) {
      let i = 1;
      return p.dst.replace(/\{\}/g, () => tr(m[i++]));
    }
  }
  const core = k.match(/^([^\p{L}]*)([\s\S]*?)([^\p{L}]*)$/u);
  if (core && core[2] && (core[1] || core[3]) && core[2] !== k) {
    const t = tr(core[2]);
    if (t !== core[2]) return String(text).replace(String(text).trim(), core[1] + t + core[3]);
  }
  const parts = k.split(/( · | — |: )/);
  if (parts.length > 1) {
    const t = parts.map((x) => (/^( · | — |: )$/.test(x) ? x : tr(x))).join("");
    if (t !== k) return String(text).replace(String(text).trim(), t);
  }
  return text;
}
function i18nTree(root) {
  if (I18N.lang === "ru" || !root) return;
  const el = root.nodeType === 1 ? root : root.parentElement;
  if (!el || (el.closest && el.closest(NO_I18N))) return;
  if (root.nodeType === 3) {
    const t = tr(root.nodeValue);
    if (t !== root.nodeValue) root.nodeValue = t;
    return;
  }
  const attrs = (n) => {
    for (const a of ["title", "placeholder", "aria-label"]) {
      const v = n.getAttribute && n.getAttribute(a);
      if (v && /[А-Яа-яЁё]/.test(v)) n.setAttribute(a, tr(v));
    }
  };
  const w = document.createTreeWalker(root, NodeFilter.SHOW_TEXT | NodeFilter.SHOW_ELEMENT, {
    acceptNode: (n) => {
      if (n.nodeType !== 1) return NodeFilter.FILTER_ACCEPT;
      if (n.matches("textarea,input")) {
        attrs(n);
        return NodeFilter.FILTER_REJECT;
      }
      return n.matches(NO_I18N) ? NodeFilter.FILTER_REJECT : NodeFilter.FILTER_ACCEPT;
    },
  });
  if (root.nodeType === 1 && root.matches("textarea,input")) {
    attrs(root);
    return;
  }
  let n = root;
  do {
    if (n.nodeType === 3) {
      if (/[А-Яа-яЁё]/.test(n.nodeValue)) {
        const t = tr(n.nodeValue);
        if (t !== n.nodeValue) n.nodeValue = t;
      }
    } else attrs(n);
  } while ((n = w.nextNode()));
}
new MutationObserver((ms) => {
  if (I18N.lang === "ru") return;
  for (const m of ms) {
    if (m.type === "characterData") i18nTree(m.target);
    else if (m.type === "attributes") {
      // a hint set later (title, placeholder): translated too; an already translated one has no Cyrillic and stays
      const v = m.target.getAttribute(m.attributeName);
      if (v && /[А-Яа-яЁё]/.test(v) && !(m.target.closest && m.target.closest(NO_I18N))) {
        const t = tr(v);
        if (t !== v) m.target.setAttribute(m.attributeName, t);
      }
    } else m.addedNodes.forEach(i18nTree);
  }
}).observe(document.documentElement, {
  childList: true,
  subtree: true,
  characterData: true,
  attributes: true,
  attributeFilter: ["title", "placeholder", "aria-label"],
});
const FSTAR = "M0,-1L.294,-.405L.951,-.309L.476,.155L.588,.809L0,.5L-.588,.809L-.476,.155L-.951,-.309L-.294,-.405Z";
const FLAGS = {
  ru: '<rect width="30" height="20" fill="#fff"/><rect y="6.67" width="30" height="6.67" fill="#0039A6"/><rect y="13.33" width="30" height="6.67" fill="#D52B1E"/>',
  en: '<rect width="30" height="20" fill="#012169"/><path d="M0,0L30,20M30,0L0,20" stroke="#fff" stroke-width="4"/><path d="M0,0L30,20M30,0L0,20" stroke="#C8102E" stroke-width="1.6"/><path d="M15,0V20M0,10H30" stroke="#fff" stroke-width="6"/><path d="M15,0V20M0,10H30" stroke="#C8102E" stroke-width="3.4"/>',
  zh: `<rect width="30" height="20" fill="#DE2910"/><path d="${FSTAR}" fill="#FFDE00" transform="translate(6,6) scale(3)"/><path d="${FSTAR}" fill="#FFDE00" transform="translate(11,2.5) scale(1)"/><path d="${FSTAR}" fill="#FFDE00" transform="translate(13,5) scale(1)"/><path d="${FSTAR}" fill="#FFDE00" transform="translate(13,8.5) scale(1)"/><path d="${FSTAR}" fill="#FFDE00" transform="translate(11,11) scale(1)"/>`,
  es: '<rect width="30" height="20" fill="#AA151B"/><rect y="5" width="30" height="10" fill="#F1BF00"/>',
  hi: '<rect width="30" height="20" fill="#fff"/><rect width="30" height="6.67" fill="#FF9933"/><rect y="13.33" width="30" height="6.67" fill="#138808"/><circle cx="15" cy="10" r="2.6" fill="none" stroke="#000080" stroke-width=".8"/><circle cx="15" cy="10" r=".6" fill="#000080"/>',
  ar: '<rect width="30" height="20" fill="#006C35"/><path d="M8,7.5c2-1.5 4,1 6-.5s3,1 5,0 3,1 3.5,.2" fill="none" stroke="#fff" stroke-width="1.1" stroke-linecap="round"/><path d="M8,12.5H21.5l1.5-1" fill="none" stroke="#fff" stroke-width="1.1" stroke-linecap="round"/>',
  pt: '<rect width="30" height="20" fill="#FF0000"/><rect width="12" height="20" fill="#006600"/><circle cx="12" cy="10" r="3.6" fill="#FFCC00"/><circle cx="12" cy="10" r="2.2" fill="#FF0000"/><rect x="11" y="8.6" width="2" height="2.8" rx=".4" fill="#fff"/>',
  fr: '<rect width="30" height="20" fill="#fff"/><rect width="10" height="20" fill="#0055A4"/><rect x="20" width="10" height="20" fill="#EF4135"/>',
  de: '<rect width="30" height="20" fill="#000"/><rect y="6.67" width="30" height="6.67" fill="#DD0000"/><rect y="13.33" width="30" height="6.67" fill="#FFCE00"/>',
  ja: '<rect width="30" height="20" fill="#fff"/><circle cx="15" cy="10" r="6" fill="#BC002D"/>',
};
const flagSvg = (k) => {
  const id = "fc" + k + Math.random().toString(36).slice(2, 7);
  return `<svg class="flag" viewBox="0 0 30 20"><clipPath id="${id}"><rect width="30" height="20" rx="3"/></clipPath><g clip-path="url(#${id})">${FLAGS[k] || ""}</g><rect width="30" height="20" rx="3" fill="none" stroke="rgba(0,0,0,.12)"/></svg>`;
};
function langMenu(anchor) {
  if ($(".lmenu")) {
    $(".lmenu").remove();
    return;
  }
  closeMenus();
  MENU_ANCHOR = anchor;
  const m = document.createElement("div");
  m.className = "mmenu menu lmenu";
  m.innerHTML =
    LANGS.map(
      ([k, n]) =>
        `<button data-l="${k}" class="mrow ${k === I18N.lang ? "cur" : ""}" data-noi18n>${flagSvg(k)}<span class="mn">${n}</span><span class="mm">${k.toUpperCase()}</span></button>`,
    ).join("") +
    `<div class="lnote">${ic("chat")}<span>${tr("ИИ отвечает на выбранном здесь языке, даже если ты пишешь на другом")}</span></div>`;
  document.body.appendChild(m);
  const r = anchor.getBoundingClientRect();
  m.style.width = "250px";
  m.style.left = r.right - 250 + "px";
  m.style.top = r.bottom + 6 + "px";
  $$("[data-l]", m).forEach(
    (b) =>
      (b.onclick = async () => {
        const l = b.dataset.l;
        m.remove();
        if (l === I18N.lang) return;
        LS.set("lang", l);
        await post("/api/agent", { lang: l }).catch(() => {});
        location.reload();
      }),
  );
}
function topRight() {
  let c = $("#trc");
  if (c) return c;
  c = document.createElement("div");
  c.id = "trc";
  c.className = "trc";
  c.innerHTML = `<div class="trrow"><span class="trs" id="tuslot"></span><span class="trs" id="gslot"></span></div>`;
  document.body.appendChild(c);
  return c;
}
function drawTutBtn() {
  const slot = topRight().querySelector("#tuslot");
  const on = LS.get("tour", true);
  document.body.classList.toggle("touron", on);
  setTimeout(fitTitle, 0);
  if (!on) {
    slot.innerHTML = "";
    drawGear();
    return;
  }
  if (!$("#tutbtn", slot)) {
    slot.innerHTML = `<button id="tutbtn" class="tutbtn on" title="${tr("Туториал показывается в каждом новом разговоре. Выключишь — переедет в шестерёнку")}">${ic("book")}<span>${tr("Туториал")}</span><i class="sw2"></i></button>`;
    $("#tutbtn", slot).onclick = () => setTour(false);
  }
  drawGear();
}
function setTour(on) {
  LS.set("tour", on);
  drawTutBtn();
  if (!CHAT.id && $(".startline")) renderEmpty();
  if (!on) {
    toast(tr("Туториал теперь в шестерёнке"));
    post("/api/ach/event", { name: "tutorial_off" })
      .then(() => setTimeout(achRefresh, 300))
      .catch(() => {});
  }
}
const THEME_ICON = { system: "auto", light: "sun", dark: "moon", custom: "palette" };
function drawThemeBtn() {
  drawGear();
}
function themeMenu(anchor) {
  if ($(".thmenu")) {
    $(".thmenu").remove();
    return;
  }
  closeMenus();
  MENU_ANCHOR = anchor;
  const cur = themeCfg().mode,
    m = document.createElement("div");
  m.className = "menu thmenu";
  m.innerHTML =
    [
      ["system", "auto", "Как в Windows"],
      ["light", "sun", "Светлая"],
      ["dark", "moon", "Тёмная"],
      ["custom", "palette", "Своя"],
    ]
      .map(
        ([k, i, t]) =>
          `<button data-tm="${k}" class="${k === cur ? "cur" : ""}">${ic(i)}<span>${t}</span>${k === cur ? ic("check") : ""}</button>`,
      )
      .join("") + `<hr><button data-tm="tune">${ic("gear")}<span>Настроить свою тему</span></button>`;
  document.body.appendChild(m);
  const r = anchor.getBoundingClientRect();
  m.style.left = Math.max(8, Math.min(innerWidth - m.offsetWidth - 8, r.right - m.offsetWidth)) + "px";
  m.style.top = r.bottom + 6 + "px";
  $$("[data-tm]", m).forEach(
    (b) =>
      (b.onclick = () => {
        const k = b.dataset.tm;
        m.remove();
        if (k === "tune") {
          setTheme({ mode: "custom" });
          drawThemeBtn();
          goSet("app/themecard");
          return;
        }
        setTheme({ mode: k });
        drawThemeBtn();
        const c = $("#themecard");
        if (c) {
          c.outerHTML = themeCard();
          typeof RTHEME === "function" && RTHEME();
        }
      }),
  );
}
function drawLangBtn() {
  drawTutBtn();
  applyAch();
}
