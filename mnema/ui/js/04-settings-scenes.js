// ---------------------------------------------------------------- settings: sections and exact links
// #settings/<section>/<block id> opens the section, scrolls to the block and lights it up. Every button that leads
// into the settings uses such a link (goSet), so it lands exactly where it promised.
const SETSECS = [
  ["ai", "chat", "ИИ и модели"],
  ["style", "edit", "Как отвечает"],
  ["learn", "book", "Обучение"],
  ["security", "shield", "Безопасность"],
  ["engine", "gear", "Движок"],
  ["meetings", "users", "Встречи"],
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
  Безопасность: "security/seccard",
  "Локальная модель": "ai/c-local",
  "Подключить другую модель": "ai/c-prov",
  Прокси: "app/netcard",
  "VPN и прокси": "app/netcard",
  "ИИ и модели": "ai/c-prov",
};
function linkSettings(html) {
  return html.replace(
    /Настройки → (Движок|Встречи|Безопасность|Локальная модель|Подключить другую модель|VPN и прокси|Прокси|ИИ и модели)/g,
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
  ecosw: {
    f: ["file", "150 000 знаков"],
    t: ["chat", "Модель"],
    on: ["7 000", "go"],
    off: ["150 000", "raw"],
    re: "длинные документы и память",
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
  ecosw: ["Модели — только нужное", "Модели — всё целиком"],
  autos: ["Учится в фоне с запуска", "Ждёт, пока откроешь"],
  pauto: ["Узнала задачу — готовит по рецепту", "Рецепты сама не берёт"],
  englow: ["Окна и браузер не тормозят", "Модель берёт всё, что может"],
};
// ---------------------------------------------------------------- every switch: its own little scene + how Mnema reacts
// [scene, data, reaction when on, reaction when off]
const MR = {
  ty: ["swap", { ctx: "Давай начнём", a: "Вы", b: "ты" }, "Обращается на «ты»", "Обращается на «вы»"],
  equals: [
    "tone",
    { a: "Позвольте объяснить…", b: "Ошибка в формуле." },
    "Говорит прямо, как с равным",
    "Вежливо и с оговорками",
  ],
  length: [
    "shrink",
    { n: 5, b: "Готово: report.pdf" },
    "Отвечает 1–3 строками на простое",
    "Пишет столько, сколько получится",
  ],
  no_process: [
    "shrink",
    { n: 4, b: "Итог: 3 расхождения", tag: "шаги" },
    "Сразу результат, без рассказа о шагах",
    "Рассказывает, как работал",
  ],
  not_doc: ["format", { to: "list" }, "Длинное — с подзаголовками и списками", "Сплошной текст"],
  form: [
    "format",
    { to: "num", a: "Стоимость зависит от…", b: "4 900 ₽" },
    "Отвечает в той форме, что просили",
    "Форма — на усмотрение ИИ",
  ],
  plain: [
    "swap",
    { ctx: "Сервер:", a: "OOMKilled", b: "не хватило памяти" },
    "Без жаргона и сокращений",
    "Может писать техническим языком",
  ],
  result_only: [
    "swap",
    { ctx: "База:", a: "B-tree, ANALYZE", b: "поиск быстрее" },
    "В незнакомой теме — только итог",
    "Объясняет детали",
  ],
  no_stamps: ["strike", { w: "Отличный вопрос!", r: "Ошибка в строке 14." }, "Убирает штампы", "Штампы возможны"],
  no_tail: [
    "strike",
    { w: "Хочешь, сделаю график?", r: "Итог: 120.", end: 1 },
    "Не навязывает следующие шаги",
    "Предлагает «а ещё сделаю…»",
  ],
  important: ["pin", { t: "Штраф 1% в день" }, "Выносит главное под «Реально важно»", "Всё одним потоком"],
  quotes: [
    "swap",
    { ctx: "Заголовок:", a: "«Продукт»", b: '"Продукт"' },
    "Простые кавычки, без «;»",
    "Типографские «ёлочки»",
  ],
  humor: ["strike", { w: "😄 цифры в прятки", r: "Дубль в строке 12." }, "Шутит редко и к месту", "Может шутить"],
  no_condescend: [
    "strike",
    { w: "Снова спрашиваешь…", r: "Файл в папке Docs." },
    "Без «снова» и «опять»",
    "Тон не контролируется",
  ],
  small_now: ["gate", { q: "Уточни язык?", r: "Memory." }, "Мелкое делает сразу", "Уточняет даже мелочи"],
  big_plan: ["steps", { l: ["План", "Ок?", "Делаю"], ask: 1 }, "Крупное: сначала план и «ок?»", "Сразу берётся делать"],
  ask_when: [
    "gate",
    { q: "Оттенок? Шрифт? Размер?", r: "Шапка синяя." },
    "Спрашивает, только если без ответа никак",
    "Задаёт много вопросов",
  ],
  ask_options: [
    "buttons",
    { q: "Какой тон?", o: ["Официально", "Дружески"] },
    "Вопрос — кнопками с вариантами",
    "Вопрос — списком в тексте",
  ],
  thorough: [
    "steps",
    { l: ["Факты", "Цифры", "Ответ"], check: 1 },
    "Проверяет перед ответом",
    "Отвечает быстрее, без проверки",
  ],
  analogy: ["copy", {}, "Делает по образцу того, что работает", "Изобретает заново"],
  whole_class: [
    "scan",
    { n: 5, hits: [1, 2, 4], label: "+4 таких же" },
    "Исправляет все похожие места",
    "Только то, на что показал",
  ],
  second_order: ["warn", { t: "Риск: пропадёт история" }, "Сам называет риски", "Риски — если спросишь"],
  stepwise: ["steps", { l: ["Шаг 1", "Шаг 2", "Шаг 3"], seq: 1 }, "Крупное — по шагам с проверкой", "Всё разом"],
  only_asked: [
    "shrink",
    { n: 4, b: "Исправил опечатку", tag: "+ абзац" },
    "Ровно то, что просили",
    "Может добавить лишнее",
  ],
  no_disclaimers: [
    "strike",
    { w: "Я не юрист, но…", r: "Можно оформить вычет." },
    "Без оговорок и дисклеймеров",
    "С оговорками",
  ],
  no_refs: ["strike", { w: "Согласно п. 4.2", r: "10 дней." }, "Без отсылок к источнику", "Ссылается на пункты"],
  no_captions: [
    "strike",
    { w: "(нажмите, чтобы купить)", r: "«Купить»", end: 1 },
    "Без лишних подписей",
    "С пояснениями",
  ],
  no_invent: [
    "num",
    { a: "≈ 50 млн", b: "не знаю — проверю", bad: 1 },
    "Не знает — так и скажет",
    "Может додумать цифру",
  ],
  estimate: ["num", { a: "2 недели", b: "≈2 нед. · оценка" }, "Оценку помечает и объясняет", "Оценка звучит как факт"],
  memory_first: ["memo", { q: "Где живу?", a: "Казань" }, "Сверяется с памятью", "Отвечает по догадке"],
  basis: ["num", { a: "4%", b: "4% · окт, 1 200" }, "Цифра — с основанием", "Просто цифра"],
  exact: ["num", { a: "≈ 42 тыс.", b: "41 860 ₽" }, "Точно, без округлений", "Округляет на глаз"],
  artifact: ["steps", { l: ["Файл", "3 стр.", "Сверено"], check: 1 }, "Отчёт — с подтверждением", "«Всё сделал»"],
  stale: ["memo", { q: "Пилот?", a: "статус 01.08", old: 1 }, "Старый статус — переспрашивает", "Верит старым данным"],
  say_early: ["warn", { t: "Это единственная копия!" }, "Видит ошибку — говорит до работы", "Делает молча"],
  no_circle: ["loop", {}, "Настоял — делает, не спорит", "Может спорить по кругу"],
  bad_news: [
    "swap",
    { ctx: "Сайт:", a: "упал", b: "починил: сертификат" },
    "Плохая новость — сразу с решением",
    "Сообщает только проблему",
  ],
  own_error: [
    "shrink",
    { n: 4, b: "Ошибся в столбце. Верно: 1 240", tag: "извинения" },
    "Ошибку признаёт коротко",
    "Долго извиняется",
  ],
  explain_diff: [
    "swap",
    { ctx: "Было 10, стало 7:", a: "извините", b: "3 дубля убраны" },
    "Объясняет причину и цифрами",
    "Просто извиняется",
  ],
  chk_answer: [
    "scan",
    { n: 4, hits: [3], label: "ответ на вопрос" },
    "Проверяет, что ответил на вопрос",
    "Без проверки",
  ],
  chk_form: ["format", { to: "table" }, "Сверяет форму с просьбой", "Форма может не совпасть"],
  chk_memory: ["memo", { q: "Мой тариф?", a: "«Про»" }, "Сверяет факты с памятью", "Без сверки"],
  chk_invented: ["scan", { n: 4, hits: [2], label: "выдумка убрана", bad: 1 }, "Убирает выдуманное", "Без проверки"],
  second_pass: [
    "scan",
    { n: 5, hits: [0, 1, 2, 3, 4], label: "перепроверено", all: 1 },
    "Перечитывает ответ перед отправкой",
    "Отправляет сразу",
  ],
  say_saved: ["save", { t: "Живёт в Казани", tag: "запомню" }, "Отмечает новое для памяти", "Молча"],
  one_fact: ["save", { t: "Пилот — 4 компании", tag: "статус 20.10" }, "Факт — одной строкой с датой", "Как получится"],
  guess_mark: ["save", { t: "Не любит поездки", tag: "предп." }, "Догадку помечает «(предп.)»", "Догадка как факт"],
  thought_capture: ["save", { t: "Сделать бота", tag: "идея", idea: 1 }, "Идеи выделяет отдельно", "Идеи теряются"],
  private_out: [
    "hide",
    { t: "Сдвигаем срок", h: "здоровье" },
    "Личное не уходит другим людям",
    "Может упомянуть личное",
  ],
  his_voice: [
    "tone",
    { a: "Уважаемый клиент…", b: "Привет! Успеваем." },
    "Пишет от тебя твоим голосом",
    "Официальный тон",
  ],
  no_secrets: ["hide", { t: "Пароль:", h: "qwerty123", pw: 1 }, "Пароли и ключи не повторяет", "Может повторить"],
  one_line_par: ["doc", {}, "Абзац — одной строкой", "Ручные переносы"],
  tables: ["format", { to: "table" }, "Сравнения — таблицей", "Простынёй текста"],
  self_check: [
    "scan",
    { n: 4, hits: [1], label: "[ИМЯ] заполнено" },
    "Проверяет документ перед сдачей",
    "Без проверки",
  ],
  short_pdf: [
    "shrink",
    { n: 6, b: "2 страницы, суть", tag: "12 стр." },
    "Внешние документы — коротко",
    "Сколько получится",
  ],
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
    return `<div class="ms pin ${O}"><i class="ln"></i><i class="ln"></i><div class="card2"><span class="lab">Реально важно</span>${esc(d.t)}</div><i class="ln"></i></div>`;
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
}
