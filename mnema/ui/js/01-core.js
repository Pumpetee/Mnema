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
  if (!r.ok) throw new Error((ERRS.last = d.error || "ошибка " + r.status));
  return d;
}

// the memory folder is encrypted by Mnemai: the password before anything else
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
// the last error the server answered with: a notification showing it is marked as an error, not as done
const ERRS = { last: "" };
function toast(t, ms) {
  const e = $("#toast");
  const bad = !!t && (t === ERRS.last || t instanceof Error);
  e.innerHTML = '<i class="tmark"></i><span></span>';
  e.lastChild.textContent = String(t && t.message ? t.message : t);
  e.classList.toggle("bad", bad);
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
// Off: the AIs get no memory and Mnemai writes nothing — a plain chat; every other function stays. A new memory folder
// starts off and the tour offers to turn it on.
const MEM = { on: true, asked: true };
// Turning the memory on is never one stray click: every switch and button asks first, with what it means.
// quiet — the choice was already made in such a window (or in the first-run tour).
// Mnemai's own dialogs instead of the browser's confirm / prompt (those show «Сообщение с 127.0.0.1»):
// ask(title, text, ok, danger) → true / false, askText(title, value, text) → the text or null
function dlg({ title, text = "", ok = "OK", danger = false, input = null, placeholder = "", wait = 0 }) {
  return new Promise((done) => {
    const pop = document.createElement("div");
    pop.className = "modal mdlg";
    pop.innerHTML = `<div class="card" role="dialog" aria-modal="true">${danger ? `<span class="mdlgi">${ic("trash")}</span>` : ""}<h2>${esc(tr(title))}</h2>${text ? `<p class="hint">${esc(tr(text))}</p>` : ""}${input !== null ? `<input class="inp" data-v placeholder="${esc(tr(placeholder))}">` : ""}${wait > 0 ? `<div class="mdlgwait" style="--t:${wait}s"><i></i><span></span></div>` : ""}
      <div class="row mdlgb"><button class="btn g" data-no>${tr("Отмена")}</button><button class="btn ${danger ? "red" : ""}" data-yes>${esc(tr(ok))}</button></div></div>`;
    const inp = $("[data-v]", pop),
      okb = $("[data-yes]", pop);
    if (inp) inp.value = input;
    let timer = 0;
    if (wait > 0) {
      // the button wakes up only after a pause: time to read what is about to be deleted
      let left = wait;
      const note = $(".mdlgwait span", pop),
        tick = () => {
          okb.textContent = `${tr(ok)} · ${left}`;
          note.textContent = `${tr("Кнопка проснётся через")} ${left} ${tr("с")}`;
        };
      okb.disabled = true;
      tick();
      timer = setInterval(() => {
        left -= 1;
        if (left > 0) return tick();
        clearInterval(timer);
        okb.disabled = false;
        okb.textContent = tr(ok);
        note.textContent = tr("Теперь можно");
        $(".mdlgwait", pop).classList.add("done");
      }, 1000);
    }
    const close = (v) => {
      clearInterval(timer);
      document.removeEventListener("keydown", key, true);
      pop.remove();
      done(v);
    };
    const yes = () => {
      if (okb.disabled) return;
      if (!inp) return close(true);
      const v = inp.value.trim();
      if (!v) return inp.focus();
      close(v);
    };
    const key = (e) => {
      if (e.key === "Escape") {
        e.stopPropagation();
        close(inp ? null : false);
      } else if (e.key === "Enter") {
        e.preventDefault();
        e.stopPropagation();
        yes();
      }
    };
    document.addEventListener("keydown", key, true);
    $("[data-no]", pop).onclick = () => close(inp ? null : false);
    $("[data-yes]", pop).onclick = yes;
    pop.onclick = (e) => e.target === pop && close(inp ? null : false);
    document.body.appendChild(pop);
    if (inp) {
      inp.focus();
      inp.select();
    } else if (wait > 0) $("[data-no]", pop).focus();
    else okb.focus();
  });
}
const ask = (title, text = "", ok = "Удалить", danger = true) => dlg({ title, text, ok, danger });
const askText = (title, value = "", text = "", placeholder = "") =>
  dlg({ title, text, ok: "Сохранить", input: value || "", placeholder });
function memConfirm() {
  return new Promise((done) => {
    const pop = document.createElement("div");
    pop.className = "modal memask";
    pop.innerHTML = `<div class="card"><h2>${tr("Включить память?")}</h2>
      <p class="hint">${tr("ИИ будут знать о тебе то, что разрешено в «Кто из ИИ что видит». Mnemai начнёт учиться на разговорах и записывать факты в папку на этом компьютере.")}</p>
      <p class="hint">${tr("Выключить можно в любой момент тем же переключателем. Всё записанное видно в «Память» → «История», любую запись можно откатить.")}</p>
      <div class="row" style="justify-content:flex-end;margin-top:14px;gap:8px"><button class="btn g" data-no>${tr("Не включать")}</button><button class="btn" data-yes>${tr("Включить память")}</button></div></div>`;
    const close = (v) => {
      pop.remove();
      done(v);
    };
    $("[data-no]", pop).onclick = () => close(false);
    $("[data-yes]", pop).onclick = () => close(true);
    pop.onclick = (e) => e.target === pop && close(false);
    document.body.appendChild(pop);
  });
}
async function memSet(on, quiet) {
  if (on && !quiet && !(await memConfirm())) return false;
  await post("/api/agent", { memory_on: !!on, memory_asked: true });
  MEM.on = !!on;
  MEM.asked = true;
  if (!quiet)
    toast(
      on
        ? tr("Память включена: ИИ знают тебя, Mnemai учится")
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
