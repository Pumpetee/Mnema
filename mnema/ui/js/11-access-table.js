// ---------------------------------------------------------------- who sees what: one table, AIs across, memory parts down
const ACC_COLS = {
  local: ["💻", "#10b981", "на компьютере", "Встроенная модель и Ollama. Ничего не уходит в интернет"],
  claude: ["✳", "#d97757", "облако", "Чат Mnema с Claude (подписка или ключ) и Claude Code через MCP"],
  chatgpt: ["◎", "#10a37f", "облако", "Чат Mnema с ключом OpenAI и расширение в ChatGPT"],
  gemini: ["✦", "#4f7cf7", "облако", "Чат Mnema с ключом Gemini и расширение в Gemini"],
  openrouter: ["⇄", "#7c5cf0", "облако", "Чат Mnema через OpenRouter — любые модели по одному ключу"],
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
function accMatrix(cl) {
  const head = `<div class="ach0"></div>${cl
    .map((c, i) => {
      const v = ACC_COLS[c.id] || ["•", "#64748b", "облако", ""];
      return `<div class="acch ${c.enabled ? "" : "off"}" style="--ac:${v[1]}" title="${esc(tr(v[3]))}">
     <span class="acb">${v[0]}</span><b>${esc(tr(c.name))}</b><small class="${c.id === "local" ? "loc" : ""}">${tr(v[2])}</small>
     <button class="sw sm ${c.enabled ? "on" : ""}" data-acc="enabled" data-ci="${i}" title="${tr(c.enabled ? "Получает память" : "Не получает ничего")}"></button></div>`;
    })
    .join("")}`;
  const row = (k, icn, t, d, cells, cls = "") =>
    `<div class="accl ${cls}"><span class="ai ${ACC_DENY.some((x) => x[0] === k) ? "dn" : ""}">${ic(icn)}</span><div><b>${tr(t)}</b><small>${tr(d)}</small></div></div>${cells}`;
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
          return `<button class="accd ${hid ? "hid" : ""} ${c.enabled ? "" : "dis"}" data-acc="deny" data-k="${k}" data-ci="${i}" title="${tr(hid ? "Вырезается" : "Уходит, если часть памяти разрешена")}">${hid ? ic("lock") + "<b>" + tr("скрыто") + "</b>" : "<em>" + tr("видно") + "</em>"}</button>`;
        })
        .join(""),
    ),
  ).join("");
  const wr = row(
    "w",
    "edit",
    "Может дописывать",
    "кладёт новое во входящие, ты разбираешь",
    cl
      .map(
        (c, i) =>
          `<button class="accc w ${c.can_write ? "on" : ""} ${c.enabled ? "" : "dis"}" style="--ac:${(ACC_COLS[c.id] || [0, "#64748b"])[1]}" data-acc="write" data-ci="${i}"><i>${c.can_write ? ic("check") : ""}</i></button>`,
      )
      .join(""),
  );
  const foot = `<div class="accl ft"></div>${cl.map((c) => `<div class="accf">${c.enabled ? `${ACC_ROWS.filter((r) => c.scopes.includes(r[0])).length}/${ACC_ROWS.length}` : "—"}</div>`).join("")}`;
  return `<div class="accm" style="--n:${cl.length}">${head}<div class="accsep">${tr("Что видит")}</div>${sc}<div class="accsep">${tr("Вырезать даже из разрешённого")}</div>${dn}<div class="accsep">${tr("Запись")}</div>${wr}${foot}</div>`;
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
    else if (what === "write") {
      c.can_write = !c.can_write;
      if (c.can_write && !(c.write_scopes || []).length) c.write_scopes = ["inbox"];
    } else c.enabled = !c.enabled;
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
