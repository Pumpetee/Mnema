// ---------------------------------------------------------------- heat: how hard the local model works this computer
const HEAT_RU = { idle: "Модель не запущена", cool: "Спокойно", warm: "Греется", hot: "Перегрев" };
function fitTitle() {
  const t = $(".top"),
    c = $(".tcenter");
  if (!t || !c) return;
  const tr = t.getBoundingClientRect(),
    h = $("#heat"),
    edge = (h && !h.hidden ? h : $("#model")).getBoundingClientRect().right;
  const mid = tr.left + tr.width / 2,
    trc = $("#trc"),
    right = trc ? trc.getBoundingClientRect().left : tr.right;
  const half = Math.min(mid - edge, right - mid) - 20;
  c.style.maxWidth = Math.max(80, 2 * half) + "px";
}
addEventListener("resize", () => fitTitle());
function heatShow() {
  setTimeout(fitTitle, 0);
  const b = $("#heat");
  if (!b) return false;
  const loc = (r) => /^(local|ollama):/.test(String(r || ""));
  const local = CHAT.cons ? CHAT.cons.members.some(loc) : loc(CHAT.model);
  b.hidden = !local;
  return local;
}
const HEAT = { running: false, last: null };
async function heatPoll() {
  if (!heatShow() && !$("#heat")) return;
  try {
    const d = await api("/api/local/heat");
    HEAT.running = d.running;
    HEAT.last = d;
    const b = $("#heat");
    if (!b) return;
    heatShow();
    b.dataset.level = d.level;
    b.title = HEAT_RU[d.level] + (d.running ? " · " + d.why : "");
    if ($(".heatpop")) heatPopFill($(".heatpop"), d);
  } catch (e) {}
}
setInterval(heatPoll, 3000);
function heatPopFill(m, d) {
  const bar = (v, t) =>
    `<div class="hrow"><span>${t}</span><i><b style="width:${Math.min(100, v || 0)}%" class="${v >= 90 ? "hot" : v >= 70 ? "warm" : ""}"></b></i><em>${v == null ? "—" : v + "%"}</em></div>`;
  m.innerHTML = `<div class="hhead lv-${d.level}"><span class="hic">${ic("thermo")}</span><div><b>${tr(HEAT_RU[d.level])}</b><small>${esc(tr(d.why))}</small></div></div>
   ${bar(d.cpu, tr("Процессор"))}${bar(d.model_cpu, tr("Из них модель"))}${bar(d.ram, tr("Память"))}
   <div class="hrow"><span>${tr("Температура")}</span><em class="wide">${d.temp != null ? d.temp + " °C" : tr("Windows не сообщает")}</em></div>
   ${d.auto_cooled ? `<div class="hnote">${tr("Перегрев держался минуту — Mnemai сама снизила приоритет модели, окна не тормозят.")}</div>` : ""}
   <div class="hacts"><button class="btn l sm" data-hc="cool" ${d.running ? "" : "disabled"}>${tr("Снизить нагрузку")}</button><button class="btn g sm" data-hc="stop" ${d.running ? "" : "disabled"}>${tr("Остановить модель")}</button></div>`;
  $$("[data-hc]", m).forEach(
    (x) =>
      (x.onclick = async () => {
        x.disabled = true;
        try {
          const r = await post("/api/local/" + x.dataset.hc, {});
          toast(
            x.dataset.hc === "cool"
              ? tr("Модель возьмёт вдвое меньше ядер со следующего сообщения")
              : tr("Модель остановлена, память освобождена"),
          );
          heatPopFill(m, r);
        } catch (e) {
          toast(e.message);
        }
      }),
  );
}
function heatMenu(anchor) {
  if ($(".heatpop")) {
    $(".heatpop").remove();
    return;
  }
  closeMenus();
  MENU_ANCHOR = anchor;
  const m = document.createElement("div");
  m.className = "menu heatpop";
  document.body.appendChild(m);
  heatPopFill(m, HEAT.last || { level: "idle", why: "", cpu: 0, model_cpu: 0, ram: 0, temp: null, running: false });
  const r = anchor.getBoundingClientRect();
  m.style.left = Math.max(8, Math.min(innerWidth - m.offsetWidth - 8, r.left)) + "px";
  m.style.top = r.bottom + 8 + "px";
  heatPoll();
}
// learning sources: each has its own medal, like the achievements
const SRC_LOOK = {
  mnema_chat: ["💬", "#6d5ff5", "#4fb6ff", "Учится, пока ты пишешь"],
  claude_code: ["🤖", "#d97757", "#f2b38f", "Читает новые разговоры"],
  browser: ["🧩", "#10a37f", "#7fd4b6", "Учится в ChatGPT и Gemini"],
  telegram_api: ["✈️", "#229ed9", "#7cc8ee", "Читает твои сообщения"],
  chatgpt_export: ["📦", "#0f766e", "#5eead4", "Разберёт выгрузку"],
  corrections: ["✏️", "#e11d48", "#fda4af", "Превращает поправки в правила"],
  notes: ["📝", "#ca8a04", "#fde047", "Читает новые заметки"],
  mail: ["✉️", "#2563eb", "#93c5fd", "Читает отправленные письма"],
  telegram: ["✈️", "#0ea5e9", "#7dd3fc", "Разберёт выгрузку Telegram"],
  calendar: ["📅", "#dc2626", "#fca5a5", "Видит регулярные встречи"],
  documents: ["📄", "#475569", "#cbd5e1", "Читает новые документы"],
  browser_history: ["🔎", "#7c3aed", "#c4b5fd", "Замечает устойчивые интересы"],
};
