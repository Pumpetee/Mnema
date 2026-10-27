// ---------------------------------------------------------------- who sees what: one table, AIs across, memory parts down
const ACC_COLS = {
  local: ["💻", "#10b981", "на компьютере", "Встроенная модель и Ollama. Ничего не уходит в интернет"],
  claude: ["✳", "#d97757", "облако", "Чат Mnema с Claude (подписка или ключ) и Claude Code через MCP"],
  chatgpt: ["◎", "#10a37f", "облако", "Чат Mnema с ключом OpenAI"],
  gemini: ["✦", "#4f7cf7", "облако", "Чат Mnema с ключом Gemini"],
  openrouter: ["⇄", "#7c5cf0", "облако", "Чат Mnema через OpenRouter — любые модели по одному ключу"],
  deepseek: ["🐋", "#4d6bfe", "облако", "Чат Mnema с ключом DeepSeek"],
  yandex: ["Я", "#fc3f1d", "облако", "Чат Mnema с YandexGPT через Yandex Cloud"],
  cursor: ["▲", "#334155", "облако", "Cursor через MCP"],
};
const ACC_ROWS = [
  ["profile", "user", "Обо мне", "имя, кто ты, как с тобой говорить"],
  ["rules", "list", "Правила", "как отвечать и чего не делать"],
  ["projects", "folder", "Проекты", "активные проекты и их цели"],
  ["cards", "cards", "Карточки", "темы: работа, дом, здоровье…"],
  ["people", "users", "Люди", "кто есть кто"],
  ["decisions", "pin", "События и решения", "что решили и когда"],
  ["inbox", "inbox", "Входящие", "ещё не разобранное"],
];
const ACC_DENY = [
  ["money", "coin", "Деньги", "карточка Деньги и всё с #money"],
  ["health", "heart", "Здоровье", "карточка Здоровье и всё с #health"],
  ["private", "eyeoff", "Личное", "карточка Личное и всё с #private"],
];
// the row medals: lit while at least one AI gets this part (or, for the cut topics, while it is cut from someone)
const ACC_MED = {
  profile: ["👤", "#6366f1", "#a855f7"],
  rules: ["📋", "#0ea5e9", "#6366f1"],
  projects: ["🗂️", "#f59e0b", "#f97316"],
  cards: ["🗃️", "#10b981", "#14b8a6"],
  people: ["👥", "#ec4899", "#a855f7"],
  decisions: ["📌", "#ef4444", "#f97316"],
  inbox: ["📥", "#0ea5e9", "#22d3ee"],
  money: ["💰", "#ef4444", "#f97316"],
  health: ["❤️", "#ef4444", "#ec4899"],
  private: ["🕶️", "#ef4444", "#a855f7"],
};
function accMatrix(cl) {
  const head = `<div class="ach0"></div>${cl
    .map((c, i) => {
      const v = ACC_COLS[c.id] || ["•", "#64748b", "облако", ""];
      return `<div class="acch ${c.enabled ? "" : "off"}" style="--ac:${v[1]}" title="${esc(tr(v[3]))}">
     <span class="acb">${v[0]}</span><b>${esc(tr(c.name))}</b><small class="${c.id === "local" ? "loc" : ""}">${tr(v[2])}</small>
     <button class="sw sm ${c.enabled ? "on" : ""}" data-acc="enabled" data-ci="${i}" title="${tr(c.enabled ? "Получает память" : "Не получает ничего")}"></button></div>`;
    })
    .join("")}`;
  const row = (k, icn, t, d, cells, cls = "") => {
    const [em, c1, c2] = ACC_MED[k] || ["•", "#64748b", "#94a3b8"],
      deny = ACC_DENY.some((x) => x[0] === k),
      lit = cl.some((c) => c.enabled && (deny ? c.deny_tags.includes(k) : c.scopes.includes(k)));
    return `<div class="accl ${cls}"><span class="medal2 accmd ${lit ? "lit" : ""}" style="--c1:${c1};--c2:${c2}"><span>${em}</span></span><div><b>${tr(t)}</b><small>${tr(d)}</small></div></div>${cells}`;
  };
  const sc = ACC_ROWS.map(([k, icn, t, d]) =>
    row(
      k,
      icn,
      t,
      d,
      cl
        .map((c, i) => {
          const on = c.scopes.includes(k);
          return `<button class="accc ${on ? "on" : ""} ${c.enabled ? "" : "dis"}" style="--ac:${(ACC_COLS[c.id] || [0, "#64748b"])[1]}" data-acc="scope" data-k="${k}" data-ci="${i}" title="${tr(on ? "Видит" : "Не видит")}"><i>${on ? ic("check") : ""}</i></button>`;
        })
        .join(""),
    ),
  ).join("");
  const dn = ACC_DENY.map(([k, icn, t, d]) =>
    row(
      k,
      icn,
      t,
      d,
      cl
        .map((c, i) => {
          const hid = c.deny_tags.includes(k);
          return `<button class="accd ${hid ? "hid" : ""} ${c.enabled ? "" : "dis"}" data-acc="deny" data-k="${k}" data-ci="${i}" title="${tr(hid ? "Вырезается" : "Уходит, если часть памяти разрешена")}">${hid ? ic("lock") + "<b>" + tr("скрыто") + "</b>" : ic("eye") + "<em>" + tr("видно") + "</em>"}</button>`;
        })
        .join(""),
    ),
  ).join("");
  const foot = `<div class="accl ft"></div>${cl.map((c) => `<div class="accf">${c.enabled ? `${ACC_ROWS.filter((r) => c.scopes.includes(r[0])).length}/${ACC_ROWS.length}` : "—"}</div>`).join("")}`;
  return `<div class="accm" style="--n:${cl.length}">${head}<div class="accsep">${tr("Что видит")}</div>${sc}<div class="accsep">${tr("Вырезать даже из разрешённого")}</div>${dn}${foot}</div>`;
}
function bindAcc(cl) {
  const box = $("#accm");
  if (!box) return;
  box.onclick = async (e) => {
    const b = e.target.closest("[data-acc]");
    if (!b) return;
    const c = cl[+b.dataset.ci],
      k = b.dataset.k,
      what = b.dataset.acc;
    if (what === "scope") c.scopes = c.scopes.includes(k) ? c.scopes.filter((x) => x !== k) : [...c.scopes, k];
    else if (what === "deny")
      c.deny_tags = c.deny_tags.includes(k) ? c.deny_tags.filter((x) => x !== k) : [...c.deny_tags, k];
    else c.enabled = !c.enabled;
    const sel = `[data-acc="${what}"][data-ci="${b.dataset.ci}"]` + (k ? `[data-k="${k}"]` : "");
    box.innerHTML = accMatrix(cl);
    const nb = $(sel, box);
    if (nb) nb.classList.add("bump");
    try {
      await post("/api/clients", cl);
      const t = $("#accsaved");
      t.classList.remove("show");
      void t.offsetWidth;
      t.classList.add("show");
    } catch (err) {
      toast(err.message);
    }
  };
}
