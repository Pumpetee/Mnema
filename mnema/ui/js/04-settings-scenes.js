// ---------------------------------------------------------------- settings: sections and exact links
// #settings/<section>/<block id> opens the section, scrolls to the block and lights it up. Every button that leads
// into the settings uses such a link (goSet), so it lands exactly where it promised.
const SETSECS = [
  ["ai", "chat", "ИИ и модели"],
  ["style", "edit", "Как отвечает"],
  ["learn", "book", "Обучение"],
  ["security", "shield", "Безопасность"],
  ["engine", "gear", "Движок"],
  ["meetings", "users", "Записи встреч"],
  ["app", "set", "Программа"],
];
let SETCUR = "ai";
function goSet(path) {
  if (location.hash === "#settings/" + path) viewSettings(path);
  else location.hash = "settings/" + path;
}
function showSec(sec, card) {
  SETCUR = sec;
  LS.set("setsec", sec);
  $$(".setnav [data-sec]").forEach((b) => b.classList.toggle("on", b.dataset.sec === sec));
  let k = 0;
  $$("#st .card[data-sec]").forEach((c) => {
    c.hidden = c.dataset.sec !== sec;
    if (!c.hidden) {
      c.classList.remove("secin");
      void c.offsetWidth;
      c.style.animationDelay = k++ * 0.05 + "s";
      c.classList.add("secin");
    }
  });
  history.replaceState(null, "", "#settings/" + sec + (card ? "/" + card : ""));
  const pg = $(".page");
  if (!card) {
    if (pg) pg.scrollTop = 0;
    return;
  }
  const el = document.getElementById(card);
  if (!el) return;
  el.hidden = false;
  setTimeout(() => {
    el.scrollIntoView({ block: "start", behavior: "smooth" });
    el.classList.remove("flash");
    void el.offsetWidth;
    el.classList.add("flash");
  }, 60);
}
// "Настройки → Движок" in a message becomes a link to that exact place
const SET_LINKS = {
  Движок: "engine/engcard",
  Встречи: "meetings/scrcard",
  "Записи встреч": "meetings/scrcard",
  Безопасность: "security/seccard",
  "Локальная модель": "ai/c-local",
  "Подключить другую модель": "ai/c-prov",
  Прокси: "app/netcard",
  "VPN и прокси": "app/netcard",
  "ИИ и модели": "ai/c-prov",
};
function linkSettings(html) {
  return html.replace(
    /Настройки → (Движок|Записи встреч|Встречи|Безопасность|Локальная модель|Подключить другую модель|VPN и прокси|Прокси|ИИ и модели)/g,
    (m, k) => `<a href="#settings/${SET_LINKS[k]}" class="setlink">${m}</a>`,
  );
}
// ---------------------------------------------------------------- mini scenes next to every switch in the settings
// Each switch shows what the system reacts to and how: a tiny looping scene for its current state. Toggling replays it.
// chat: [what the owner says, the answer when off, the answer when on, extra] — extra: md, table, buttons, check, save, flag
// flow: {f:[icon,label], t:[icon,label], on:[packet,mode], off:[packet,mode]} — mode go | block | stop | raw
const MINI_FLOW = {
  secred: {
    f: ["file", "Твой запрос"],
    t: ["globe", "Облачный ИИ"],
    on: ["[КАРТА-1]", "go"],
    off: ["4111 1111…", "raw"],
    re: "номера карт, пароли, ключи, телефоны",
  },
  secefs: {
    f: ["folder", "Папка памяти"],
    t: ["eye", "Чужой вход"],
    on: ["🔒", "block"],
    off: ["текст", "raw"],
    re: "диск без твоего входа в Windows",
  },
  autos: {
    f: ["set", "Windows"],
    t: ["mem", "Mnema"],
    on: ["запуск", "go"],
    off: ["", "stop"],
    re: "включение компьютера",
  },
  pauto: {
    f: ["book", "Рецепт"],
    t: ["chat", "Ответ"],
    on: ["", "go"],
    off: ["", "stop"],
    re: "узнала знакомую задачу",
  },
  englow: { meter: 1, re: "нагрузка от локальной модели" },
};
const MINI_CAP = {
  secred: ["Секреты заменены метками", "Уходят как есть"],
  secefs: ["Без входа не прочитать", "Файлы читаются с диска"],
  autos: ["Учится в фоне с запуска", "Ждёт, пока откроешь"],
  pauto: ["Узнала задачу — готовит по рецепту", "Рецепты сама не берёт"],
  englow: ["Окна и браузер не тормозят", "Модель берёт всё, что может"],
};
// ---------------------------------------------------------------- every switch: its own little scene + how Mnema reacts
// [scene, data, reaction when on, reaction when off]
const MR = {
  no_filler: [
    "strike",
    { w: "Хороший вопрос! Давайте разберёмся…", r: "10 дней." },
    "Сразу по делу",
    "Со вступлениями",
  ],
  lead: ["format", { to: "list" }, "Главное — первой строкой", "Главное где-то в середине"],
  ty: ["swap", { ctx: "Давай начнём", a: "Вы", b: "ты" }, "Обращается на «ты»", "Обращается на «вы»"],
  plain: [
    "swap",
    { ctx: "Сервер:", a: "OOMKilled", b: "не хватило памяти" },
    "Без жаргона и сокращений",
    "Может писать техническим языком",
  ],
  no_stamps: ["strike", { w: "Отличный вопрос!", r: "Ошибка в строке 14." }, "Убирает штампы", "Штампы возможны"],
  humor: ["strike", { w: "😄 цифры в прятки", r: "Дубль в строке 12." }, "Шутит редко и к месту", "Может шутить"],
  ask_options: [
    "buttons",
    { q: "Какой тон?", o: ["Официально", "Дружески"] },
    "Вопрос — кнопками с вариантами",
    "Вопрос — списком в тексте",
  ],
  only_asked: [
    "shrink",
    { n: 4, b: "Исправил опечатку", tag: "+ абзац" },
    "Ровно то, что просили",
    "Может добавить лишнее",
  ],
  no_invent: [
    "num",
    { a: "≈ 50 млн", b: "не знаю — проверю", bad: 1 },
    "Не знает — так и скажет",
    "Может додумать цифру",
  ],
  memory_first: ["memo", { q: "Где живу?", a: "Казань" }, "Сверяется с памятью", "Отвечает по догадке"],
  second_pass: [
    "scan",
    { n: 5, hits: [0, 1, 2, 3, 4], label: "перепроверено", all: 1 },
    "Перечитывает ответ перед отправкой",
    "Отправляет сразу",
  ],
  say_saved: ["save", { t: "Живёт в Казани", tag: "запомню" }, "Отмечает новое для памяти", "Молча"],
  no_secrets: ["hide", { t: "Пароль:", h: "qwerty123", pw: 1 }, "Пароли и ключи не повторяет", "Может повторить"],
  tables: ["format", { to: "table" }, "Сравнения — таблицей", "Простынёй текста"],
};
function mrScene(type, d, on) {
  const O = on ? "is-on" : "is-off";
  if (type === "swap")
    return `<div class="ms swap ${O}"><span class="ctx">${esc(d.ctx)}</span><span class="pair"><em class="a">${esc(d.a)}</em><em class="b">${esc(d.b)}</em></span></div>`;
  if (type === "tone")
    return `<div class="ms tone ${O}"><div class="bub a">${esc(d.a)}</div><div class="bub b">${esc(d.b)}</div><i class="dial"><b></b></i></div>`;
  if (type === "shrink")
    return `<div class="ms shrink ${O}"><div class="lines">${Array.from({ length: d.n }, (_, k) => `<i style="--w:${60 + ((k * 37) % 35)}%;--k:${k}"></i>`).join("")}${d.tag ? `<span class="tg2">${esc(d.tag)}</span>` : ""}</div><div class="short">${esc(d.b)}</div></div>`;
  if (type === "format") {
    const wall = `<div class="wall">${Array.from({ length: 5 }, (_, k) => `<i style="--w:${70 + ((k * 13) % 30)}%"></i>`).join("")}</div>`;
    const res =
      d.to === "table"
        ? `<table class="tb"><tr><th></th><th></th></tr><tr><td></td><td></td></tr><tr><td></td><td></td></tr></table>`
        : d.to === "num"
          ? `<div class="num">${esc(d.b)}</div>`
          : `<div class="lst"><b></b><i></i><i></i><i></i></div>`;
    return `<div class="ms format ${O}">${d.to === "num" ? `<div class="wall txt">${esc(d.a)}</div>` : wall}<div class="res">${res}</div></div>`;
  }
  if (type === "strike")
    return `<div class="ms strike ${O} ${d.end ? "end" : ""}"><span class="w">${esc(d.w)}</span><span class="r">${esc(d.r)}</span></div>`;
  if (type === "pin")
    return `<div class="ms pin ${O}"><i class="ln"></i><i class="ln"></i><div class="card2"><span class="lab">Главное</span>${esc(d.t)}</div><i class="ln"></i></div>`;
  if (type === "gate")
    return `<div class="ms gate ${O}"><div class="qs">${esc(d.q)}</div><b class="arr">→</b><div class="go">${esc(d.r)}</div></div>`;
  if (type === "steps")
    return `<div class="ms steps ${O} ${d.ask ? "ask" : ""} ${d.seq ? "seq" : ""}">${d.l.map((t, k) => `<span style="--k:${k}"><i>${k + 1}</i>${esc(t)}</span>`).join("")}</div>`;
  if (type === "buttons")
    return `<div class="ms buttons ${O}"><div class="q">${esc(d.q)}</div><div class="opts">${d.o.map((t, k) => `<em style="--k:${k}">${esc(t)}</em>`).join("")}</div><div class="lst2"><i></i><i></i><i></i></div></div>`;
  if (type === "copy")
    return `<div class="ms copy ${O}"><div class="tpl"><i></i><i></i><b></b></div><div class="arrow">⇢</div><div class="tpl new"><i></i><i></i><b></b></div></div>`;
  if (type === "scan")
    return `<div class="ms scan ${O} ${d.bad ? "bad" : ""} ${d.all ? "all" : ""}"><div class="lines">${Array.from({ length: d.n }, (_, k) => `<i class="${d.hits.includes(k) ? "hit" : ""}" style="--k:${k}"></i>`).join("")}</div><span class="lens"></span><span class="lab">${esc(d.label)}</span></div>`;
  if (type === "warn")
    return `<div class="ms warn ${O}"><i class="ln"></i><i class="ln"></i><div class="tri">!</div><div class="msg">${esc(d.t)}</div></div>`;
  if (type === "memo")
    return `<div class="ms memo ${O} ${d.old ? "old" : ""}"><div class="q">${esc(d.q)}</div><div class="mem">${ic("mem")}<span>${esc(d.a)}</span></div><b class="ok">${d.old ? "?" : "✓"}</b></div>`;
  if (type === "num")
    return `<div class="ms num ${O} ${d.bad ? "bad" : ""}"><span class="a">${esc(d.a)}</span><span class="b">${esc(d.b)}</span></div>`;
  if (type === "save")
    return `<div class="ms save ${O}"><div class="fact">${d.idea ? "💡 " : ""}${esc(d.t)}<em>${esc(d.tag)}</em></div><div class="box">${ic("mem")}</div></div>`;
  if (type === "hide")
    return `<div class="ms hide ${O}"><span class="t">${esc(d.t)}</span><span class="h">${esc(d.h)}</span><span class="lk">${ic("lock")}</span></div>`;
  if (type === "loop")
    return `<div class="ms loop ${O}"><svg viewBox="0 0 60 60"><path d="M30 8a22 22 0 1 1-19 11"/><path d="M8 12l3 7 7-3"/></svg><b class="ok">✓</b></div>`;
  if (type === "doc")
    return `<div class="ms doc ${O}"><div class="pg">${Array.from({ length: 6 }, (_, k) => `<i style="--k:${k}"></i>`).join("")}</div></div>`;
  return "";
}
function miniScene(key, on, label) {
  const r = MR[key];
  if (r) return `<div class="mini mr ${on ? "is-on" : "is-off"}">${mrScene(r[0], r[1], on)}</div>`;
  const f =
    MINI_FLOW[key] ||
    (key.startsWith("src:")
      ? { f: ["book", label || key.slice(4)], t: ["mem", "Память"], on: ["новое", "go"], off: ["", "stop"], re: label }
      : null);
  if (!f) return "";
  if (f.meter)
    return `<div class="mini mmeter ${on ? "is-on" : "is-off"}"><div class="mrowm"><span>Mnema</span><i><b style="--w:${on ? 28 : 88}%"></b></i></div><div class="mrowm"><span>${tr("Браузер")}</span><i><b class="o" style="--w:${on ? 64 : 12}%"></b></i></div><div class="mrowm"><span>${tr("Окна")}</span><i><b class="o" style="--w:${on ? 48 : 8}%"></b></i></div></div>`;
  const [pk, mode] = on ? f.on : f.off;
  return `<div class="mini mflow ${on ? "is-on" : "is-off"} m-${mode}"><div class="mnode">${ic(f.f[0])}<span>${esc(tr(f.f[1]))}</span></div><div class="mpipe"><i class="mline"></i>${pk ? `<em class="mpk">${esc(pk)}</em>` : ""}${mode === "block" ? '<b class="mx">×</b>' : ""}</div><div class="mnode">${ic(f.t[0])}<span>${esc(tr(f.t[1]))}</span></div></div>`;
}
function miniReact(key, on) {
  const r = MR[key];
  if (r) return on ? r[2] : r[3];
  const c = MINI_CAP[key] || (key.startsWith("src:") ? ["Читает новое и учится", "Не читает этот источник"] : null);
  return c ? c[on ? 0 : 1] : "";
}
function miniKey(sw) {
  if (sw.dataset.tog) return sw.dataset.tog;
  if (sw.dataset.src) return "src:" + sw.dataset.src;
  return sw.id || "";
}
function decorateToggles(root) {
  const attach = (row, sw, host, slot) => {
    const key = miniKey(sw),
      label = ($("b", row) || {}).textContent || "";
    const react = document.createElement("div");
    react.className = "react";
    host.appendChild(react);
    const draw = (swap) => {
      const on = sw.classList.contains("on");
      slot.innerHTML = miniScene(key, on, label);
      if (swap) {
        const m = $(".mini", slot);
        m && m.classList.add("swap");
      }
      react.innerHTML = `${ic("chat")}<span><b>${tr("Как среагирует")}:</b> ${esc(tr(miniReact(key, on)))}</span>`;
      react.classList.toggle("on", on);
      if (swap) {
        react.classList.remove("rpop");
        void react.offsetWidth;
        react.classList.add("rpop");
      }
    };
    draw(false);
    new MutationObserver(() => draw(true)).observe(sw, { attributes: true, attributeFilter: ["class"] });
  };
  $$(".tg", root || document).forEach((tg) => {
    const sw = $(".sw", tg);
    if (!sw || tg.dataset.mini) return;
    const key = miniKey(sw);
    if (!MR[key] && !MINI_FLOW[key]) return;
    tg.dataset.mini = "1";
    tg.classList.add("hasmini");
    const slot = document.createElement("div");
    slot.className = "minislot";
    tg.appendChild(slot);
    const host = $("div", tg) || tg;
    attach(tg, sw, host, slot);
  });
  $$(".set", root || document).forEach((set) => {
    const sws = $$(".sw", set);
    if (sws.length !== 1 || set.dataset.mini || sws[0].closest(".tg")) return;
    const sw = sws[0],
      key = miniKey(sw);
    if (!MR[key] && !MINI_FLOW[key]) return;
    set.dataset.mini = "1";
    const slot = document.createElement("div");
    slot.className = "minislot inset";
    sw.parentElement.appendChild(slot);
    attach(set, sw, sw.parentElement, slot);
  });
  tileToggles(root);
}

