const $ = (s, r = document) => r.querySelector(s),
  $$ = (s, r = document) => [...r.querySelectorAll(s)];
const esc = (s) =>
  String(s ?? "").replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" })[c]);
const ic = (n, c = "") => `<svg class="i ${c}"><use href="#i-${n}"/></svg>`;
async function api(path, opt = {}) {
  const r = await fetch(path, { ...opt, headers: { "X-Mnema-Token": TOKEN, "Content-Type": "application/json" } });
  let d = {};
  try {
    d = await r.json();
  } catch (e) {}
  if (r.status === 423 && d.locked) unlockScreen(); // encrypted memory, the password not given yet
  if (!r.ok) throw new Error(d.error || "ошибка " + r.status);
  return d;
}

// the memory folder is encrypted by Mnema: the password before anything else
function unlockScreen() {
  if ($(".unlock")) return;
  hideSplash();
  const pop = document.createElement("div");
  pop.className = "modal unlock";
  pop.innerHTML = `<div class="card"><div class="unlockic">${ic("lock")}</div><h2>${tr("Память зашифрована")}</h2><p class="hint">${tr("Введи пароль, который ты задал при шифровании.")}</p>
    <input type="password" id="ulpw" autocomplete="current-password" placeholder="${tr("Пароль")}">
    <label class="ulrem"><input type="checkbox" id="ulrem"> ${tr("Помнить на этом компьютере")}</label>
    <div class="ulerr" id="ulerr"></div>
    <div class="row" style="justify-content:flex-end;margin-top:12px"><button class="btn" id="ulgo">${tr("Открыть")}</button></div></div>`;
  document.body.appendChild(pop);
  const go = async () => {
    const pw = $("#ulpw").value;
    if (!pw) return;
    $("#ulgo").disabled = true;
    $("#ulerr").textContent = "";
    try {
      await post("/api/crypto", { action: "unlock", password: pw, remember: $("#ulrem").checked });
      location.reload();
    } catch (e) {
      $("#ulerr").textContent = e.message;
      $("#ulgo").disabled = false;
      $("#ulpw").select();
    }
  };
  $("#ulgo").onclick = go;
  $("#ulpw").onkeydown = (e) => e.key === "Enter" && go();
  setTimeout(() => $("#ulpw").focus(), 50);
}
const post = (p, b) => api(p, { method: "POST", body: JSON.stringify(b || {}) });
const _confirm = window.confirm.bind(window);
window.confirm = (t) => _confirm(tr(t));
const _prompt = window.prompt.bind(window);
window.prompt = (t, d) => _prompt(tr(t), d);
function toast(t, ms) {
  const e = $("#toast");
  e.textContent = t;
  e.classList.add("on");
  clearTimeout(e._t);
  e._t = setTimeout(() => e.classList.remove("on"), ms || 2600);
}
const LS = {
  get: (k, d) => {
    try {
      const v = localStorage.getItem("mn_" + k);
      return v === null ? d : JSON.parse(v);
    } catch (e) {
      return d;
    }
  },
  set: (k, v) => {
    try {
      localStorage.setItem("mn_" + k, JSON.stringify(v));
    } catch (e) {}
  },
};
let APP = { desktop: false };
function closeMenus() {
  $$(".menu").forEach((m) => m.remove());
}
let MENU_ANCHOR = null;
document.addEventListener("click", (e) => {
  if (e.target.closest(".menu") || e.target.closest(".pop") || (MENU_ANCHOR && MENU_ANCHOR.contains(e.target))) return;
  closeMenus();
  const p = $(".pop");
  if (p) p.remove();
});
function menu(anchor, items) {
  closeMenus();
  MENU_ANCHOR = anchor;
  const m = document.createElement("div");
  m.className = "menu";
  m.innerHTML = items
    .map((it, i) =>
      it === "-"
        ? "<hr>"
        : `<button data-k="${i}" class="${it.danger ? "danger" : ""}">${it.icon ? ic(it.icon) : ""}${esc(it.label)}${it.check !== undefined ? `<span class="chk ${it.check ? "on" : ""}">${it.check ? "✓" : ""}</span>` : ""}</button>`,
    )
    .join("");
  document.body.appendChild(m);
  const r = anchor.getBoundingClientRect();
  const w = m.offsetWidth,
    h = m.offsetHeight;
  m.style.left = Math.min(window.innerWidth - w - 8, Math.max(8, r.right - w)) + "px";
  m.style.top = (r.bottom + h + 8 > window.innerHeight ? r.top - h - 6 : r.bottom + 6) + "px";
  $$("button", m).forEach(
    (b) =>
      (b.onclick = () => {
        closeMenus();
        items[+b.dataset.k].run();
      }),
  );
}
// the start screen with the logo: stays at least 1.4 s so the animation plays out, then fades
function hideSplash() {
  const sp = document.getElementById("splash");
  if (!sp || sp.dataset.out) return;
  sp.dataset.out = "1";
  setTimeout(
    () => {
      sp.classList.add("out");
      setTimeout(() => sp.remove(), 500);
    },
    Math.max(0, 1400 - performance.now()),
  );
}

// ---------------------------------------------------------------- memory on / off
// Off: the AIs get no memory and Mnema writes nothing — a plain chat; every other function stays. A new memory folder
// starts off and the tour offers to turn it on.
const MEM = { on: true, asked: true };
async function memSet(on, quiet) {
  await post("/api/agent", { memory_on: !!on, memory_asked: true });
  MEM.on = !!on;
  MEM.asked = true;
  if (!quiet)
    toast(
      on
        ? tr("Память включена: ИИ знают тебя, Mnema учится")
        : tr("Память выключена: обычный чат, ничего не запоминается"),
    );
  document.body.classList.toggle("mem-off", !MEM.on);
  if (typeof refreshStatus === "function") refreshStatus();
  const [v, ...a] = location.hash.slice(1).split("/");
  if (v === "memory" || v === "settings") go(v, a.join("/"));
  else if (typeof drawChips === "function") drawChips();
}
function memOffNote(what) {
  return `<div class="memoffnote">${ic("eyeoff")}<span>${tr("Память выключена")} — ${tr(what)}</span><button class="btn sm" data-memon>${tr("Включить")}</button></div>`;
}
document.addEventListener("click", (e) => {
  const b = e.target.closest("[data-memon]");
  if (b) {
    e.preventDefault();
    memSet(true);
  }
});
