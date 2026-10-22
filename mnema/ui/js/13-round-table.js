// ---------------------------------------------------------------- the round table: who speaks, who's next, rounds, pause / continue / finish
async function consAct(action, extra) {
  if (!CHAT.id) return;
  try {
    const r = await post("/api/chat/cons", { chat: CHAT.id, action, ...(extra || {}) });
    if (action === "off") {
      const c = await api("/api/chat?id=" + CHAT.id);
      CHAT.model = c.model;
      CHAT.live = null;
      renderChat(c);
      toast(tr("Дальше отвечает один ИИ"));
      return;
    }
    if (action === "set") {
      const c = await api("/api/chat?id=" + CHAT.id);
      CHAT.chat.consortium = c.consortium;
      CHAT.cons = c.consortium;
      drawModelLabel();
      drawTable();
      return;
    }
    if (action === "pause") {
      toast(tr("Договорит текущий, остальные подождут"));
      if (CHAT.live) {
        CHAT.live.pausing = true;
        drawTable();
      }
      return;
    }
    if (action === "finish" && CHAT.polling) {
      if (CHAT.live) {
        CHAT.live.finishing = true;
        drawTable();
      }
      return;
    }
    if (action === "resume" || action === "finish") {
      $("#msgs").insertAdjacentHTML(
        "beforeend",
        `<div class="msg ai" id="live"><div class="av"></div><div><div class="md">${TYPING}</div></div></div>`,
      );
      scrollEnd();
      poll();
    }
  } catch (e) {
    toast(e.message);
  }
}
function tableState() {
  const c = CHAT.cons,
    st = (c && c.state) || {},
    L = CHAT.live,
    mem = (c && c.members) || [],
    n = mem.length || 1;
  if (L && L.status && CHAT.polling) {
    return {
      status: L.finishing || L.status === "summary" ? "summary" : L.pausing ? "pausing" : "running",
      round: L.round || 1,
      rounds: L.rounds || c.rounds,
      idx: L.idx || 0,
      done: (L.turn || 1) - 1,
      total: L.turns || n * c.rounds,
      speaker: L.speaker,
      next: L.next,
    };
  }
  const s = st.status || "",
    r = +st.round || 0,
    nx = +st.next || 0;
  return {
    status: s === "paused" || s === "waiting" ? s : s === "running" ? "paused" : s === "done" ? "done" : "ready",
    round: r + 1,
    rounds: c.rounds,
    idx: nx % n,
    done: s === "done" ? n * c.rounds : s ? r * n + nx : 0,
    total: n * c.rounds,
    asked: st.asked,
  };
}
function drawTable() {
  const box = $("#ctable");
  if (!box) return;
  const c = CHAT.cons;
  if (!c || !CHAT.id) {
    box.innerHTML = "";
    box.className = "";
    return;
  }
  const t = tableState(),
    names = c.members.map(consName),
    live = t.status === "running" || t.status === "pausing" || t.status === "summary";
  const key = JSON.stringify([t, c.members, c.rounds]);
  if (box.dataset.k === key) return;
  box.dataset.k = key;
  box.className = "ctable on";
  const ready = (CHAT.providers || [])
    .filter((p) => p.ready)
    .flatMap((p) => p.models.filter((m) => m.id || p.id !== "claude_code").map((m) => p.id + ":" + m.id))
    .filter((r) => !c.members.includes(r));
  const seat = (r, i) => {
    const nm = names[i],
      sp = live && nm === t.speaker,
      nx = !sp && (live ? nm === t.next : (t.status === "paused" || t.status === "waiting") && i === t.idx),
      ask = t.status === "waiting" && t.asked === nm;
    const lab = sp
      ? t.status === "summary"
        ? tr("подводит итог")
        : tr("говорит")
      : ask
        ? tr("спросил тебя")
        : nx
          ? tr("следующий")
          : "";
    return `<div class="seat ${sp ? "sp" : ""} ${nx ? "nx" : ""} ${ask ? "ask" : ""}" style="--sc:${SPK_COLORS[i % SPK_COLORS.length]};--i:${i}"><span class="sav">${esc(nm.slice(0, 1))}${sp ? '<i class="ring"></i><i class="ring r2"></i>' : ""}</span><b data-noi18n>${esc(nm)}</b><small>${sp ? TYPING : ""}${lab}</small>${c.members.length > 2 && !live ? `<button class="sx" data-rm="${esc(r)}" title="${tr("Убрать из обсуждения")}">×</button>` : ""}</div>`;
  };
  const segs = Array.from(
    { length: t.total },
    (_, k) =>
      `<i class="${k < t.done ? "f" : k === t.done && live ? "cur" : ""} ${(k + 1) % c.members.length === 0 && k < t.total - 1 ? "rb" : ""}"></i>`,
  ).join("");
  const stg = (consPlan(c.rounds)[Math.min(t.round, c.rounds) - 1] || [""])[0];
  const msg = {
    running: `${stg ? `<em class="cstg">${tr(stg)}</em>` : ""}${tr("Говорит")} <b data-noi18n>${esc(t.speaker || "")}</b>${t.next ? ` · ${tr("дальше")} <b data-noi18n>${esc(t.next)}</b>` : ` · ${tr("подведёт итог")}`}`,
    pausing: tr("Пауза: договорит текущий, остальные ждут"),
    summary: tr("Обсуждение завершается: подводят итог"),
    paused: tr("Пауза. Внеси ясность сообщением или нажми «Продолжить»"),
    waiting: `<b data-noi18n>${esc(t.asked || "")}</b> ${tr("спросил тебя — остальные ждут ответа")}`,
    ready: tr("Задай вопрос — обсудят по кругу, а ты можешь вмешаться в любой момент"),
    done: `${ic("check")}${tr("Обсуждение завершено. Задай новый вопрос — или пусть обсудят ещё раз")}`,
  }[t.status];
  const btns = live
    ? `<button class="cbtn" data-ca="pause" ${t.status !== "running" ? "disabled" : ""}>${ic("pause")}${tr("Пауза")}</button><button class="cbtn fin" data-ca="finish" ${t.status === "summary" ? "disabled" : ""}>${ic("check")}${tr("Завершить")}</button>`
    : t.status === "paused" || t.status === "waiting"
      ? `<button class="cbtn go" data-ca="resume">${ic("play")}${tr("Продолжить")}</button><button class="cbtn fin" data-ca="finish">${ic("check")}${tr("Завершить")}</button>`
      : `${CHAT.chat && (CHAT.chat.messages || []).some((m) => m.role === "user") ? `<button class="cbtn go" data-ca="resume">${ic("redo")}${tr("Обсудить ещё раз")}</button>` : ""}`;
  box.innerHTML = `<div class="ctop"><div class="seats">${c.members.map(seat).join("")}${c.members.length < 4 && ready.length ? `<button class="seat add" data-add title="${tr("Добавить ИИ")}"><span class="sav">+</span><b>${tr("Добавить")}</b><small></small></button>` : ""}</div>
    <div class="cside"><div class="cround"><span>${t.status === "done" || t.status === "ready" ? tr("Кругов") : `${tr("Круг")} <b>${Math.min(t.round, c.rounds)}</b> ${tr("из")}`}</span><div class="stepper sm"><button data-rd="-1" ${c.rounds <= Math.max(1, live ? t.round : 1) ? "disabled" : ""}>−</button><b>${c.rounds}</b><button data-rd="1" ${c.rounds >= 20 ? "disabled" : ""}>+</button></div></div>
    <div class="cprog">${segs}</div></div></div>
    <div class="cbot"><span class="cmsg2 st-${t.status}">${live ? '<i class="pulse"></i>' : ""}${msg}</span><div class="cbtns">${btns}<button class="cbtn g" data-ca="menu" title="${tr("Ещё")}">${ic("dots")}</button></div></div>`;
  $$("[data-ca]", box).forEach(
    (b) =>
      (b.onclick = (e) => {
        const a = b.dataset.ca;
        if (a === "menu") {
          consMenu(b);
          return;
        }
        consAct(a);
      }),
  );
  $$("[data-rd]", box).forEach(
    (b) => (b.onclick = () => consAct("set", { rounds: Math.max(1, Math.min(20, c.rounds + +b.dataset.rd)) })),
  );
  $$("[data-rm]", box).forEach(
    (b) => (b.onclick = () => consAct("set", { members: c.members.filter((x) => x !== b.dataset.rm) })),
  );
  const add = $("[data-add]", box);
  if (add)
    add.onclick = () => {
      closeMenus();
      MENU_ANCHOR = add;
      const m = document.createElement("div");
      m.className = "menu";
      m.innerHTML = ready
        .slice(0, 14)
        .map((r) => `<button data-r="${esc(r)}">${esc(consName(r))}</button>`)
        .join("");
      document.body.appendChild(m);
      const rr = add.getBoundingClientRect();
      m.style.left = rr.left + "px";
      m.style.top = rr.bottom + 6 + "px";
      $$("[data-r]", m).forEach(
        (x) =>
          (x.onclick = () => {
            m.remove();
            consAct("set", { members: [...c.members, x.dataset.r] });
          }),
      );
    };
}
function consMenu(anchor) {
  closeMenus();
  MENU_ANCHOR = anchor;
  const m = document.createElement("div");
  m.className = "menu";
  const live = !!CHAT.polling;
  m.innerHTML = `<button data-cm="edit">${ic("users")}<span>${tr("Состав и круги")}</span></button><button data-cm="off" ${live ? "disabled" : ""}>${ic("chat")}<span>${tr("Выйти из консорциума — дальше один ИИ")}</span></button>`;
  document.body.appendChild(m);
  const r = anchor.getBoundingClientRect();
  m.style.left = Math.max(8, r.right - m.offsetWidth) + "px";
  m.style.top = r.bottom + 6 + "px";
  $$("[data-cm]", m).forEach(
    (b) =>
      (b.onclick = () => {
        m.remove();
        b.dataset.cm === "edit" ? consortModal() : consAct("off");
      }),
  );
}