// ---------------------------------------------------------------- one look for every switch (design pass 27.10.2026)
// Every «switch + text» row becomes a tile like «Где учиться»: a 3D medal in the switch's own colours that lights up
// when on, a small category label, the switch in the corner, the scene and «Как среагирует» inside. Only the look
// changes: the switch keeps its id and its handler.
const TILE_LOOK = {
  secred: ["🕶️", "#6366f1", "#22d3ee", "Защита"],
  outred: ["🕶️", "#6366f1", "#22d3ee", "Защита"],
  secefs: ["🗄️", "#0ea5e9", "#22c55e", "Шифрование"],
  seccry: ["🔑", "#f59e0b", "#ef4444", "Шифрование"],
  memsw2: ["🧠", "#22c55e", "#14b8a6", "Память"],
  selfasksw: ["🙋", "#f59e0b", "#f97316", "Вопросы"],
  outsw: ["🔭", "#6366f1", "#a855f7", "Источники"],
  autos: ["🚀", "#0ea5e9", "#6366f1", "Запуск"],
  pauto: ["📒", "#f59e0b", "#eab308", "Рецепты"],
  actsw: ["🛠️", "#10b981", "#0ea5e9", "Файлы"],
  "actask-sw": ["✋", "#f97316", "#ef4444", "Файлы"],
  englow: ["🧘", "#22c55e", "#0ea5e9", "Компьютер"],
  scrkeep: ["🎧", "#ec4899", "#f97316", "Запись"],
};
function tileToggles(root) {
  const tiles = [];
  $$(".tg", root || document).forEach((tg) => {
    if (tg.classList.contains("stile") || tg.parentElement.closest(".tg, .srct")) return; // a switch inside a tile stays a row
    const sw = $(":scope > .sw", tg);
    if (!sw) return;
    const key = miniKey(sw),
      [em, c1, c2, tag] = TILE_LOOK[key] || ["⚙️", "#6366f1", "#a855f7", ""];
    tg.classList.add("srct", "stile");
    tg.style.setProperty("--c1", c1);
    tg.style.setProperty("--c2", c2);
    tg.insertAdjacentHTML(
      "afterbegin",
      `${tag ? `<span class="srctag">${esc(tr(tag))}</span>` : ""}<div class="medal2"><span>${em}</span><i class="spark"></i><i class="spark"></i><i class="spark"></i></div>`,
    );
    const sync = () => {
      tg.classList.toggle("on", sw.classList.contains("on"));
      tg.classList.toggle("off-dis", sw.disabled);
    };
    sync();
    new MutationObserver(sync).observe(sw, { attributes: true, attributeFilter: ["class", "disabled"] });
    tg.addEventListener("click", (e) => {
      if (e.target.closest("button, a, input, select, textarea, label, details")) return;
      sw.click(); // the whole tile switches, like «Где учиться»
    });
    tiles.push(tg);
  });
  // neighbours share one grid
  tiles.forEach((t) => {
    if (t.parentElement.classList.contains("stgrid")) return;
    const run = [t];
    let n = t.nextElementSibling;
    while (n && n.classList.contains("stile")) {
      run.push(n);
      n = n.nextElementSibling;
    }
    const grid = document.createElement("div");
    grid.className = "srcgrid stgrid" + (run.length === 1 ? " one" : "");
    t.before(grid);
    run.forEach((x) => grid.appendChild(x));
  });
}

