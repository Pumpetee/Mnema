// ---------------------------------------------------------------- achievements
const ACH = { data: null, folder: "", busy: false, queue: [] };
const TIER = { common: "обычное", rare: "редкое", epic: "эпическое", legendary: "легендарное" };
function fmtNum(n) {
  n = n || 0;
  return n >= 1e6
    ? (n / 1e6).toFixed(1).replace(".", ",") + " млн"
    : n >= 1e3
      ? Math.round(n / 1e3) + " тыс."
      : String(n);
}
async function achRefresh() {
  let d;
  try {
    d = await api("/api/ach");
  } catch (e) {
    return;
  }
  ACH.data = d;
  drawAchCard();
  const b = $("#achbadge");
  if (b) {
    b.hidden = !d.pending.length;
    b.textContent = d.pending.length;
  }
  if (d.pending.length && !ACH.busy) {
    ACH.queue.push(...d.pending);
    post("/api/ach/seen", {}).catch(() => {});
    achNext();
  }
}
function drawAchCard() {
  const lc = $("#localcard"),
    d = ACH.data,
    sf = ACH.safety;
  if (!lc) return;
  lc.classList.add("achcard");

  const g = sf ? sf.guarded : [];
  const row = (k, ico, t, sub, bad, tail) =>
    `<button class="srow ${bad ? "bad" : ""}" data-sr="${k}" title="${sub}"><span class="sri">${ic(bad ? "x" : ico)}</span><span><b>${t}</b></span>${tail || ic("chev")}</button>`;
  lc.innerHTML = `<div class="safehead">${ic("shield")}<b>${tr("Память")}</b><button class="sgear shelp" id="memtut" title="${tr("Как работает память")}"><i>?</i></button><button class="sgear" id="safeset" title="${tr("Настроить защиту")}">${ic("gear")}</button><button class="sw sm ${MEM.on ? "on" : ""}" id="memsw" title="${tr(MEM.on ? "Выключить память" : "Включить память")}"></button></div>
    ${
      !MEM.on
        ? `<div class="memoffrow">${tr("Выключена: ИИ не знают тебя, Mnema ничего не запоминает")}</div>`
        : `${row("folder", "folder", tr("Локальная память на ПК"), (sf && sf.encrypted ? tr("зашифрована · ") : "") + tr("открыть папку"), false, `<span class="sropen">${ic("ext")}</span>`)}
    ${row("access", "lock", tr("Настройки доступа"), g.length ? `${tr("Личное скрыто от")} ${g.length} ${tr("ИИ")}` : tr("кто из ИИ что видит"))}`
    }`;
  $("#memsw", lc).onclick = () => memSet(!MEM.on);
  if ($("#memtut", lc)) $("#memtut", lc).onclick = () => memTour();
  $$("[data-achopen]", lc).forEach((x) => (x.onclick = () => achGallery()));
  if ($("#safeset", lc)) $("#safeset", lc).onclick = () => goSet("security/seccard");
  $$("[data-sr]", lc).forEach(
    (x) =>
      (x.onclick = () =>
        ({
          folder: () => post("/api/memory/open").catch((err) => toast(err.message)),
          access: () => goSet("security/c-access"),
          out: () => outgoingModal(7),
        })[x.dataset.sr]()),
  );
}
function achNext() {
  if (!achOn()) {
    ACH.queue = [];
    ACH.busy = false;
    return;
  }
  const a = ACH.queue.shift();
  if (!a) {
    ACH.busy = false;
    return;
  }
  ACH.busy = true;
  const t = document.createElement("div");
  t.className = "achtoast " + a.tier;
  t.innerHTML = `<div class="glow"></div><div class="medal"><span>${a.icon}</span></div><div class="tx"><small>Достижение · ${TIER[a.tier]}</small><b>${esc(a.title)}</b><span>${esc(a.how)}</span></div><div class="xp">+${a.xp} XP</div>`;
  document.body.appendChild(t);
  requestAnimationFrame(() => t.classList.add("in"));
  if (a.tier === "epic" || a.tier === "legendary") confetti(a.tier);
  t.onclick = () => {
    t.remove();
    achGallery();
  };
  setTimeout(
    () => {
      t.classList.remove("in");
      t.classList.add("out");
      setTimeout(() => {
        t.remove();
        achNext();
      }, 450);
    },
    a.tier === "common" ? 3200 : 4600,
  );
}
function confetti(tier) {
  const c = document.createElement("canvas");
  c.className = "confetti";
  c.width = innerWidth;
  c.height = innerHeight;
  document.body.appendChild(c);
  const x = c.getContext("2d");
  const colors =
    tier === "legendary"
      ? ["#f5b301", "#ffd84d", "#ff9f1c", "#fff3b0"]
      : tier === "epic"
        ? ["#8b5cf6", "#c084fc", "#6366f1", "#f0abfc"]
        : ["#3b82f6", "#60a5fa", "#22c55e", "#a78bfa"];
  const N = tier === "legendary" ? 220 : tier === "epic" ? 150 : 90,
    ox = innerWidth - 210,
    oy = 90;
  const P = Array.from({ length: N }, () => ({
    x: ox,
    y: oy,
    vx: (Math.random() - 0.5) * 14,
    vy: -Math.random() * 12 - 3,
    r: Math.random() * 6 + 3,
    c: colors[(Math.random() * colors.length) | 0],
    a: Math.random() * 6,
    va: (Math.random() - 0.5) * 0.3,
  }));
  let f = 0;
  (function tick() {
    x.clearRect(0, 0, c.width, c.height);
    for (const p of P) {
      p.vy += 0.35;
      p.vx *= 0.99;
      p.x += p.vx;
      p.y += p.vy;
      p.a += p.va;
      x.save();
      x.translate(p.x, p.y);
      x.rotate(p.a);
      x.fillStyle = p.c;
      x.globalAlpha = Math.max(0, 1 - f / 140);
      x.fillRect(-p.r / 2, -p.r / 4, p.r, p.r / 2);
      x.restore();
    }
    if (++f < 150) requestAnimationFrame(tick);
    else c.remove();
  })();
}
function achGallery(group) {
  closeMenus();
  const d = ACH.data;
  if (!d) return;
  const old = $(".achm");
  if (old) old.remove();
  const pop = document.createElement("div");
  pop.className = "modal achm";
  document.body.appendChild(pop);
  pop.onclick = (e) => {
    if (e.target === pop) pop.remove();
  };
  let g = group || "all";
  const L = d.level;
  const draw = () => {
    const items = d.items
      .filter((i) => g === "all" || i.group === g)
      .sort((a, b) => b.got - a.got || b.progress - a.progress);
    const pct = Math.round(L.progress * 100),
      R = 44,
      C = 2 * Math.PI * R,
      rare = d.items.filter((i) => i.group === "rare"),
      ep = d.items.filter((i) => i.tier === "epic" || i.tier === "legendary");
    pop.innerHTML = `<div class="card"><div class="lvhero"><div class="lvglow"></div>
       <div class="lvbig"><svg viewBox="0 0 104 104"><defs><linearGradient id="lvg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#8b7cff"/><stop offset="1" stop-color="#4fb6ff"/></linearGradient></defs><circle cx="52" cy="52" r="${R}" class="lvtrack"/><circle cx="52" cy="52" r="${R}" class="lvbar" stroke="url(#lvg)" stroke-dasharray="${C}" stroke-dashoffset="${C}" style="--off:${C * (1 - L.progress)}"/></svg><div class="lvnum"><small>${tr("уровень")}</small><b>${L.level}</b></div></div>
       <div class="lvinfo"><div class="lvname">${esc(L.name)}</div>
        <div class="lvxp"><div class="lvline"><i style="--w:${pct}%"></i></div><div class="lvlbl"><span><b>${L.xp}</b> XP</span><span>${L.to ? `${tr("до")} «${esc(tr(L.next_name || ""))}» — ${L.to - L.xp} XP` : tr("высший уровень")}</span></div></div>
        <div class="lvstats"><div><b>${d.got}<small>/${d.total}</small></b><span>${tr("открыто")}</span></div><div><b>${rare.filter((i) => i.got).length}<small>/${rare.length}</small></b><span>${tr("редких")}</span></div><div><b>${ep.filter((i) => i.got).length}<small>/${ep.length}</small></b><span>${tr("эпических")}</span></div></div></div>
       <label class="achsw" title="${tr("Выключишь — пропадут и всплывающие награды, и этот раздел. Вернуть можно в шестерёнке")}"><span>${tr("Показывать достижения")}</span><button class="sw on" id="achoff"></button></label><button class="lmx" id="achx">×</button></div>
      <div class="achtabs">${[["all", "Все"], ...Object.entries(d.groups)].map(([k, t]) => `<button data-g="${k}" class="${k === g ? "on" : ""}">${esc(t)}<span>${d.items.filter((i) => (k === "all" || i.group === k) && i.got).length}/${d.items.filter((i) => k === "all" || i.group === k).length}</span></button>`).join("")}</div>
      <div class="achgrid">${items
        .map(
          (
            i,
          ) => `<div class="ach ${i.tier} ${i.got ? "got" : "locked"} ${i.secret && !i.got ? "secret" : ""}"><div class="medal"><span>${i.icon}</span></div><b>${esc(i.title)}</b><small>${esc(i.how)}</small>
        ${i.got ? `<em class="when">${esc(String(i.at).slice(0, 10))} · +${i.xp} XP</em>` : i.progress > 0 ? `<i class="mini"><em style="width:${Math.round(i.progress * 100)}%"></em></i>` : `<em class="when">${TIER[i.tier]} · ${i.xp} XP</em>`}</div>`,
        )
        .join("")}</div></div>`;
    $("#achx", pop).onclick = () => pop.remove();
    if ($("#achoff", pop))
      $("#achoff", pop).onclick = () => {
        LS.set("ach_on", false);
        applyAch();
        drawAchCard();
        pop.remove();
        toast(tr("Достижения выключены. Вернуть — в шестерёнке справа вверху"));
      };
    $$("[data-g]", pop).forEach(
      (b) =>
        (b.onclick = () => {
          g = b.dataset.g;
          draw();
        }),
    );
  };
  draw();
}
setInterval(() => {
  if (!document.hidden) achRefresh();
}, 30000);
