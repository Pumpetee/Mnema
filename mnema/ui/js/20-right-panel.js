// ---------------------------------------------------------------- right panel
const STAGE = {
  записала: "c-ok",
  подтвердилось: "c-ok",
  спрашиваю: "c-warn",
  читаю: "c-acc",
  "ищу в сети": "c-acc",
  ошибка: "c-bad",
  заметила: "c-acc",
  "жду повтора": "c-mute",
  пропустила: "c-mute",
  "уже знаю": "c-mute",
  "ничего нового": "c-mute",
};
const SMALL = new Set(["читаю", "ничего нового", "уже знаю", "пропустила"]);
async function buildPanel() {
  const P = $("#panel");
  if (!P) return;
  const [ls, br] = await Promise.all([api("/api/learn/status"), api("/api/learn/brain")]);
  const s = ls.settings;
  const st = s.demo
    ? ["info", "демо"]
    : s.paused
      ? ["pause", "пауза"]
      : !s.sources.mnema_chat.enabled
        ? ["info", "выключено"]
        : br.level === "bad"
          ? ["bad", "не работает"]
          : br.ok
            ? ["", "учусь"]
            : ["info", "только явное"];
  P.innerHTML = `<div class="ph"><div class="ph-row"><b>Что поняла и почему</b><span class="status ${st[0]}"><i></i>${st[1]}</span><div class="sp"></div>
     <button class="ib" id="phide" title="Закрыть (Esc)">${ic("x")}</button></div>${timersHtml()}
    ${!s.demo && br.level !== "ok" ? `<div class="brain ${br.level === "bad" ? "bad" : "info"}"><div style="flex:1">${esc(br.message)}</div><button class="btn sm" id="bfix">${br.kind === "none" ? "Понимать речь" : "Исправить"}</button></div>` : ""}
    <div class="ptabs"><button data-pt="feed">Лента</button></div></div>
   <div class="pbody" id="pbody"></div>
   <div class="quick"><div class="row"><input id="qfact" placeholder="Запомнить о себе…"><select id="qwhere" title="Куда"><option value="inbox">${tr("факт")}</option><option value="rules">${tr("правило")}</option><option value="decisions">${tr("решение")}</option></select><button class="btn sm" id="qsave">Запомнить</button></div></div>`;
  $("#phide").onclick = () => toggleDrawer(false);
  if (CHAT.tab === "sees") CHAT.tab = "feed";
  if ($("#bfix")) $("#bfix").onclick = (e) => brainFix(e.currentTarget, br);
  $$("[data-pt]").forEach(
    (b) =>
      (b.onclick = () => {
        CHAT.tab = b.dataset.pt;
        LS.set("ptab", CHAT.tab);
        panelTab();
      }),
  );
  const q = async () => {
    const f = $("#qfact").value.trim();
    if (!f) return;
    try {
      await post("/api/remember", { fact: f, where: $("#qwhere").value });
      $("#qfact").value = "";
      toast("Запомнила");
      refreshStatus();
    } catch (e) {
      toast(e.message);
    }
  };
  $("#qsave").onclick = q;
  $("#qfact").onkeydown = (e) => {
    if (e.key === "Enter") q();
  };
  badge();
  panelTab();
}
function brainFix(anchor, br) {
  const opts = [
    {
      label: "Claude по подписке — рекомендую",
      icon: "chat",
      run: async () => {
        await post("/api/learn/settings", { brain: { kind: "claude_code" } });
        toast("Теперь понимаю обычную речь");
        buildPanel();
      },
    },
    { label: "Своя или локальная модель — в настройках", icon: "set", run: () => goSet("learn/c-sources") },
  ];
  if (br.kind !== "none")
    opts.push({
      label: "Вернуть «только явное»",
      icon: "redo",
      run: async () => {
        await post("/api/learn/settings", { brain: { kind: "none" } });
        buildPanel();
      },
    });
  menu(anchor, opts);
}
async function panelTab() {
  $$("[data-pt]").forEach((b) => b.classList.toggle("on", b.dataset.pt === CHAT.tab));
  clearInterval(CHAT.feedTimer);
  CHAT.feedTimer = null;
  return startFeed();
}
function fileOf(w) {
  const [k, n] = String(w).split(/:(.*)/),
    nm = String(n || "")
      .replace(/\s*#[\w-]+/g, "")
      .trim();
  return (
    {
      inbox: "00 Inbox/Inbox.md",
      rules: "70 Memory/Rules.md",
      decisions: "60 Events",
      profile: "70 Memory/Profile.md",
      thought: "70 Memory/Thoughts.md",
    }[k] ||
    (k === "project"
      ? "20 Projects/" + nm + "/_Project.md"
      : k === "person"
        ? "30 People/" + nm + ".md"
        : k === "card"
          ? "70 Memory/Cards/" + nm + ".md"
          : w)
  );
}
function evHtml(e) {
  const t = (e.ts || "").slice(11, 16),
    cls = STAGE[e.stage] || "c-mute";
  if (SMALL.has(e.stage))
    return `<div class="ev small" data-small><b class="${cls}">${esc(e.stage)}</b>${esc(e.stage === "читаю" ? e.text.slice(0, 60) + (e.text.length > 60 ? "…" : "") : e.text)}<span>${t}</span></div>`;
  const it = e.item,
    open = it && CHAT.open.has(it);
  let a = "";
  if (e.stage === "спрашиваю" && open)
    a = /противоречит/.test(e.why || "")
      ? `<button class="p" data-a="keep">Новое верно</button><button data-a="keep_old">Старое верно</button>`
      : `<button class="p" data-a="keep">Запомнить</button><button data-a="reject">Нет</button><button data-a="never">Не учись такому</button>`;
  else if (e.stage === "записала" && it)
    a = `<button data-a="forget">Отменить</button><button data-a="edit">Поправить</button>`;
  else if ((e.stage === "заметила" || e.stage === "жду повтора") && it)
    a = `<button data-a="keep">Запомнить сейчас</button>`;
  return `<div class="ev" data-item="${esc(it || "")}" data-text="${esc(e.text)}"><div class="h ${cls}"><i></i>${esc(e.stage)}<span>${t}</span></div><div class="tx">${esc(e.text)}</div>${e.why ? `<div class="why">${esc(e.why)}</div>` : ""}${e.stage === "записала" && e.where ? `<div class="file">в файл <code>${esc(fileOf(e.where))}</code> у тебя на компьютере</div>` : ""}${e.quote && e.stage !== "читаю" ? `<div class="q">${inline(e.quote)}</div>` : ""}${a ? `<div class="a">${a}</div>` : ""}</div>`;
}
async function startFeed() {
  const B = $("#pbody");
  if (!B) return;
  CHAT.feedSince = "";
  CHAT.open = new Set((await api("/api/learn/items?view=queue")).items.map((i) => i.id));
  B.innerHTML = `<div class="ptools"><span class="hint">что поняла и почему</span><label class="hint" style="display:flex;gap:6px;align-items:center;cursor:pointer">мелочи<button class="sw ${CHAT.detail ? "on" : ""}" id="pdet" style="transform:scale(.8)"></button></label></div><div id="feed"></div>`;
  $("#pdet").onclick = () => {
    CHAT.detail = !CHAT.detail;
    LS.set("detail", CHAT.detail);
    $("#pdet").classList.toggle("on", CHAT.detail);
    $$("#feed [data-small]").forEach((x) => (x.hidden = !CHAT.detail));
    emptyHint();
  };
  const load = async () => {
    const f = $("#feed");
    if (!f) {
      clearInterval(CHAT.feedTimer);
      CHAT.feedTimer = null;
      return;
    }
    const d = await api("/api/learn/live?since=" + encodeURIComponent(CHAT.feedSince));
    if (d.events.length) {
      if (d.events.some((e) => e.stage === "спрашиваю"))
        CHAT.open = new Set((await api("/api/learn/items?view=queue")).items.map((i) => i.id));
      CHAT.feedSince = d.events[d.events.length - 1].ts;
      f.insertAdjacentHTML("afterbegin", d.events.slice().reverse().map(evHtml).join(""));
      $$("[data-small]", f).forEach((x) => (x.hidden = !CHAT.detail));
      bindFeed();
      badge();
    }
    emptyHint();
  };
  await load();
  CHAT.feedTimer = setInterval(load, 1500);
}
function emptyHint() {
  const f = $("#feed");
  if (!f) return;
  const any = $$(".ev", f).some((x) => !x.hidden);
  const ph = $(".empty-feed", f);
  if (any && ph) ph.remove();
  if (!any && !ph)
    f.insertAdjacentHTML(
      "beforeend",
      '<div class="hint empty-feed" style="padding:14px 6px;text-align:center">Пока тихо. Расскажи что-нибудь о себе — здесь появится, что я поняла и почему.</div>',
    );
}
function bindFeed() {
  $$("#feed .a button").forEach((b) => {
    if (b._b) return;
    b._b = 1;
    b.onclick = async () => {
      const ev = b.closest(".ev"),
        a = b.dataset.a,
        body = { id: ev.dataset.item, action: a };
      if (a === "edit") {
        const v = prompt("Поправь:", ev.dataset.text);
        if (!v) return;
        body.text = v;
      }
      try {
        await post("/api/learn/review", body);
        CHAT.open.delete(ev.dataset.item);
        $(".a", ev).outerHTML =
          `<div class="done">✓ ${{ keep: "запомнила", reject: "не буду", never: "больше такому не учусь", keep_old: "оставила как было", forget: "отменила — этого больше нет в памяти", edit: "поправила" }[a]}</div>`;
        badge();
      } catch (e) {
        toast(e.message);
      }
    };
  });
}
function staleWhy(i) {
  const d = (i.date || "").split("-").reverse().join(".");
  return `${i.title || ""} · ${tr("статус от")} ${d}, ${i.age_days} ${tr("дн. назад")}`;
}
async function loadSees() {
  if (CHAT.tab !== "sees") return;
  const B = $("#pbody");
  if (!B) return;
  const d = await api("/api/chat/sees?model=" + encodeURIComponent(CHAT.model || ""));
  B.innerHTML = `<div class="seebox"><h4>${esc(d.provider)} видит</h4><div class="chips">${d.sees.map((x) => `<span class="chip yes">${esc(x.name)} · ${x.count}</span>`).join("")}</div>
     ${d.hidden_parts.length || d.hidden_tags.length ? `<h4 style="margin-top:12px">Скрыто от неё</h4><div class="chips">${[...d.hidden_parts, ...d.hidden_tags].map((x) => `<span class="chip no">${esc(x)}</span>`).join("")}</div>` : ""}
     <div class="hint" style="margin-top:10px">Доступ — по правилам «${esc(d.client)}». <a href="#settings/security/c-access" style="color:var(--acc)">Изменить</a></div></div>
   <div class="seebox"><h4>Как она со мной работает</h4><div class="hint">Характер «${esc(d.preset)}», включено ${d.rules_on} из ${d.rules_total} правил.</div>
     <div class="mini-tg"><button class="sw ${d.ask_options ? "on" : ""}" data-qt="ask_options"></button>Уточнять вопросами с кнопками</div>
     <div class="mini-tg"><button class="sw ${d.second_pass ? "on" : ""}" data-qt="second_pass"></button>Перечитывать ответ перед отправкой</div>
     <div class="hint"><a href="#settings/style/c-rules" style="color:var(--acc)">Все правила</a></div></div>
   <div class="seebox"><h4>Выучено само</h4><div class="hint">${d.learned} фактов. <a href="#memory/portrait" style="color:var(--acc)">Посмотреть, откуда</a></div></div>`;
  $$("[data-qt]", B).forEach(
    (b) =>
      (b.onclick = async () => {
        const on = !b.classList.contains("on");
        await post("/api/agent", { toggles: { [b.dataset.qt]: on } });
        b.classList.toggle("on", on);
        toast("Сохранено");
      }),
  );
}