// ---------------------------------------------------------------- one look for every «choose one of» row (design pass 27.10.2026)
// Every segmented choice in the settings becomes a row of small cards with the same 3D medal as the tiles: grey while
// not chosen, in its own colours when chosen. Only the look changes: the buttons keep their data and their handlers.
// A watcher dresses new rows too, so a card drawn again after a click keeps the look.
const SEG_GREY = ["#64748b", "#94a3b8"];
const SEG_AUTONOMY = {
  observe: ["👀", ...SEG_GREY],
  approve: ["🙋", "#f59e0b", "#f97316"],
  mixed: ["🎯", "#6366f1", "#a855f7"],
  quiet: ["🚀", "#10b981", "#22d3ee"],
};
const SEG_LOOK = {
  autonomy: SEG_AUTONOMY,
  brain: {
    auto: ["🧠", "#6366f1", "#a855f7"],
    none: ["✍️", ...SEG_GREY],
    local: ["💻", "#10b981", "#14b8a6"],
    claude_code: ["✳️", "#d97757", "#f0a37f"],
    api: ["🔑", "#f59e0b", "#eab308"],
    ollama: ["🦙", "#0ea5e9", "#6366f1"],
  },
  gender: { m: ["👨", "#0ea5e9", "#6366f1"], f: ["👩", "#ec4899", "#f97316"], "": ["🙂", ...SEG_GREY] },
  onclose: {
    ask: ["❓", "#6366f1", "#a855f7"],
    tray: ["📥", "#0ea5e9", "#22d3ee"],
    quit: ["🚪", "#ef4444", "#f97316"],
  },
  pmode: { off: ["💤", ...SEG_GREY], second: ["🔁", "#6366f1", "#a855f7"], every: ["📝", "#f59e0b", "#f97316"] },
  mode: {
    system: ["🖥️", "#0ea5e9", "#6366f1"],
    light: ["☀️", "#f59e0b", "#eab308"],
    dark: ["🌙", "#6366f1", "#334155"],
    custom: ["🎨", "#ec4899", "#a855f7"],
  },
  base: { light: ["☀️", "#f59e0b", "#eab308"], dark: ["🌙", "#6366f1", "#334155"] },
  tone: { warm: ["🔥", "#f97316", "#ef4444"], cool: ["❄️", "#0ea5e9", "#22d3ee"], neutral: ["⚪", ...SEG_GREY] },
  send: { enter: ["⏎", "#6366f1", "#a855f7"], ctrl: ["⌨️", "#0ea5e9", "#6366f1"] },
  pm: {
    system: ["🖥️", "#0ea5e9", "#6366f1"],
    off: ["➡️", ...SEG_GREY],
    http: ["🌐", "#10b981", "#0ea5e9"],
    socks5: ["🧦", "#f59e0b", "#f97316"],
  },
};
function segKey(sg) {
  const k = sg.dataset.seg || sg.dataset.cseg || sg.dataset.th || (sg.classList.contains("pxmode") ? "pm" : "");
  return k.startsWith("mode:") ? "autonomy" : k;
}
function segTiles(root) {
  $$(".seg", root || document).forEach((sg) => {
    if (sg.classList.contains("sm") || sg.dataset.pseg !== undefined || !sg.closest("#st, .modal")) return;
    const look = SEG_LOOK[segKey(sg)] || {};
    sg.classList.add("segt");
    const n = $$(":scope > button", sg).length;
    sg.style.setProperty("--n", n > 4 ? 3 : n);
    $$(":scope > button", sg).forEach((b, n) => {
      if (b.dataset.segt) return;
      b.dataset.segt = "1";
      const v = b.dataset.v !== undefined ? b.dataset.v : b.dataset.pm || "";
      const lk = look[v];
      b.style.setProperty("--d", `${n * 0.04}s`);
      b.innerHTML = `${lk ? `<span class="medal2 segm" style="--c1:${lk[1]};--c2:${lk[2]}"><span>${lk[0]}</span></span>` : ""}<span class="segl">${b.innerHTML}</span>`;
      if (lk) b.style.setProperty("--c1", lk[1]);
    });
    sg.classList.toggle("nomed", !$(".segm", sg));
  });
}
new MutationObserver((ms) => {
  for (const m of ms)
    for (const n of m.addedNodes)
      if (n.nodeType === 1 && (n.matches(".seg") || n.querySelector(".seg"))) segTiles(n.parentElement || n);
}).observe(document.documentElement, { childList: true, subtree: true });
