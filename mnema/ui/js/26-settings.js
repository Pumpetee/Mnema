// ---------------------------------------------------------------- settings
const AUTO_HINT = {
  observe: "Только показывает, что заметила. Ничего не пишет.",
  approve: "Всё новое ждёт тебя.",
  mixed: "Уверенное записывает сама, личное и спорное спрашивает.",
  quiet: "Пишет всё сама, ты откатываешь лишнее.",
};
const BRAIN_HINT = {
  auto: "Сама выбирает лучшее из того, что есть: Claude по подписке, если он стоит на компьютере, иначе встроенную модель.",
  none: "Понимает только явное: «запомни», поправки, решения.",
  local: "Встроенная модель на компьютере понимает обычную речь. Ничего не уходит наружу.",
  claude_code: "Понимает обычную речь. Тексты уходят в Claude по твоей подписке.",
  api: "Ключ и модель задаются в продвинутых настройках.",
  ollama: "Нужна запущенная Ollama, модель выбирается в продвинутых настройках. Ничего не уходит с компьютера.",
};
const BRAINS = {
  auto: "сама",
  none: "только явное",
  local: "встроенная",
  claude_code: "Claude по подписке",
  api: "свой ключ",
  ollama: "Ollama",
};
let SETTINGS_FOCUS = "",
  PRM_ST = { prompts: [], mode: "second", auto: true };
function parseProxy(u) {
  u = String(u || "").trim();
  if (!u) return { mode: "system" };
  if (/^(off|нет|none|direct)$/i.test(u)) return { mode: "off" };
  if (!/:\/\//.test(u)) u = "http://" + u;
  try {
    const x = new URL(u.replace(/^socks5?h?:/i, "http:"));
    return {
      mode: /^socks/i.test(u) ? "socks5" : "http",
      host: x.hostname,
      port: x.port,
      user: decodeURIComponent(x.username || ""),
    };
  } catch (e) {
    return { mode: "http", host: u };
  }
}
function proxyForm(cur, pwSet, sys) {
  const p = parseProxy(cur),
    m = p.mode;
  return `<div class="pxf">${vpnButtons()}<div class="pxmanual" ${m === "http" || m === "socks5" ? "" : "hidden"}><div class="seg pxmode">${[
    ["system", "Как в Windows"],
    ["off", "Напрямую"],
    ["http", "HTTP"],
    ["socks5", "SOCKS5"],
  ]
    .map(([k, l]) => `<button data-pm="${k}" class="${m === k ? "on" : ""}">${l}</button>`)
    .join("")}</div>
   <div class="hint pxsys" ${m === "system" ? "" : "hidden"}>${sys ? `Windows сейчас использует <b>${esc(sys)}</b> — его и возьму.` : "В Windows прокси не задан — пойду напрямую."}</div>
   <div class="pxfields" ${m === "http" || m === "socks5" ? "" : "hidden"}><div class="pxrow"><div class="fld"><span>Адрес</span><input data-px="host" value="${esc(p.host || "")}" placeholder="127.0.0.1"></div><div class="fld"><span>Порт</span><input data-px="port" value="${esc(p.port || "")}" placeholder="${m === "socks5" ? "1080" : "8080"}"></div></div>
   <div class="pxrow"><div class="fld"><span>Логин, если нужен</span><input data-px="user" value="${esc(p.user || "")}" autocomplete="off"></div><div class="fld"><span>Пароль</span><input data-px="pw" type="password" placeholder="${pwSet ? "сохранён" : ""}" autocomplete="new-password"></div></div></div>
   <div class="row" style="margin-top:10px"><button class="btn l" data-pxa="check">Проверить</button><button class="btn" data-pxa="save">Сохранить</button><span class="hint pxres"></span></div></div></div>`;
}
function bindProxyForm(box, onSave) {
  let mode = $(".pxmode .on", box).dataset.pm;
  const url = () => {
    if (mode === "system") return "";
    if (mode === "off") return "off";
    const v = (k) => $(`[data-px="${k}"]`, box).value.trim();
    if (!v("host")) return null;
    return `${mode}://${v("user") ? encodeURIComponent(v("user")) + "@" : ""}${v("host")}${v("port") ? ":" + v("port") : ""}`;
  };
  const pw = () => {
    const v = $('[data-px="pw"]', box).value;
    return v ? v : null;
  };
  $$("[data-pm]", box).forEach(
    (b) =>
      (b.onclick = () => {
        mode = b.dataset.pm;
        $$("[data-pm]", box).forEach((x) => x.classList.toggle("on", x === b));
        $(".pxsys", box).hidden = mode !== "system";
        $(".pxfields", box).hidden = !(mode === "http" || mode === "socks5");
        $(".pxres", box).textContent = "";
      }),
  );
  $('[data-pxa="check"]', box).onclick = async () => {
    const u = url();
    if (u === null) {
      toast("Укажи адрес прокси");
      return;
    }
    const r = $(".pxres", box);
    r.textContent = "проверяю…";
    r.style.color = "";
    try {
      const x = await post("/api/net/check", { proxy: u, ...(pw() !== null ? { password: pw() } : {}) });
      r.textContent = x.ok ? `работает · ${x.via} · ${x.ms} мс` : `не работает: ${x.error}`;
      r.style.color = x.ok ? "var(--ok)" : "var(--bad)";
    } catch (e) {
      r.textContent = e.message;
    }
  };
  $('[data-pxa="save"]', box).onclick = async () => {
    const u = url();
    if (u === null) {
      toast("Укажи адрес прокси");
      return;
    }
    await onSave(u, pw());
  };
  bindVpnButtons(
    box,
    async (u, name) => {
      await onSave(u, null, true);
      toast(u ? tr("VPN подключён") + ": " + name : name + " " + tr("работает на всю систему"));
    },
    () => {
      const mm = $(".pxmanual", box);
      mm.hidden = !mm.hidden;
    },
  );
  if (0)
    $('[data-pxa="find"]', box).onclick = async (e) => {
      const b = e.currentTarget,
        r = $(".vpnr", box);
      b.disabled = true;
      r.innerHTML = `<div class="hint" style="margin:8px 0">${tr("Ищу VPN на этом компьютере…")}</div>`;
      let d;
      try {
        d = await api("/api/net/detect");
      } catch (err) {
        d = { proxies: [], tunnels: [] };
      }
      b.disabled = false;
      r.innerHTML =
        [
          ...(d.tunnels || []).map(
            (t) =>
              `<div class="vrow sys"><i></i><div><b>${esc(t)}</b> <span class="hint">${tr("запущен. Если он подключён, Mnema пойдёт через него сама — поля можно не заполнять")}</span></div></div>`,
          ),
          ...(d.proxies || []).map(
            (p) =>
              `<div class="vrow ok"><i></i><div><b>${esc(p.name)}</b> <span class="hint">${esc(p.url.replace("://", " · "))} · ${p.ms} ${tr("мс")}</span></div><button class="btn sm" data-vu="${esc(p.url)}">${tr("Использовать")}</button></div>`,
          ),
        ].join("") ||
        `<div class="vrow"><div class="hint">${tr("Ничего не нашла. Включи VPN-программу и нажми ещё раз. Если он в Windows на всю систему (OpenVPN, WireGuard), поля можно оставить пустыми.")}</div></div>`;
      $$("[data-vu]", r).forEach(
        (x) =>
          (x.onclick = async () => {
            await onSave(x.dataset.vu, null);
            toast(tr("VPN подключён: все запросы к ИИ идут через него"));
          }),
      );
    };
}
async function viewSettings(arg) {
  arg = String(arg || "");
  arg = { adv: "style", simple: "ai", net: "app/netcard" }[arg] || arg;
  let [sec, card] = arg.split("/");
  if (!SETSECS.some((x) => x[0] === sec)) sec = "ai"; // settings always open at the first section
  const page = $(".page"),
    keep = !card && page && $("#st") && sec === SETCUR ? page.scrollTop : 0;
  const adv = true;
  const [ag, ms, ls, br, pst, eng, scr, efs] = await Promise.all([
    api("/api/agent"),
    api("/api/models"),
    api("/api/learn/status"),
    api("/api/learn/brain"),
    api("/api/prompts").catch(() => ({ prompts: [], mode: "second", auto: true })),
    api("/api/engine").catch(() => null),
    api("/api/scribe/settings").catch(() => null),
    api("/api/efs").catch(() => null),
  ]);
  PRM_ST = pst;
  const prof = ag.profile,
    simple = prof.simple,
    s = ls.settings;
  const seg = (key, choices, val) =>
    `<div class="seg" data-seg="${key}">${Object.entries(choices)
      .map(([k, l]) => `<button data-v="${k}" class="${k === val ? "on" : ""}">${esc(l)}</button>`)
      .join("")}</div>`;
  const allModels = ms.providers
    .filter((p) => p.ready)
    .flatMap((p) =>
      p.models.map((m) => ({ v: p.id + ":" + m.id, l: (p.id === "claude_code" ? "" : p.name + " · ") + m.name })),
    );
  const groups = {};
  Object.entries(ls.sources).forEach(([k, m]) => {
    (groups[m.group] = groups[m.group] || []).push([k, m]);
  });
  if (!$("#st"))
    $("#view").innerHTML = `<div class="page"><div class="wrap setwrap">${APP.demo ? demoBar() : ""}<h1>Настройки</h1>
  <div class="setlay"><nav class="setnav">${SETSECS.map(([k, i, l]) => `<button data-sec="${k}">${ic(i)}<span>${tr(l)}</span></button>`).join("")}</nav><div id="st"></div></div></div></div>`;
  $$(".setnav [data-sec]").forEach((b) => (b.onclick = () => showSec(b.dataset.sec)));
  bindDemo();
  const save = async (patch, msg) => {
    try {
      await post("/api/agent", patch);
      if (msg) toast(msg);
    } catch (e) {
      toast(e.message);
    }
  };
  const saveL = async (patch, msg) => {
    try {
      await post("/api/learn/settings", patch);
      if (msg) toast(msg);
    } catch (e) {
      toast(e.message);
    }
  };
  const again = () => viewSettings(SETCUR);
  {
    $("#st").innerHTML = `
    ${modelHero(ms, allModels, prof.default_model || ms.default_model)}
    <div class="card" data-sec="ai" id="c-prov"><h2>${tr("Модели")}<span class="hint">${tr("с какими ИИ говорить в Mnema")}</span></h2><div class="aigrid">${ms.providers.map((x, n) => provTile(x, n)).join("")}</div></div>
    ${engineCard(eng)}
    ${scribeCard(scr)}
    <div class="card" data-sec="security" id="seccard"><h2>${tr("Защита данных")}</h2>
     <div class="tg" style="padding:0 0 10px;border:0"><button class="sw ${prof.redact !== false ? "on" : ""}" id="secred"></button><div><b>${tr("Скрывать секреты от облачных ИИ")}</b><p>${tr("Номера карт, пароли, ключи, телефоны, паспорта и СНИЛС заменяются метками до отправки, в ответ настоящие значения подставляются на компьютере.")}</p></div></div>
     ${efs ? `<div class="tg" style="padding:0 0 10px;border:0"><button class="sw ${efs.on ? "on" : ""}" id="secefs" ${efs.supported ? "" : "disabled"}></button><div><b>${tr("Шифровать папку памяти")}</b><p>${efs.supported ? tr("Средствами Windows: файлы на диске зашифрованы ключом твоей учётной записи, без входа в неё их не прочитать, даже вынув диск. Для тебя и Mnema всё работает как раньше.") : esc(tr(efs.reason))}</p>${efs.on ? `<button class="btn g sm" id="secbk" style="margin-top:6px">${tr("Сохранить ключ восстановления")}</button>` : ""}</div></div>` : ""}
     <div class="row"><button class="btn l" id="secout">${ic("eye")}${tr("Что ушло наружу")}</button><button class="btn g" id="secacc">${ic("lock")}${tr("Кто из ИИ что видит")}</button></div></div>
    ${themeCard()}
    ${compCard()}
    ${youCard(prof, ag)}
    <div class="card" data-sec="learn" id="c-learn"><div class="set"><b>Насколько сама учится${hq("learn")}</b><div>${seg("autonomy", ag.simple.autonomy.choices, simple.autonomy)}<div class="hint" style="margin-top:6px">${esc(AUTO_HINT[simple.autonomy])}</div></div></div>
    <div class="set"><b>${tr("Что мне можно смотреть")}${hq("outside")}</b><div class="tg" style="padding:0;border:0"><button class="sw ${s.outside !== false ? "on" : ""}" id="outsw"></button><div><b>${tr("Другие программы и браузер")}</b><p>${s.outside === false ? tr("Выключено: учусь только из разговоров в Mnema и работаю с папкой памяти. Чаты Claude Code, заметки, документы, Telegram, браузер и расширение не читаю.") : tr("Можно: читаю только то, что включено ниже. Всё читается на компьютере.")}</p></div></div></div>
    <div class="set srcset"><b>Где учиться<span class="hint">${tr("Нажми на карточку, чтобы включить или выключить")}</span></b><div class="srcgrid ${s.outside === false ? "outoff" : ""}">${Object.entries(
      groups,
    )
      .flatMap(([g, list]) => list.map((x) => [g, ...x]))
      .map(([g, k, m], n) => {
        const on = s.sources[k].enabled,
          v = SRC_LOOK[k] || ["📘", "#6d5ff5", "#4fb6ff", "Читает новое"];
        const o = s.sources[k].options || {},
          where = o.path ? String(o.path).replace(/^~/, "~") : "",
          needs = !on && ["mail", "calendar"].includes(k);
        const lock = s.outside === false && !["mnema_chat", "corrections"].includes(k);
        return `<div class="srct ${on && !lock ? "on" : ""} ${lock ? "locked" : ""}" data-tile="${k}" style="--c1:${v[1]};--c2:${v[2]};--d:${n * 0.06}s">
        <span class="srctag">${esc(g)}</span><button class="sw ${on ? "on" : ""}" data-src="${k}" title="${on ? "Выключить" : "Включить"}"></button>
        <div class="medal2"><span>${v[0]}</span><i class="spark"></i><i class="spark"></i><i class="spark"></i></div>
        <b>${esc(m.name)}</b>${m.note ? `<p>${esc(m.note)}</p>` : ""}
        <div class="srcst">${lock ? `${ic("lock")}${tr("Закрыто: другие программы не смотрю")}` : on ? `<i></i>${tr(v[3])}` : needs ? tr(k === "mail" ? "нужны почта и пароль" : "нужна ссылка или файл") : tr("Не читает")}</div>
        ${on && where ? `<div class="srcwhere" title="${esc(where)}" data-noi18n>${esc(where)}</div>` : ""}
        ${srcOpts(k, o) && !lock ? `<button class="srcset2" data-sopt="${k}">${ic("set")}${tr(on ? "Настроить" : "Указать и включить")}</button>` : ""}</div>`;
      })
      .join("")}</div></div></div>
    <div class="card" data-sec="ai" id="c-other"><h2>${tr("Память в других ИИ")}<span class="hint">${tr("там будет та же память, по их правам доступа")}</span></h2><div class="aigrid" id="conngrid">${OUT_AI.map(([k, n, note]) => outTile(k, n, note, null)).join("")}</div></div>
    </div>${
      APP.desktop
        ? `<div class="card" data-sec="app" id="c-app"><div class="set"><b>Запуск</b><div class="tg" style="padding:0;border:0"><button class="sw ${APP.autostart ? "on" : ""}" id="autos"></button><div><b>Вместе с Windows</b><p>Учится в фоне, окно не открывает.</p></div></div></div>
    <div class="set"><b>Крестик окна</b><div>${seg("onclose", { ask: "спрашивать", tray: "сворачивать в трей", quit: "закрывать" }, APP.on_close || "ask")}</div></div></div>`
        : ""
    }`;
    $$("#st [data-seg]").forEach((sg) =>
      $$("button", sg).forEach(
        (b) =>
          (b.onclick = async () => {
            const k = sg.dataset.seg,
              v = b.dataset.v;
            if (k === "brain") await saveL({ brain: { kind: v } }, "Сохранено");
            else if (k === "onclose") {
              APP = await post("/api/app/close_pref", { value: v });
              toast("Сохранено");
            } else if (k === "gender") await save({ gender: v }, "Сохранено");
            else await save({ simple: { [k]: v } }, "Сохранено");
            again();
          }),
      ),
    );
    if ($("#oname")) {
      $("#oname").onchange = async (e) => {
        await save({ owner_name: e.target.value.trim() }, "Сохранено");
      };
      $("#oname").oninput = (e) => {
        const pv = $("#ypv");
        if (pv) pv.innerHTML = youPreview({ ...prof, owner_name: e.target.value }, ag);
        const av = $(".yav");
        if (av) av.textContent = (e.target.value.trim() || "?").slice(0, 1).toUpperCase();
      };
    }
    bindEngine();
    bindScribeCard();
    $("#secred").onclick = async (e) => {
      const b = e.currentTarget,
        on = !b.classList.contains("on");
      await save({ redact: on }, on ? "Секреты скрываются" : "Секреты уходят как есть");
      b.classList.toggle("on", on);
      refreshStatus();
    };
    $("#secout").onclick = () => outgoingModal(7);
    if ($("#secefs"))
      $("#secefs").onclick = async (e) => {
        const b = e.currentTarget,
          on = !b.classList.contains("on");
        if (
          on &&
          !confirm(
            tr(
              "Ключ шифрования живёт в твоей учётной записи Windows. Если переустановить Windows без сохранённого ключа восстановления, файлы памяти не открыть. После включения сохрани ключ восстановления. Включить?",
            ),
          )
        )
          return;
        b.disabled = true;
        try {
          const d = await post("/api/efs", { action: on ? "on" : "off" });
          toast(d.on ? tr("Папка памяти зашифрована") : tr("Шифрование выключено"));
          again();
        } catch (err) {
          toast(err.message);
          b.disabled = false;
        }
      };
    if ($("#secbk"))
      $("#secbk").onclick = async () => {
        const d = await post("/api/efs", { action: "backup" });
        toast(tr("Windows спросит пароль в отдельном окне. Ключ сохранится в") + " " + d.file);
      };
    $("#secacc").onclick = () => goSet("security/c-access");
    const rcomp = () => {
      const c = $("#compcard");
      if (c) {
        c.outerHTML = compCard();
        bindCompCard($("#compcard"), rcomp);
      }
    };
    bindCompCard($("#compcard"), rcomp);
    const rtheme = () => {
      const c = $("#themecard");
      if (c) {
        c.outerHTML = themeCard();
        bindThemeCard(rtheme);
      }
      drawThemeBtn();
    };
    bindThemeCard(rtheme);
    RTHEME = rtheme;
    $$("[data-pr]").forEach(
      (b) =>
        (b.onclick = async () => {
          await save({ preset: b.dataset.pr }, "Характер: " + $("b", b).textContent);
          again();
        }),
    );
    const onDefm = (e) => {
      CHAT.model = e.target.value;
      save({ default_model: e.target.value }, "Модель по умолчанию");
      const h = $("#c-model");
      if (h) {
        h.outerHTML = modelHero(ms, allModels, e.target.value);
        $("#defm").onchange = onDefm;
      }
    };
    if ($("#defm")) $("#defm").onchange = onDefm;
    $$("[data-src]").forEach(
      (b) =>
        (b.onclick = async () => {
          if (b.closest(".locked")) {
            toast(tr("Сначала разреши смотреть другие программы — переключатель выше"));
            return;
          }
          await saveL({ sources: { [b.dataset.src]: { enabled: !s.sources[b.dataset.src].enabled } } });
          again();
        }),
    );
    if ($("#outsw"))
      $("#outsw").onclick = async () => {
        await saveL(
          { outside: s.outside === false, found_asked: true },
          s.outside === false ? tr("Можно смотреть то, что включено") : tr("Только разговоры в Mnema и папка памяти"),
        );
        again();
      };
    $$("[data-tile]").forEach(
      (t) =>
        (t.onclick = (e) => {
          if (e.target.closest("input,select,textarea,button,label,a,.srcopts,.fld,.row")) return;
          const b = $("[data-src]", t);
          if (b) b.click();
        }),
    );
    $$("[data-sopt]").forEach(
      (b) =>
        (b.onclick = (e) => {
          e.stopPropagation();
          const k = b.dataset.sopt,
            src = s.sources[k],
            meta = (ls.sources || {})[k] || { name: k };
          const pop = document.createElement("div");
          pop.className = "modal srcm";
          document.body.appendChild(pop);
          pop.onclick = (ev) => {
            if (ev.target === pop) pop.remove();
          };
          pop.innerHTML = `<div class="card"><div class="cmhead"><div class="medal2 on" style="--c1:${(SRC_LOOK[k] || [])[1] || "#6d5ff5"};--c2:${(SRC_LOOK[k] || [])[2] || "#4fb6ff"};margin:0;width:44px;height:44px;font-size:22px;filter:none;opacity:1;background:linear-gradient(135deg,var(--c1),var(--c2))"><span>${(SRC_LOOK[k] || ["📘"])[0]}</span></div><div><h2>${esc(meta.name)}</h2><p>${esc(meta.note || "")}</p></div><button class="lmx" data-x>×</button></div>
        <div class="srcopts">${srcOpts(k, src.options)}</div><div class="row" style="justify-content:flex-end;margin-top:14px;gap:8px"><button class="btn g" data-x>${tr("Отмена")}</button><button class="btn" data-ok>${tr(src.enabled ? "Сохранить" : "Сохранить и включить")}</button></div></div>`;
          $$("[data-x]", pop).forEach((x) => (x.onclick = () => pop.remove()));
          $$("[data-pick]", pop).forEach(
            (x) =>
              (x.onclick = async () => {
                const pth = await window.pywebview.api.pick(x.dataset.kind || "folder");
                if (pth) x.parentElement.querySelector("input").value = pth;
              }),
          );
          $("[data-ok]", pop).onclick = async () => {
            const opts = {};
            $$("[data-opt]", pop).forEach((i) => (opts[i.dataset.opt] = i.type === "checkbox" ? i.checked : i.value));
            pop.remove();
            await saveL({ sources: { [k]: { enabled: true, options: opts } } }, tr("Сохранено"));
            again();
          };
        }),
    );
    $$("[data-opt]").forEach(
      (i) =>
        (i.onchange = () =>
          saveL(
            {
              sources: { [i.dataset.s]: { options: { [i.dataset.opt]: i.type === "checkbox" ? i.checked : i.value } } },
            },
            "Сохранено",
          )),
    );
    $$("[data-pick]").forEach(
      (b) =>
        (b.onclick = async () => {
          const p = await window.pywebview.api.pick(b.dataset.kind || "folder");
          if (p) {
            const i = b.parentElement.querySelector("input");
            i.value = p;
            i.onchange();
          }
        }),
    );
    if ($("#autos"))
      $("#autos").onclick = async () => {
        APP = await post("/api/app/autostart", { on: !APP.autostart });
        again();
      };
    bindTiles();
    bindProv();
  }
  {
    const [clients, et] = await Promise.all([api("/api/clients"), api("/api/ext_token")]);
    $("#st").insertAdjacentHTML(
      "beforeend",
      `
    <div class="card" data-sec="style" id="c-packs"><h2>Наборы <span class="hint">поделиться настройками без личных данных</span></h2><div class="row"><button class="btn l" id="exp">Скачать мой набор</button><label class="btn l" style="cursor:pointer">Загрузить набор<input type="file" id="imp" accept=".json" hidden></label></div></div>
    ${ag.catalog.map((sec, si) => `<div class="card adv-sec" data-sec="style" ${si ? "" : 'id="c-rules"'}><details><summary><h2>${esc(sec.title)} <span class="cnt">${sec.items.filter((i) => i.on).length} из ${sec.items.length}</span></h2></summary>${sec.items.map((i) => `<div class="tg"><button class="sw ${i.on ? "on" : ""}" data-tog="${i.id}" data-on="${i.on ? 1 : 0}"></button><div><b>${esc(i.title)}</b><p>${esc(i.rule)}</p></div></div>`).join("")}</details></div>`).join("")}
    <div class="card" data-sec="style" id="c-custom"><h2>Своими словами <span class="hint">добавится к правилам</span></h2><div class="fld"><textarea id="custom" placeholder="Например: про деньги всегда сначала спрашивай">${esc(prof.custom || "")}</textarea></div><div class="row" style="margin-top:8px"><button class="btn" id="csave">Сохранить</button></div></div>
    <div class="card" data-sec="learn" id="c-sources"><h2>Обучение по источникам${hq("learn")}</h2>${
      Object.entries(ls.sources)
        .filter(([k]) => s.sources[k].enabled)
        .map(
          ([k, m]) =>
            `<div class="set"><b>${esc(m.name)}</b><div>${seg("mode:" + k, ag.simple.autonomy.choices, s.sources[k].mode)}</div></div>`,
        )
        .join("") || '<p class="hint">Источники выключены.</p>'
    }
      <div class="set"><b>Записывать без вопроса при уверенности от, %</b><div class="fld" style="margin:0"><input id="auto" type="number" min="50" max="100" value="${Math.round(s.auto_confidence * 100)}"></div></div>
      <div class="set"><b>Предлагать забыть то, что не пригодилось, через (дней)</b><div class="fld" style="margin:0"><input id="fdays" type="number" min="7" value="${s.forget_after_days}"></div></div>
      <div class="set"><b>Не учиться на темах и словах</b><div><div class="lchips">${s.never.map((p, i) => `<label class="on">${esc(p)} <b data-nv="${i}">×</b></label>`).join("") || '<span class="hint">пусто</span>'}</div><div class="row" style="margin-top:8px"><input id="nva" class="inp" placeholder="тема или слово"><button class="btn l" id="nvb">Добавить</button></div></div></div>
      <div class="set"><b>Чем понимает тексты${hq("brain")}</b><div>${seg("brain", BRAINS, s.brain.kind)}<div class="hint" style="margin-top:6px">${esc(BRAIN_HINT[s.brain.kind])}${s.brain.kind === "auto" && br.using ? ` <b>${tr("Сейчас")}: ${esc(tr({ claude_code: "Claude по подписке", local: "встроенная модель", none: "только явное" }[br.using] || br.using))}</b>` : ""}</div>${br.level === "bad" ? `<div class="brain bad" style="margin-top:8px">${esc(br.message)}</div>` : ""}
        ${s.brain.kind === "api" ? `<div class="fld"><span>Провайдер</span><select id="bprov"><option value="anthropic" ${s.brain.provider === "anthropic" ? "selected" : ""}>Anthropic</option><option value="openai" ${s.brain.provider !== "anthropic" ? "selected" : ""}>Совместимый с OpenAI</option></select></div><div class="fld"><span>Ключ</span><input id="bkey" type="password" value="${esc(s.brain.api_key)}"></div>` : ""}
        ${!["none", "auto"].includes(s.brain.kind) ? `<div class="fld"><span>Модель</span><input id="bmodel" value="${esc(s.brain.model)}" placeholder="${s.brain.kind === "claude_code" ? "по умолчанию" : s.brain.kind === "ollama" ? "например, qwen2.5:14b" : "название модели"}"></div>` : ""}${s.brain.kind === "ollama" || s.brain.kind === "api" ? `<div class="fld"><span>Адрес, если не стандартный</span><input id="bend" value="${esc(s.brain.endpoint)}"></div>` : ""}
        <div class="row" style="margin-top:8px"><button class="btn l" id="btest">Проверить</button><span class="hint" id="bres"></span></div></div></div>
      <div class="row" style="margin-top:10px"><button class="btn" id="lsave">Сохранить</button><button class="btn l" id="lnow">Учиться сейчас</button><button class="btn g" id="lpause">${s.paused ? "Продолжить обучение" : "Пауза обучения"}</button></div></div>
    <div class="card" data-sec="security" id="c-access"><h2>Кто из ИИ что видит${hq("access")}<span class="accsaved" id="accsaved">${ic("check")}${tr("Сохранено")}</span></h2>
      <p class="hint" style="margin:-4px 0 12px">${tr("Галочка — эта часть памяти уходит этому ИИ вместе с вопросом. Замок — тема вырезается даже из разрешённых частей. Меняется сразу.")}</p>
      <div class="accwrap" id="accm">${accMatrix(clients)}</div></div>
    <div class="card" data-sec="style" id="promptcard"><h2>Рецепты задач${hq("prompts")}</h2><p class="hint" style="margin:-4px 0 10px">${tr("Делаешь что-то не в первый раз — отчёт по встрече, пост по заметкам, письмо клиенту? Mnema запишет рецепт: как именно ты это делаешь. Дальше просишь коротко — и она делает так же, без уточнений.")}</p>
      <div class="set"><b>${tr("Предлагать записать рецепт")}</b><div>${seg("pmode", { off: "никогда", second: "когда задача повторилась", every: "на каждую задачу" }, PRM_ST.mode)}</div></div>
      <div class="tg" style="padding:12px 0"><button class="sw ${PRM_ST.auto ? "on" : ""}" id="pauto"></button><div><b>${tr("Узнавать задачу и готовить по рецепту")}</b><p>${tr("Попросил знакомое — Mnema сама берёт рецепт, в ответе пометка «по рецепту». Выключено — рецепты лежат, но сама их не берёт.")}</p></div></div>
      <div class="set"><b>${tr("Мои рецепты")}</b><div>${PRM_ST.prompts.length ? `<div class="plist">${PRM_ST.prompts.map((x) => `<div class="pi"><div><b>${esc(x.name)}</b><span>${esc(x.when || "")} · использован ${x.uses} раз</span></div><button class="btn g sm" data-popen="${esc(x.file)}">Открыть</button><button class="btn g sm" data-pdel="${esc(x.file)}">Удалить</button></div>`).join("")}</div>` : '<span class="hint">пока нет — Mnema предложит первый, когда задача повторится</span>'}</div></div></div>
    <div class="card" data-sec="app" id="netcard"><h2>${tr("VPN и прокси")}</h2>
      <p class="hint" style="margin:-4px 0 12px">${tr("Если ИИ недоступны напрямую. По ключу Mnema подключается сама — приложение VPN для этого не нужно держать открытым. Через VPN идут только запросы Mnema, остальной компьютер он не трогает.")}</p>
      <div class="vkrow"><select class="inp" id="vksvc">${VK_SVCS.map((x) => `<option ${x === (prof.vpn_service || "Hiddify") ? "selected" : ""}>${esc(x)}</option>`).join("")}</select>
        <button class="btn" id="vkimp">${ic("copy")}${tr("Импортировать ключ")}</button><button class="btn g" id="vkman">${ic("edit")}${tr("Ввести ключ вручную")}</button></div>
      <div class="hint vkhint" id="vkhint"></div>
      <div class="vkbox" id="vkbox" hidden><textarea class="inp" id="vkkey" rows="3" placeholder="vless://…  vmess://…  trojan://…  ss://…  ${tr("или ссылка подписки")} https://…"></textarea><div class="row" style="margin-top:8px;gap:8px"><button class="btn" id="vkgo">${tr("Подключиться")}</button><span class="hint" id="vkmsg"></span></div></div>
      <div class="vkstat" id="vkstat"></div>
      <details class="vkold"><summary>${tr("Или через уже запущенный VPN (Hiddify, Happ…) или свой прокси")}</summary>${proxyForm(prof.vpn_key_on ? "" : prof.proxy || "", ag.proxy_password_set, ag.proxy_system)}</details>
      <div class="hint" style="margin-top:10px">${tr("Сейчас запросы идут")}: <b>${esc(ag.proxy_used || tr("напрямую"))}</b></div></div>
    <div class="card" data-sec="engine" id="c-economy"><h2>Экономия токенов${hq("economy")}</h2><div class="set"><b>Экономить на компьютере</b><div><div class="row" style="gap:10px"><button class="sw ${prof.economy !== false ? "on" : ""}" id="ecosw" title="Экономия токенов"></button></div></div></div>
      <div class="set"><b>Поиск в интернете${hq("web")}</b><div><div class="fld"><span>Ключ Brave Search, если хочешь стабильнее (необязательно)</span><input id="bravek" type="password" placeholder="${ag.brave_set ? "ключ сохранён" : "пусто — бесплатные поисковики"}"></div><div class="row" style="margin-top:8px"><button class="btn" id="bsave">Сохранить ключ</button>${ag.brave_set ? '<button class="btn g" id="bdel">Убрать ключ</button>' : ""}</div></div></div></div>
    <div class="card" data-sec="app" id="c-acts"><h2>${tr("Действия с файлами")}</h2>
      <div class="tg" style="padding:0 0 10px;border:0"><button class="sw ${prof.tools !== false ? "on" : ""}" id="actsw"></button><div><b>${tr("Модель может читать и создавать файлы")}</b><p>${tr("Читать, искать, создавать и править файлы, делать PDF, Word и Excel, записывать в память. Программы не запускаются, в интернет ничего не уходит. Любую запись можно откатить: «Память» → «История».")}</p></div></div>
      <div class="tg" style="padding:0 0 10px;border:0"><button class="sw ${prof.tools_ask ? "on" : ""}" id="actask-sw"></button><div><b>${tr("Спрашивать разрешение на каждое действие")}</b><p>${tr("Выключено: Mnema делает сразу. Каждая запись всё равно в журнале и откатывается в «Память» → «История».")}</p></div></div>
      <div class="set"><b>${tr("Где можно")}</b><div><div class="actfolders"><div class="actf"><span>${tr("Папка памяти")}</span><code data-noi18n>${esc(ACH.folder || "")}</code></div>${(prof.tool_folders || []).map((f, k) => `<div class="actf"><span>${tr("Рабочая папка")}</span><code data-noi18n>${esc(f)}</code><button class="btn g sm" data-actdel="${k}">${tr("Убрать")}</button></div>`).join("")}</div>
      <div class="row" style="margin-top:8px"><input id="actnew" class="inp" style="min-width:320px" placeholder="${tr("папка, где можно работать")}">${window.pywebview ? `<button class="btn l" id="actpick">${tr("Выбрать…")}</button>` : ""}<button class="btn" id="actadd">${tr("Добавить")}</button></div></div></div></div>
    <div class="card" data-sec="app" id="c-team"><h2>Общая память команды${hq("team")}</h2><div class="row"><input id="team" class="inp" style="min-width:380px" value="${esc(prof.team_vault || "")}" placeholder="папка общей памяти">${window.pywebview ? '<button class="btn l" id="tpick">Выбрать…</button>' : ""}<button class="btn" id="tsave">Сохранить</button></div></div>
    <div class="card" data-sec="ai" id="c-ext"><h2>Расширение для ChatGPT и Gemini${hq("extension")}</h2>
      <ol class="extsteps"><li>${tr("Нажми «Открыть папку расширения» — Mnema положит его на компьютер и откроет папку.")}</li>
      <li>${tr("В Chrome, Edge или Яндекс Браузере открой страницу расширений (chrome://extensions), включи «Режим разработчика».")}</li>
      <li>${tr("Нажми «Загрузить распакованное» и выбери эту папку. В настройках расширения вставь токен ниже.")}</li></ol>
      <div class="row" style="margin:6px 0 10px"><button class="btn sm" id="extopen">${tr("Открыть папку расширения")}</button></div>
      <code class="tok">${esc(et.token)}</code>${APP.port && APP.port != 7461 ? `<p class="hint">Порт приложения: <b>${APP.port}</b> — укажи его в настройках расширения.</p>` : ""}</div>`,
    );
    if ($("#extopen"))
      $("#extopen").onclick = async () => {
        try {
          const r = await post("/api/extension/open", {});
          toast(tr("Папка расширения") + ": " + r.folder, 6000);
        } catch (e) {
          toast(e.message, 6000);
        }
      };
    $("#exp").onclick = async () => {
      const p = await api("/api/agent/pack");
      const a = document.createElement("a");
      a.href = URL.createObjectURL(new Blob([JSON.stringify(p, null, 2)], { type: "application/json" }));
      a.download = "mnema-набор.json";
      a.click();
    };
    $("#imp").onchange = async (e) => {
      const f = e.target.files[0];
      if (!f) return;
      try {
        await post("/api/agent/pack", JSON.parse(await f.text()));
        toast("Набор загружен");
        again();
      } catch (err) {
        toast(err.message);
      }
    };
    $$("[data-tog]").forEach(
      (b) =>
        (b.onclick = async () => {
          const on = b.dataset.on !== "1";
          await save({ toggles: { [b.dataset.tog]: on } });
          b.dataset.on = on ? 1 : 0;
          b.classList.toggle("on", on);
          const sec = b.closest(".adv-sec");
          $(".cnt", sec).textContent = `${$$(".sw.on", sec).length} из ${$$(".sw", sec).length}`;
        }),
    );
    $("#csave").onclick = () => save({ custom: $("#custom").value }, "Сохранено");
    $$("#st .adv-only [data-seg],#c-sources [data-seg],#promptcard [data-seg]").forEach((sg) =>
      $$("button", sg).forEach(
        (b) =>
          (b.onclick = async () => {
            const k = sg.dataset.seg,
              v = b.dataset.v;
            if (k === "pmode") await save({ prompts_mode: v });
            else if (k === "brain") await saveL({ brain: { kind: v } });
            else if (k.startsWith("mode:")) await saveL({ sources: { [k.slice(5)]: { mode: v } } });
            again();
          }),
      ),
    );
    const collect = () => {
      const p = { auto_confidence: +$("#auto").value / 100, forget_after_days: +$("#fdays").value, brain: {} };
      for (const [id, k] of [
        ["bprov", "provider"],
        ["bkey", "api_key"],
        ["bmodel", "model"],
        ["bend", "endpoint"],
      ])
        if ($("#" + id)) p.brain[k] = $("#" + id).value;
      return p;
    };
    $("#lsave").onclick = async () => {
      await saveL(collect(), "Сохранено");
      again();
    };
    $("#lnow").onclick = async () => {
      await saveL(collect());
      try {
        await post("/api/learn/run", { initial: !s.initial.done });
        toast("Учусь. Что поняла — в ленте справа вверху");
      } catch (e) {
        toast(e.message);
      }
    };
    $("#lpause").onclick = async () => {
      await saveL({ paused: !s.paused }, s.paused ? "Обучение продолжается" : "Обучение на паузе");
      again();
    };
    $("#btest").onclick = async () => {
      $("#bres").textContent = "проверяю…";
      const r = await post("/api/learn/test_brain", collect());
      $("#bres").textContent = r.ok
        ? "Работает: " + r.found.join("; ")
        : "Не работает: " + (r.error || "ничего не нашла");
    };
    $$("[data-nv]").forEach(
      (x) => (x.onclick = () => saveL({ never: s.never.filter((_, i) => i != x.dataset.nv) }).then(again)),
    );
    $("#nvb").onclick = () => {
      const v = $("#nva").value.trim();
      if (v) saveL({ never: [...s.never, v] }, "Добавлено").then(again);
    };
    bindAcc(clients);
    if ($("#tpick"))
      $("#tpick").onclick = async () => {
        const p = await window.pywebview.api.pick("folder");
        if (p) $("#team").value = p;
      };
    $("#tsave").onclick = () => save({ team_vault: $("#team").value.trim() }, "Сохранено");
    const actFolders = prof.tool_folders || [];
    if ($("#actsw"))
      $("#actsw").onclick = async (e) => {
        const on = !e.currentTarget.classList.contains("on");
        e.currentTarget.classList.toggle("on", on);
        await save({ tools: on }, on ? "Действия с файлами включены" : "Действия с файлами выключены");
      };
    if ($("#actask-sw"))
      $("#actask-sw").onclick = async (e) => {
        const on = !e.currentTarget.classList.contains("on");
        e.currentTarget.classList.toggle("on", on);
        await save({ tools_ask: on }, on ? "Буду спрашивать перед действием" : "Действия — сразу, без вопросов");
      };
    if ($("#actpick"))
      $("#actpick").onclick = async () => {
        const p = await window.pywebview.api.pick("folder");
        if (p) $("#actnew").value = p;
      };
    if ($("#actadd"))
      $("#actadd").onclick = async () => {
        const v = $("#actnew").value.trim();
        if (!v) return toast(tr("Укажи папку"));
        await save({ tool_folders: [...actFolders, v] }, "Папка добавлена");
        viewSettings(SETCUR);
      };
    $$("[data-actdel]").forEach(
      (b) =>
        (b.onclick = async () => {
          await save({ tool_folders: actFolders.filter((_, k) => k !== +b.dataset.actdel) }, "Папка убрана");
          viewSettings(SETCUR);
        }),
    );
    if ($("#pauto"))
      $("#pauto").onclick = async (e) => {
        const on = !e.currentTarget.classList.contains("on");
        e.currentTarget.classList.toggle("on", on);
        await save({ prompts_auto: on });
      };
    $$("[data-popen]").forEach((b) => (b.onclick = () => post("/api/prompts/open", { file: b.dataset.popen })));
    $$("[data-pdel]").forEach(
      (b) =>
        (b.onclick = async () => {
          if (!confirm("Удалить рецепт?")) return;
          await post("/api/prompts/delete", { file: b.dataset.pdel });
          again();
        }),
    );
    bindVpnKey(prof);
    bindProxyForm($("#netcard"), async (url, pw, quiet) => {
      await save({ proxy: url, ...(pw !== null ? { proxy_password: pw } : {}) }, quiet ? "" : "Прокси сохранён");
      if (!quiet) again();
      else {
        const cur = $("#netcard .hint b:last-of-type");
      }
    });
    $("#ecosw").onclick = async (e) => {
      const on = !e.currentTarget.classList.contains("on");
      e.currentTarget.classList.toggle("on", on);
      await save({ economy: on }, on ? "Экономлю токены" : "Отправляю модели всё целиком");
    };
    $("#bsave").onclick = async () => {
      const k = $("#bravek").value.trim();
      if (!k) {
        toast("Вставь ключ");
        return;
      }
      await save({ brave_key: k }, "Ключ сохранён на этом компьютере");
      again();
    };
    if ($("#bdel"))
      $("#bdel").onclick = async () => {
        await save({ brave_key: "" }, "Ключ убран");
        again();
      };
  }
  decorateToggles($("#st"));
  showSec(sec, card);
  const pg = $(".page");
  if (pg && !card) pg.scrollTop = keep;
}
function srcOpts(k, o) {
  const f = (key, label, ph, kind) =>
    `<div class="fld"><span>${label}</span><div class="row"><input data-s="${k}" data-opt="${key}" value="${esc(o[key] ?? "")}" placeholder="${esc(ph)}" style="flex:1">${kind && window.pywebview ? `<button class="btn g sm" data-pick data-kind="${kind}">Выбрать…</button>` : ""}</div></div>`;
  const M = {
    claude_code: () => f("path", "Папка разговоров", "~/.claude/projects", "folder"),
    notes: () => f("path", "Папка заметок", "например, папка Obsidian", "folder"),
    chatgpt_export: () => f("path", "Файл conversations.json", "выгрузка ChatGPT", "file"),
    telegram: () => f("path", "Папка выгрузки", "Telegram Desktop → Экспорт → JSON", "folder"),
    mail: () =>
      f("host", "Сервер IMAP", "imap.gmail.com") +
      f("user", "Почта", "you@gmail.com") +
      `<div class="fld"><span>Пароль приложения</span><input type="password" data-s="mail" data-opt="password" value="${esc(o.password || "")}"></div>`,
    calendar: () => f("path", "Файл .ics или ссылка iCal", "секретная ссылка iCal из Google Календаря", "file"),
    documents: () => f("path", "Папка документов", "например, Документы", "folder"),
    browser_history: () =>
      `<div class="fld"><span>Браузер</span><select data-s="browser_history" data-opt="browser"><option value="">все найденные</option>${["Chrome", "Edge", "Яндекс Браузер"].map((b) => `<option ${o.browser === b ? "selected" : ""}>${b}</option>`).join("")}</select></div>`,
  };
  return M[k] ? M[k]() : "";
}
// brand look of every AI: glyph and two colours of the medal (the same tile for all, no one is first among equals)
const AI_LOOK = {
  local: ["💻", "#0ea5e9", "#22c55e"],
  claude_code: ["C", "#d97757", "#f4a582"],
  anthropic: ["A", "#b45309", "#e0915f"],
  openai: ["O", "#10a37f", "#4fd1a5"],
  gemini: ["✦", "#4285f4", "#9b8cf5"],
  openrouter: ["R", "#475569", "#94a3b8"],
  ollama: ["🦙", "#374151", "#9ca3af"],
  "claude-code": [">_", "#d97757", "#f4a582"],
  "claude-desktop": ["C", "#c2410c", "#fb923c"],
  cursor: ["⌘", "#1f2937", "#6b7280"],
  extension: ["🧩", "#10a37f", "#4285f4"],
};
const aiLook = (k, name) => AI_LOOK[k] || [(name || "?").slice(0, 1), "#64748b", "#94a3b8"];
const aiMedal = (k, name, cls = "") => {
  const [g] = aiLook(k, name);
  return `<span class="medal2 aimed ${cls}"><span data-noi18n>${esc(g)}</span><i class="spark"></i><i class="spark"></i><i class="spark"></i></span>`;
};
const OUT_AI = [
  ["claude-code", "Claude Code", "память в каждой сессии через MCP"],
  ["claude-desktop", "Claude Desktop", "память в приложении Claude через MCP"],
  ["cursor", "Cursor", "правила и проекты в редакторе через MCP"],
  ["extension", "ChatGPT и Gemini", "в браузере, через расширение Mnema для Chrome"],
];
// the AI that answers by default: a hero with its medal, the choice right there
function modelHero(ms, allModels, cur) {
  const pid = String(cur || "").split(":")[0],
    p = ms.providers.find((x) => x.id === pid) || {},
    opt = allModels.find((o) => o.v === cur) || allModels[0] || { l: "" },
    ready = ms.providers.filter((x) => x.ready).length,
    [, c1, c2] = aiLook(pid, p.name);
  return `<div class="card aihero" data-sec="ai" id="c-model" style="--c1:${c1};--c2:${c2}">
    <div class="aihl">${aiMedal(pid, p.name, "on")}<div><small>${tr("Сейчас отвечает")}</small><b>${esc(opt.l.split(" · ").pop() || p.name || "")}</b><span>${esc(p.name || "")}${p.note ? ` · ${esc(p.note)}` : ""}</span></div></div>
    <div class="aihr"><label for="defm">${tr("Модель по умолчанию")}${hq("models")}</label><select class="inp" id="defm">${allModels.map((o) => `<option value="${esc(o.v)}" ${o.v === cur ? "selected" : ""}>${esc(o.l)}</option>`).join("")}</select><small>${tr("Подключено")}: ${ready} ${tr("из")} ${ms.providers.length}. ${tr("В разговоре модель меняется сверху слева.")}</small></div></div>`;
}
const aiStatus = (on, txt) => `<span class="aist">${on ? "<i></i>" : ""}${txt}</span>`;
function provTile(p, n = 0) {
  const act =
    p.id === "local"
      ? `<button class="btn g sm" data-lm>${tr(p.ready ? "Другая модель" : "Выбрать и скачать")}</button>`
      : p.id === "claude_code"
        ? p.ready
          ? `<span class="aiok">${tr("работает без ключа")}</span>`
          : `<span class="hint">${tr("установи Claude Code")}</span>`
        : `<button class="btn g sm" data-more>${tr(p.needs_key ? (p.ready ? "Сменить ключ" : "Указать ключ") : "Указать адрес")}</button>`;
  const local = p.id === "local" && p.ready ? p.models.map((m) => m.name).join(", ") : "";
  const [, c1, c2] = aiLook(p.id, p.name);
  return `<div class="aitile ${p.ready ? "on" : ""}" data-p="${p.id}" ${p.id === "local" ? 'id="c-local"' : ""} style="--c1:${c1};--c2:${c2};--d:${n * 0.05}s">${aiStatus(p.ready, tr(p.ready ? "подключено" : "не подключено"))}
    ${aiMedal(p.id, p.name)}<b>${esc(p.name)}</b><small>${esc(local || p.note)}</small>
    <div class="aift">${act}</div>
    ${p.id === "local" || p.id === "claude_code" ? "" : `<div class="more" hidden>${p.needs_key ? `<input class="inp" type="password" placeholder="${tr("ключ")}" value="${esc(p.key)}" data-k>` : `<input class="inp" placeholder="http://127.0.0.1:11434" value="${esc(p.endpoint)}" data-e>`}<button class="btn sm" data-pk>${tr("Сохранить и найти модели")}</button><button class="btn g sm" data-less>${tr("Отмена")}</button></div>`}</div>`;
}
function outTile(k, name, note, on, n = 0) {
  const act =
    k === "extension"
      ? `<button class="btn g sm" data-ext>${tr("Показать токен")}</button>`
      : `<button class="btn g sm" data-con="${k}">${tr(on ? "Обновить" : "Подключить")}</button>`;
  const [, c1, c2] = aiLook(k, name);
  return `<div class="aitile out ${on ? "on" : ""}" data-out="${k}" style="--c1:${c1};--c2:${c2};--d:${n * 0.05}s">${aiStatus(on, k === "extension" ? tr("по токену") : on === null ? "…" : tr(on ? "подключено" : "не подключено"))}
    <span class="aipipe"><span class="aim">M</span><i></i>${aiMedal(k, name)}</span><b>${esc(name)}</b><small>${esc(tr(note))}</small>
    <div class="aift">${act}</div></div>`;
}
function bindTiles(fetch = true) {
  $$(".aitile [data-more]").forEach(
    (b) =>
      (b.onclick = () => {
        const t = b.closest(".aitile"),
          m = $(".more", t);
        m.hidden = !m.hidden;
        t.classList.toggle("editing", !m.hidden);
        if (!m.hidden) $("input", m).focus();
      }),
  );
  $$(".aitile [data-less]").forEach(
    (b) =>
      (b.onclick = () => {
        const t = b.closest(".aitile");
        $(".more", t).hidden = true;
        t.classList.remove("editing");
      }),
  );
  $$(".aitile [data-lm]").forEach((b) => (b.onclick = () => localModal()));
  $$(".aitile [data-ext]").forEach((b) => (b.onclick = () => goSet("ai/c-ext")));
  if (fetch)
    api("/api/connect")
      .then((st) => {
        const g = $("#conngrid");
        if (!g) return;
        g.innerHTML = OUT_AI.map(([k, n, note], i) => outTile(k, n, note, k === "extension" ? false : !!st[k], i)).join(
          "",
        );
        bindTiles(false);
      })
      .catch(() => {});
  bindCon();
  bindProv();
}
function bindCon() {
  $$("[data-con]").forEach(
    (b) =>
      (b.onclick = async () => {
        b.disabled = true;
        const r = await post("/api/connect", { target: b.dataset.con });
        b.disabled = false;
        toast(r.ok ? tr("Подключено. В новых сессиях там будет твоя память.") : tr("Не вышло") + ": " + r.message);
        if (r.ok) bindTiles();
      }),
  );
}
function provHtml(ps) {
  return ps
    .map(
      (
        p,
      ) => `<div class="prov" data-p="${p.id}"><div><b>${esc(p.name)}</b> <span class="hint">${esc(p.note)}</span></div><span class="${p.ready ? "ok" : "no"}">${p.ready ? "подключено" : "не подключено"}</span>
  <div class="more">${p.needs_key ? `<input class="inp" type="password" placeholder="ключ" value="${esc(p.key)}" data-k>` : `<input class="inp" placeholder="адрес, по умолчанию http://127.0.0.1:11434" value="${esc(p.endpoint)}" data-e>`}<button class="btn l sm" data-pk>Сохранить и найти модели</button>${p.models.length ? `<span class="hint">${p.models.length} моделей</span>` : ""}</div></div>`,
    )
    .join("");
}
function bindProv() {
  $$("[data-pk]").forEach(
    (b) =>
      (b.onclick = async () => {
        const row = b.closest("[data-p]"),
          id = row.dataset.p,
          k = $("[data-k]", row),
          e = $("[data-e]", row);
        b.disabled = true;
        b.textContent = "ищу модели…";
        await post("/api/providers", { id, key: k ? k.value : undefined, endpoint: e ? e.value : undefined });
        const r = await post("/api/providers/models", { id });
        b.disabled = false;
        b.textContent = "Сохранить и найти модели";
        toast(r.ok ? `Нашла моделей: ${r.models.length}` : "Не вышло: " + r.error);
        if (r.ok) viewSettings(SETCUR);
      }),
  );
}

// ---------------- model picker: every provider, connected or not
function modelLabel(v) {
  const [pid, mid] = String(v || "").split(/:(.*)/);
  const p = (CHAT.providers || []).find((x) => x.id === pid);
  if (!p || (CHAT.providers && !p.ready)) return tr("Нет модели — подключить");
  const m = p.models.find((x) => x.id === mid) || { name: mid || p.name };
  return pid === "claude_code"
    ? mid
      ? m.name
      : "Claude"
    : pid === "anthropic"
      ? m.name + " · ключ API"
      : pid === "local"
        ? m.name + " · на компьютере"
        : p.name + " · " + m.name;
}
const SPK_COLORS = ["#5b5bd6", "#0f8b8d", "#c76a12", "#b8327a"];
function spkColor(ref) {
  const m = (CHAT.cons && CHAT.cons.members) || [];
  const i = m.indexOf(ref);
  return SPK_COLORS[(i < 0 ? 0 : i) % SPK_COLORS.length];
}
function consName(ref) {
  const [pid, mid] = String(ref).split(/:(.*)/);
  if (pid === "claude_code")
    return (
      { "": "Claude", sonnet: "Claude Sonnet", opus: "Claude Opus", haiku: "Claude Haiku" }[mid || ""] ||
      "Claude " + mid
    );
  const p = (CHAT.providers || []).find((x) => x.id === pid);
  const m = p && p.models.find((x) => x.id === mid);
  if (pid === "local") return m ? m.name : mid;
  if (pid === "anthropic") {
    // "claude-sonnet-4-5" → "Claude Sonnet 4.5", as the server names it
    const out = [];
    for (const part of (mid || "claude").split("-")) {
      const prev = out[out.length - 1];
      if (/^\d{1,2}$/.test(part) && prev && /^[\d.]+$/.test(prev)) out[out.length - 1] = prev + "." + part;
      else out.push(/^\d+$/.test(part) ? part : part.charAt(0).toUpperCase() + part.slice(1));
    }
    return out.join(" ");
  }
  const base = { openai: "ChatGPT", gemini: "Gemini" }[pid];
  return base && mid ? base + " · " + mid : mid || pid;
}
const CONS_FORMATS = {
  council: {
    n: "Совет",
    d: "каждый отвечает, проверяют друг друга, в конце общий ответ",
    first: "own",
    middle: ["check", "better", "dispute"],
    last: "final",
    art: "⟲",
  },
  debate: {
    n: "Дебаты",
    d: "одни за, другие против, в конце вердикт",
    first: "pos",
    middle: ["rebut"],
    last: "verdict",
    art: "⇄",
  },
  brainstorm: {
    n: "Мозговой штурм",
    d: "идеи без критики, потом три лучшие",
    first: "ideas",
    middle: ["grow"],
    last: "best",
    art: "✦",
  },
  redteam: {
    n: "Красная команда",
    d: "ищут дыры в твоём плане и как их закрыть",
    first: "attack",
    middle: ["fix", "attack"],
    last: "risks",
    art: "⚑",
  },
};
const CONS_ROLES = {
  "": "Без роли",
  skeptic: "Скептик",
  practitioner: "Практик",
  finance: "Финансист",
  lawyer: "Юрист",
  creative: "Креативщик",
  analyst: "Аналитик",
  client: "Клиент",
};
const CONS_LEN = {
  short: ["Коротко", "до 80 слов"],
  normal: ["Обычно", "до 150 слов"],
  long: ["Развёрнуто", "до 300 слов"],
};
const CONS_STAGE = {
  pos: ["Позиции", "каждый защищает свою сторону 2–3 доводами"],
  rebut: ["Возражения", "отвечают на сильный довод другой стороны"],
  verdict: ["Вердикт", "честно взвешивают обе стороны"],
  ideas: ["Идеи", "по 3–5 идей, без критики"],
  grow: ["Развитие", "усиливают чужие идеи"],
  best: ["Лучшие идеи", "три лучшие: почему, первый шаг, риск"],
  attack: ["Атака", "ищут, что сломается в твоём плане"],
  fix: ["Как закрыть", "как закрыть самые опасные дыры"],
  risks: ["Риски и что делать", "список: риск, опасность, действие"],
  own: ["Свой ответ", "каждый отвечает на вопрос сам, прямо и по делу"],
  check: ["Проверка", "ищут слабые места в ответах друг друга"],
  better: ["Улучшение", "собирают лучший ответ из сильного у всех"],
  dispute: ["Спорное", "что не решено и как это решить"],
  final: ["Общий ответ", "ответ, с которым согласен весь совет"],
};
function consPlan(n, fmt) {
  fmt = CONS_FORMATS[fmt] ? fmt : "council";
  let keys;
  if (fmt === "council") {
    const P = { 1: ["own"], 2: ["own", "final"], 3: ["own", "check", "final"], 4: ["own", "check", "better", "final"] };
    keys =
      P[n] ||
      Array.from({ length: n }, (_, r) =>
        r === 0 ? "own" : r === n - 1 ? "final" : ["check", "better", "dispute"][(r - 1) % 3],
      );
  } else {
    const f = CONS_FORMATS[fmt];
    keys =
      n === 1
        ? [f.last]
        : Array.from({ length: n }, (_, r) =>
            r === 0 ? f.first : r === n - 1 ? f.last : f.middle[(r - 1) % f.middle.length],
          );
  }
  return keys.map((k) => CONS_STAGE[k]);
}
function consScheme(sel, fmt, summ) {
  const n = sel.length;
  if (n < 2) return `<div class="cschem empty">${tr("Выбери участников — здесь появится стол")}</div>`;
  const R = 62,
    C = 86,
    pts = sel.map((r, k) => {
      const a = -Math.PI / 2 + (k * 2 * Math.PI) / n;
      return [C + R * Math.cos(a), C + R * Math.sin(a)];
    });
  const sumr = summ && sel.includes(summ) ? summ : sel[n - 1];
  const arcs = pts
    .map((p, k) => {
      const q = pts[(k + 1) % n];
      return `<path d="M${p[0].toFixed(1)} ${p[1].toFixed(1)} A${R} ${R} 0 0 1 ${q[0].toFixed(1)} ${q[1].toFixed(1)}" style="--k:${k}"/>`;
    })
    .join("");
  const seats = sel
    .map((r, k) => {
      const [x, y] = pts[k],
        col = SPK_COLORS[k % SPK_COLORS.length],
        side = fmt === "debate" ? (k % 2 === 0 ? "за" : "против") : "";
      return `<div class="cseat" style="left:${x}px;top:${y}px;--sc:${col}"><b>${k + 1}</b>${r === sumr ? `<i class="ccrown">${ic("trophy")}</i>` : ""}${side ? `<em class="${k % 2 === 0 ? "cside-pro" : "cside-con"}">${tr(side)}</em>` : ""}</div>`;
    })
    .join("");
  return `<div class="cschem f-${fmt}"><svg viewBox="0 0 172 172">${arcs}</svg><div class="cschem-table"><span>${CONS_FORMATS[fmt].art}</span></div>${seats}</div>`;
}
async function consortModal(full = false) {
  await refreshProviders();
  const cur = CHAT.cons,
    edit = !!(CHAT.id && cur);
  const join = !!(
    CHAT.id &&
    !cur &&
    ((CHAT.chat || {}).messages || []).some((m) => m.role === "assistant" && !m.hidden)
  );
  const ready = (CHAT.providers || []).filter((p) => p.ready && p.models.length);
  if (ready.reduce((n, p) => n + p.models.filter((m) => m.id || p.id !== "claude_code").length, 0) < 2) {
    toast("Для консорциума нужны хотя бы два ИИ — подключи ещё один");
    modelMenu($("#model"));
    return;
  }
  let sel = cur ? [...cur.members] : join && CHAT.model && CHAT.model !== "consortium" ? [CHAT.model] : [],
    rounds = cur ? cur.rounds : 2;
  const def = LS.get("cons_def", {});
  let fmt = (cur && cur.format) || def.format || "council",
    roles = { ...(def.roles || {}), ...((cur && cur.roles) || {}) },
    summ = (cur && cur.summarizer) || "",
    len = (cur && cur.length) || def.length || "normal",
    look = cur ? cur.search !== false : def.search !== false,
    adv = !!full;
  const pop = document.createElement("div");
  pop.className = "modal cm";
  document.body.appendChild(pop);
  pop.onclick = (e) => {
    if (e.target === pop) pop.remove();
  };
  const draw = () => {
    const stg = consPlan(rounds, fmt),
      n = sel.length;
    if (summ && !sel.includes(summ)) summ = "";
    pop.innerHTML = adv
      ? `<div class="card cm2 ${adv ? "adv" : "simple"}"><div class="cmhead"><div class="cmic">${ic("users")}</div><div><h2>${join ? tr("Подключить консорциум к этому разговору") : tr("Консорциум — совет из нескольких ИИ")}${hq("consortium")}</h2>
      <p>${join ? tr("ИИ прочитают разговор выше и разберут твой последний вопрос, где прошлый ответ не помог.") : tr("Задаёшь вопрос — несколько ИИ разбирают его по кругам: каждый отвечает, проверяет других и вместе они приходят к одному ответу. Помогает, когда вопрос спорный или от ответа много зависит.")}</p></div><button class="lmx" id="cmx2">×</button></div>
     <div class="cmsec"><b>1. ${tr("Кто в совете")}</b>${hq("cons_members")}<span class="hint">${tr("от 2 до 4 · по порядку выступлений")}</span></div>
     <div class="cmgrid">${ready
       .map((p) =>
         p.models
           .filter((m) => m.id || p.id !== "claude_code")
           .slice(0, 8)
           .map((m) => {
             const r = p.id + ":" + m.id,
               k = sel.indexOf(r),
               on = k >= 0,
               col = on ? SPK_COLORS[k % SPK_COLORS.length] : "";
             return `<button class="cmm ${on ? "on" : ""}" data-r="${esc(r)}" style="${on ? "--sc:" + col : ""}"><span class="cmav">${on ? k + 1 : esc(consName(r).slice(0, 1))}</span><span class="cmt"><b data-noi18n>${esc(consName(r))}</b><small>${esc(provOf(r))}</small></span>${on ? ic("check") : ""}</button>`;
           })
           .join(""),
       )
       .join("")}
       <button class="cmm add" id="cmconnect"><span class="cmav">+</span><span class="cmt"><b>${tr("Подключить ещё ИИ")}</b><small>${tr("ChatGPT, Gemini, свои модели")}</small></span></button></div>
     <div class="cmsec"><b>2. ${tr("Сколько кругов")}</b>${hq("cons_rounds")}<span class="hint">${tr("больше кругов — глубже разбор и больше запросов")}</span></div>
     <div class="cmrounds">${[1, 2, 3, 4, 5].map((k) => `<button data-rk="${k}" class="${rounds === k ? "on" : ""}">${k}</button>`).join("")}<div class="stepper sm"><button data-st="-1" ${rounds <= 1 ? "disabled" : ""}>−</button><b>${rounds}</b><button data-st="1" ${rounds >= 20 ? "disabled" : ""}>+</button></div></div>
     <div class="cmsec"><b>3. ${tr("Как обсуждают")}</b>${hq("cons_format")}<span class="hint">${tr("формат задаёт, что делает каждый круг")}</span></div>
     <div class="cmfmt">${Object.entries(CONS_FORMATS)
       .map(
         ([k, f]) =>
           `<button data-fmt="${k}" class="${fmt === k ? "on" : ""}"><span class="fart f-${k}">${f.art}</span><b>${tr(f.n)}</b><small>${tr(f.d)}</small></button>`,
       )
       .join("")}</div>
     ${
       n
         ? `<div class="cmsec"><b>4. ${tr("Роли")}</b>${hq("cons_roles")}<span class="hint">${tr("с какой стороны каждый смотрит на вопрос")}</span></div>
     <div class="cmroles">${sel
       .map(
         (r, k) =>
           `<div class="cmrole" style="--sc:${SPK_COLORS[k % SPK_COLORS.length]}"><span class="cmav">${k + 1}</span><b data-noi18n>${esc(consName(r))}</b>${fmt === "debate" ? `<em class="${k % 2 === 0 ? "cside-pro" : "cside-con"}">${tr(k % 2 === 0 ? "за" : "против")}</em>` : ""}<select class="inp sm" data-role="${esc(r)}">${Object.entries(
             CONS_ROLES,
           )
             .map(([v, l]) => `<option value="${v}" ${(roles[r] || "") === v ? "selected" : ""}>${tr(l)}</option>`)
             .join("")}</select></div>`,
       )
       .join("")}</div>`
         : ""
     }
     <div class="cmsec"><b>${n ? 5 : 4}. ${tr("Итог и длина реплик")}</b>${hq("cons_sum")}<span class="hint">${tr("кто подводит итог и насколько подробно говорят")}</span></div>
     <div class="cmsum2"><div class="cmbox"><div class="cmbh">${ic("trophy")}<b>${tr("Итог подводит")}</b></div><div class="cmpick">${[
       ["", tr("последний по очереди"), ""],
       ...sel.map((r, k) => [r, consName(r), SPK_COLORS[k % SPK_COLORS.length], k + 1]),
     ]
       .map(
         ([v, l, col, num]) =>
           `<button data-summ="${esc(v)}" class="${summ === v ? "on" : ""}" style="${col ? "--sc:" + col : ""}"><span class="cmav ${v ? "" : "auto"}">${v ? num : ic("redo")}</span><span class="cmpl" data-noi18n>${esc(l)}</span>${summ === v ? ic("check") : ""}</button>`,
       )
       .join("")}</div></div>
       <div class="cmbox"><div class="cmbh">${ic("list")}<b>${tr("Реплики")}</b></div><div class="cmlen">${Object.entries(
         CONS_LEN,
       )
         .map(
           ([v, [l, h]], k) =>
             `<button data-len="${v}" class="${len === v ? "on" : ""}"><span class="lbars">${[0, 1, 2, 3]
               .slice(0, k + 2)
               .map((x) => `<i style="--w:${[100, 82, 92, 60][x]}%"></i>`)
               .join("")}</span><b>${tr(l)}</b><small>${tr(h)}</small></button>`,
         )
         .join("")}</div></div></div>
     <div class="cmsec"><b>${n ? 6 : 5}. ${tr("Проверка фактов")}</b>${hq("cons_search")}<span class="hint">${tr("участники сами ищут в интернете, чтобы подтвердить слова")}</span></div>
     <button class="cmsearch ${look ? "on" : ""}" id="cmlook"><span class="cmsico">${ic("globe")}</span><span class="cmst"><b>${tr("Искать в интернете")}</b><small>${look ? tr("до двух запросов за ход, источники под репликой") : tr("отвечают только из своих знаний")}</small></span><i class="sw ${look ? "on" : ""}"></i></button>
     <div class="cmsec"><b>${tr("Как пойдёт обсуждение")}</b></div>
     <div class="cmviz">${consScheme(sel, fmt, summ)}<div class="cmplan">${stg.map(([t, d], k) => `<div class="cmstep" style="--d:${k * 0.05}s"><span class="cmn">${k + 1}</span><div><b>${tr(t)}</b><small>${tr(d)}</small></div></div>`).join("")}
       <div class="cmstep fin"><span class="cmn">${ic("trophy")}</span><div><b>${tr("Итог")}</b><small>${summ && sel.includes(summ) ? esc(consName(summ)) + " — " + tr("отвечает на твой вопрос прямо: в чём сошлись и что советуют") : tr("последний выступающий отвечает на твой вопрос прямо: в чём сошлись и что советуют")}</small></div></div></div></div>
     <div class="cmfoot"><button class="btn g cmadvb" id="cmsimple">← ${tr("Проще")}</button><span class="hint">${n >= 2 ? `${tr("Выступлений")}: ${n} × ${rounds} = <b>${n * rounds}</b> · ${tr("вмешаться и поставить на паузу можно в любой момент")}` : tr("Выбери хотя бы двух участников")}</span>
       <div class="row" style="gap:8px">${edit ? `<button class="btn g" id="cmoff">${tr("Выйти из консорциума")}</button>` : ""}<button class="btn g" id="cmx">${tr("Отмена")}</button><button class="btn" id="cmgo" ${n < 2 ? "disabled" : ""}>${edit ? tr("Сохранить") : join ? tr("Обсудить этот разговор") : tr("Собрать совет")}</button></div></div></div>`
      : `<div class="card cm2 ${adv ? "adv" : "simple"}"><div class="cmhead"><div class="cmic">${ic("users")}</div><div><h2>${join ? tr("Подключить консорциум к этому разговору") : tr("Консорциум — совет из нескольких ИИ")}${hq("consortium")}</h2>
      <p>${join ? tr("ИИ прочитают разговор выше и разберут твой последний вопрос, где прошлый ответ не помог.") : tr("Задаёшь вопрос — несколько ИИ разбирают его по кругам: каждый отвечает, проверяет других и вместе они приходят к одному ответу. Помогает, когда вопрос спорный или от ответа много зависит.")}</p></div><button class="lmx" id="cmx2">×</button></div>
     <div class="cmsec"><b>1. ${tr("Кто в совете")}</b>${hq("cons_members")}<span class="hint">${tr("от 2 до 4 · по порядку выступлений")}</span></div>
     <div class="cmgrid">${ready
       .map((p) =>
         p.models
           .filter((m) => m.id || p.id !== "claude_code")
           .slice(0, 8)
           .map((m) => {
             const r = p.id + ":" + m.id,
               k = sel.indexOf(r),
               on = k >= 0,
               col = on ? SPK_COLORS[k % SPK_COLORS.length] : "";
             return `<button class="cmm ${on ? "on" : ""}" data-r="${esc(r)}" style="${on ? "--sc:" + col : ""}"><span class="cmav">${on ? k + 1 : esc(consName(r).slice(0, 1))}</span><span class="cmt"><b data-noi18n>${esc(consName(r))}</b><small>${esc(provOf(r))}</small></span>${on ? ic("check") : ""}</button>`;
           })
           .join(""),
       )
       .join("")}
       <button class="cmm add" id="cmconnect"><span class="cmav">+</span><span class="cmt"><b>${tr("Подключить ещё ИИ")}</b><small>${tr("ChatGPT, Gemini, свои модели")}</small></span></button></div>
     <div class="cmsec"><b>2. ${tr("Как обсуждают")}</b>${hq("cons_format")}<span class="hint">${tr("формат задаёт, что делает каждый круг")}</span></div>
     <div class="cmfmt">${Object.entries(CONS_FORMATS)
       .map(
         ([k, f]) =>
           `<button data-fmt="${k}" class="${fmt === k ? "on" : ""}"><span class="fart f-${k}">${f.art}</span><b>${tr(f.n)}</b><small>${tr(f.d)}</small></button>`,
       )
       .join("")}</div>
     <div class="cmprev">${consScheme(sel, fmt, summ)}<div class="cmprevt">${
       n >= 2
         ? `<b>${tr("Совет собран")}</b><div class="cmorder">${sel.map((r, k) => `<span style="--sc:${SPK_COLORS[k % SPK_COLORS.length]};--d:${k * 0.08}s"><i>${k + 1}</i><em data-noi18n>${esc(consName(r))}</em></span>`).join("")}</div><small>${tr(CONS_FORMATS[fmt].n)} · ${tr("кругов")}: ${rounds} · ${look ? tr("проверяют факты в интернете") : tr("без интернета")}</small>`
         : `<b>${tr("Выбери 2–4 ИИ")}</b><small>${tr("они сядут за стол и обсудят твой вопрос по очереди")}</small>`
     }</div></div>
     <div class="cmfoot"><button class="btn g cmadvb" id="cmadv">${ic("set")}${tr("Продвинутая настройка")}</button>
       <div class="row" style="gap:8px">${edit ? `<button class="btn g" id="cmoff">${tr("Выйти из консорциума")}</button>` : ""}<button class="btn g" id="cmx">${tr("Отмена")}</button><button class="btn" id="cmgo" ${n < 2 ? "disabled" : ""}>${edit ? tr("Сохранить") : join ? tr("Обсудить этот разговор") : tr("Собрать совет")}</button></div></div></div>`;
    if ($("#cmadv", pop))
      $("#cmadv", pop).onclick = () => {
        adv = true;
        draw();
        $(".cm2", pop).scrollTop = 0;
      };
    if ($("#cmsimple", pop))
      $("#cmsimple", pop).onclick = () => {
        adv = false;
        draw();
      };
    if ($("#cmlook", pop))
      $("#cmlook", pop).onclick = () => {
        look = !look;
        draw();
      };
    $$("[data-rk]", pop).forEach(
      (b) =>
        (b.onclick = () => {
          rounds = +b.dataset.rk;
          draw();
        }),
    );
    $$("[data-fmt]", pop).forEach(
      (b) =>
        (b.onclick = () => {
          fmt = b.dataset.fmt;
          draw();
        }),
    );
    $$("[data-summ]", pop).forEach(
      (b) =>
        (b.onclick = () => {
          summ = b.dataset.summ;
          draw();
        }),
    );
    $$("[data-len]", pop).forEach(
      (b) =>
        (b.onclick = () => {
          len = b.dataset.len;
          draw();
        }),
    );
    $$("[data-role]", pop).forEach(
      (x) =>
        (x.onchange = () => {
          roles[x.dataset.role] = x.value;
          draw();
        }),
    );
    if ($("#cmx2", pop)) $("#cmx2", pop).onclick = () => pop.remove();
    $$("[data-r]", pop).forEach(
      (c) =>
        (c.onclick = () => {
          const r = c.dataset.r;
          if (!sel.includes(r)) {
            if (sel.length >= 4) {
              toast(tr("Не больше четырёх"));
              return;
            }
            sel.push(r);
          } else sel = sel.filter((x) => x !== r);
          draw();
        }),
    );
    $$("[data-st]", pop).forEach(
      (b) =>
        (b.onclick = () => {
          rounds = Math.max(1, Math.min(20, rounds + +b.dataset.st));
          draw();
        }),
    );
    $("#cmx", pop).onclick = () => pop.remove();
    $("#cmconnect", pop).onclick = (e) => {
      e.preventDefault();
      pop.remove();
      modelMenu($("#model"));
    };
    if ($("#cmoff", pop))
      $("#cmoff", pop).onclick = () => {
        pop.remove();
        consAct("off");
      };
    $("#cmgo", pop).onclick = async () => {
      const rl = {};
      sel.forEach((r) => {
        if (roles[r]) rl[r] = roles[r];
      });
      const opts = { format: fmt, roles: rl, summarizer: summ, length: len, search: look },
        cfg = { members: sel, rounds, ...opts };
      pop.remove();
      LS.set("cons_def", {
        format: fmt,
        length: len,
        search: look,
        roles: { ...(LS.get("cons_def", {}).roles || {}), ...rl },
      });
      if (join) {
        try {
          await post("/api/chat/cons", { chat: CHAT.id, action: "start", members: sel, rounds, ...opts });
          const c = await api("/api/chat?id=" + CHAT.id);
          renderChat(c);
          $("#msgs").insertAdjacentHTML(
            "beforeend",
            `<div class="msg ai" id="live"><div class="av"></div><div><div class="md">${TYPING}</div></div></div>`,
          );
          scrollEnd();
          poll();
        } catch (e) {
          toast(e.message);
        }
      } else if (edit) {
        await consAct("set", { members: sel, rounds, ...opts });
      } else {
        CHAT.pendingCons = cfg;
        await viewChat();
        $("#inp").focus();
      }
    };
  };
  draw();
}
function drawModelLabel() {
  setTimeout(() => {
    drawChips();
    heatShow();
    drawTable();
  }, 0);
  drawState();
  const f = $("#mfree");
  const ready = (CHAT.providers || []).find((x) => x.id === String(CHAT.model || "").split(":")[0] && x.ready);
  if (f) f.textContent = CHAT.cons ? tr("несколько ИИ") : ready ? provOf(CHAT.model) : tr("скачай или укажи ключ");
  const l = $("#mlabel");
  if (l) l.textContent = CHAT.cons ? `Консорциум · ${CHAT.cons.members.length} ИИ` : modelLabel(CHAT.model);
  if ($("#model")) $("#model").classList.toggle("none", !CHAT.cons && !ready);
  const b = $("#conbtn");
  if (b) b.classList.toggle("on", !!CHAT.cons);
}
function provOf(v) {
  const pid = String(v || "").split(":")[0];
  return tr(
    {
      claude_code: "Claude по подписке",
      anthropic: "Anthropic · свой ключ",
      openai: "OpenAI",
      gemini: "Google Gemini",
      openrouter: "OpenRouter",
      ollama: "Ollama · на компьютере",
      local: "на этом компьютере",
    }[pid] || (pid ? pid : ""),
  );
}
function warmLocal(v) {
  if (!/^local:/.test(String(v || ""))) return;
  post("/api/local/warm", { model: v }).catch(() => {});
}
const SESSION_WARNED = {};
function setModel(v) {
  CHAT.model = v;
  drawModelLabel();
  warmLocal(v);
  if (v && v !== "consortium") post("/api/agent", { last_model: v }).catch(() => {});
  if (!CHAT.id && $(".startline")) renderEmpty();
}
async function refreshProviders() {
  CHAT.providers = (await api("/api/models")).providers;
  drawModelLabel();
}
function mHead(letter, name, status, on) {
  return `<div class="mh"><span class="mav ${on ? "on" : ""}">${esc(letter)}</span><b>${esc(name)}</b><span class="mst ${on ? "on" : ""}">${esc(tr(status))}</span></div>`;
}
function mRow(ref, name, meta, cur) {
  return `<button data-m="${esc(ref)}" class="mrow ${cur ? "cur" : ""}"><i class="rd"></i><span class="mn">${esc(name)}</span>${meta ? `<span class="mm">${esc(tr(meta))}</span>` : ""}</button>`;
}
function mAdd(pid, label) {
  return `<button class="mrow madd" data-p="${esc(pid)}"><i class="pl">${ic("plus")}</i><span class="mn">${esc(tr(label))}</span></button>`;
}
function modelMenu(anchor) {
  if ($(".mmenu")) {
    $(".mmenu").remove();
    return;
  }
  closeMenus();
  MENU_ANCHOR = anchor;
  const m = document.createElement("div");
  m.className = "mmenu menu mm2";
  // connected providers side by side as cards; not connected — one row of «+ connect» chips under them
  const P = CHAT.providers || [],
    cc = P.find((p) => p.id === "claude_code"),
    an = P.find((p) => p.id === "anthropic");
  const COL = {
    local: "#10b981",
    claude_code: "#d97757",
    anthropic: "#d97757",
    openai: "#10a37f",
    gemini: "#4f7cf7",
    openrouter: "#7c5cf0",
    ollama: "#334155",
  };
  const NM = {
    local: "На этом компьютере",
    claude_code: "Claude",
    openai: "ChatGPT",
    gemini: "Gemini",
    openrouter: "OpenRouter",
    ollama: "Ollama",
    anthropic: "Claude · ключ API",
  };
  const SUB = {
    local: "бесплатно, без интернета",
    claude_code: "по подписке",
    openai: "OpenAI · свой ключ",
    gemini: "Google · свой ключ",
    openrouter: "любые модели по одному ключу",
    ollama: "на компьютере",
    anthropic: "Anthropic · свой ключ",
  };
  const row = (ref, name) =>
    `<button data-m="${esc(ref)}" class="m2row ${ref === CHAT.model || (ref === "claude_code:sonnet" && CHAT.model === "claude_code:") ? "cur" : ""}"><i></i><span data-noi18n>${esc(name)}</span></button>`;
  const card = (p, models, extra) =>
    `<div class="m2card" style="--pc:${COL[p.id] || "#64748b"}"><div class="m2h"><span class="m2av">${esc((NM[p.id] || p.name).slice(0, 1))}</span><div><b>${tr(NM[p.id] || p.name)}</b><small>${tr(SUB[p.id] || "")}</small></div></div>${models}${extra || ""}</div>`;
  const ready = P.filter((p) => p.ready),
    order = ["local", "claude_code", "anthropic", "openai", "gemini", "openrouter", "ollama"];
  const items = ready
    .sort((a, b) => order.indexOf(a.id) - order.indexOf(b.id))
    .flatMap((p) => {
      const ms = p.id === "claude_code" ? p.models.filter((x) => x.id) : p.models;
      return ms.slice(0, p.id === "local" ? 6 : 5).map((x) => ({ ref: p.id + ":" + x.id, name: x.name, p }));
    });
  const more = ready.filter(
    (p) => (p.id === "claude_code" ? p.models.filter((x) => x.id) : p.models).length > (p.id === "local" ? 6 : 5),
  );
  const cards =
    items
      .map(
        ({ ref, name, p }) =>
          `<button data-m="${esc(ref)}" class="m3row ${ref === CHAT.model || (ref === "claude_code:sonnet" && CHAT.model === "claude_code:") ? "cur" : ""}" style="--pc:${COL[p.id] || "#64748b"}"><i></i><span data-noi18n>${esc(name)}</span><em>${tr(SUB[p.id] || p.name)}</em></button>`,
      )
      .join("") +
    (ready.some((p) => p.id === "local")
      ? `<button class="m2more" data-p="local">${tr("Другие модели на компьютере")}</button>`
      : "") +
    more
      .filter((p) => p.id !== "local")
      .map((p) => `<button class="m2more" data-p="${p.id}">${tr("Все модели")} ${esc(NM[p.id] || p.name)}</button>`)
      .join("");
  const add = P.filter((p) => !p.ready)
    .map(
      (p) =>
        `<button class="m2add" data-p="${p.id}" style="--pc:${COL[p.id] || "#64748b"}"><span>+</span>${tr(p.id === "local" ? "Скачать бесплатную модель" : p.id === "anthropic" ? "Ключ API Anthropic" : p.id === "claude_code" ? "Подписка Claude" : NM[p.id] || p.name)}</button>`,
    )
    .join("");
  m.innerHTML = `<div class="m3list">${cards || `<div class="hint" style="padding:10px">${tr("Пока ни одного ИИ не подключено")}</div>`}</div>${add ? `<div class="m2foot"><span>${tr("Подключить ещё")}</span><div>${add}</div></div>` : ""}`;
  document.body.appendChild(m);
  const r = anchor.getBoundingClientRect();
  m.style.left = Math.max(8, Math.min(window.innerWidth - m.offsetWidth - 8, r.left)) + "px";
  m.style.top = r.bottom + 6 + "px";
  $$("[data-m]", m).forEach(
    (b) =>
      (b.onclick = () => {
        m.remove();
        setModel(b.dataset.m);
      }),
  );
  $$("[data-p]", m).forEach(
    (b) =>
      (b.onclick = () => {
        m.remove();
        b.dataset.p === "local" ? localModal() : connectModal(b.dataset.p);
      }),
  );
}
const PROV_HOW = {
  claude_code: {
    t: "Нужны подписка Claude и установленный Claude Code от Anthropic. Mnema находит его сама — после установки нажми «Проверить снова».",
  },
  anthropic: { t: "Ключ берётся в кабинете разработчика Anthropic, раздел API Keys." },
  openai: {
    t: "Ключ берётся на platform.openai.com/api-keys — «Create new secret key».",
    u: "https://platform.openai.com/api-keys",
  },
  gemini: {
    t: "Ключ берётся в Google AI Studio: aistudio.google.com → Get API key.",
    u: "https://aistudio.google.com",
  },
  openrouter: { t: "Один ключ на сотни моделей разных компаний: openrouter.ai/keys.", u: "https://openrouter.ai/keys" },
  ollama: {
    t: "Нужна установленная и запущенная Ollama (ollama.com). Адрес по умолчанию — http://127.0.0.1:11434.",
    u: "https://ollama.com",
  },
};
async function connectModal(pid) {
  await refreshProviders();
  const p = CHAT.providers.find((x) => x.id === pid);
  if (!p) return;
  const pop = document.createElement("div");
  pop.className = "modal pm";
  document.body.appendChild(pop);
  pop.onclick = (e) => {
    if (e.target === pop) pop.remove();
  };
  const how = PROV_HOW[pid] || { t: "" };
  const draw = (models, msg) => {
    const list = models || p.models;
    pop.innerHTML = `<div class="card"><h2>${esc(p.name)} <span class="hint">${p.ready ? "подключено" : "не подключено"}</span></h2>
    <div class="how">${esc(how.t)}${how.u ? ` <a href="#" id="openu" style="color:var(--acc)">Открыть сайт</a>` : ""}</div>
    ${pid === "claude_code" ? "" : p.needs_key ? `<div class="fld"><span>Ключ API хранится в Windows, не в папке памяти</span><input id="pkey" type="password" placeholder="${p.key ? "сохранён " + esc(p.key) : "вставь ключ"}"></div>` : `<div class="fld"><span>Адрес</span><input id="pend" value="${esc(p.endpoint)}" placeholder="http://127.0.0.1:11434"></div>`}
    <div class="row" style="margin-top:10px"><button class="btn" id="pgo">${pid === "claude_code" ? "Проверить снова" : "Проверить и найти модели"}</button><span class="hint" id="pmsg">${esc(msg || "")}</span></div>
    ${list.length ? `<div class="fld" style="margin-top:12px"><span>Выбери модель (${list.length})</span><input id="pq" placeholder="поиск"></div><div class="mlist" id="pml">${list.map((x) => `<button data-pm="${esc(x.id || x)}">${esc(x.name || x)}</button>`).join("")}</div>` : ""}
    <div class="row" style="margin-top:12px;justify-content:flex-end"><button class="btn g sm" id="pclose">Закрыть</button></div></div>`;
    $("#pclose", pop).onclick = () => pop.remove();
    if ($("#openu", pop))
      $("#openu", pop).onclick = (e) => {
        e.preventDefault();
        post("/api/open_url", { url: how.u }).catch(() => toast(how.u));
      };
    if ($("#pq", pop))
      $("#pq", pop).oninput = (e) => {
        const q = e.target.value.toLowerCase();
        $$("[data-pm]", pop).forEach((b) => (b.hidden = !b.textContent.toLowerCase().includes(q)));
      };
    $$("[data-pm]", pop).forEach(
      (b) =>
        (b.onclick = async () => {
          await refreshProviders();
          pop.remove();
          setModel(pid + ":" + b.dataset.pm);
        }),
    );
    $("#pgo", pop).onclick = async () => {
      const k = $("#pkey", pop),
        e = $("#pend", pop);
      $("#pmsg", pop).textContent = "проверяю…";
      try {
        if (pid !== "claude_code")
          await post("/api/providers", {
            id: pid,
            key: k && k.value ? k.value : undefined,
            endpoint: e ? e.value : undefined,
          });
        if (pid === "claude_code") {
          await refreshProviders();
          const q = CHAT.providers.find((x) => x.id === pid);
          Object.assign(p, q);
          draw(null, q.ready ? "Claude Code найден — выбери модель" : "Claude Code пока не найден");
        } else {
          const r = await post("/api/providers/models", { id: pid });
          await refreshProviders();
          Object.assign(
            p,
            CHAT.providers.find((x) => x.id === pid),
          );
          draw(
            r.ok ? r.models.map((x) => ({ id: x, name: x })) : null,
            r.ok ? `Подключено: ${r.models.length} моделей` : "Не вышло: " + r.error,
          );
        }
      } catch (err) {
        $("#pmsg", pop).textContent = "Не вышло: " + err.message;
      }
    };
  };
  draw();
}

// ---------------------------------------------------------------- «Как отвечает»: tiles on the left, a live sample answer on the right
const YOU_LOOK = {
  soft: ["☕", "#f472b6", "#fb923c", 1],
  business: ["💼", "#6366f1", "#22d3ee", 2],
  strict: ["🛡️", "#10b981", "#0ea5e9", 3],
};
function youPreview(prof, ag) {
  const simple = prof.simple || {},
    vy = simple.address === "vy",
    len = simple.length || "normal",
    g = prof.gender || "",
    pr = prof.preset || "business",
    name = (prof.owner_name || "").trim();
  const hi = vy
    ? name
      ? `${esc(name)}, ${tr("добрый день")}.`
      : tr("Добрый день.")
    : name
      ? `${esc(name)}, ${tr("привет")}.`
      : tr("Привет.");
  const right = tr(
    vy ? "вы были правы" : g === "f" ? "ты была права" : g === "m" ? "ты был прав" : "оценка сроков точная",
  );
  const agree = tr(vy ? "согласуете" : "согласуешь");
  const body = {
    short: [`${tr("Да, успеваем")} — ${right}. ${tr("Осталось согласовать отдел.")}`],
    normal: [
      `${tr("Да, успеваем")} — ${right}. ${tr("Осталось два шага")}: ${tr("согласовать отдел и подготовить доступы")}. ${tr("Первое лучше закрыть на этой неделе.")}`,
    ],
    long: [
      `${tr("Да, успеваем, если до пятницы")} ${agree} ${tr("отдел")} — ${right}.`,
      `<ul><li>${tr("согласовать отдел — до пятницы")}</li><li>${tr("подготовить доступы — два дня")}</li><li>${tr("короткий инструктаж — в день старта")}</li></ul>`,
      `${tr("Риск один: отпуск руководителя в конце месяца.")}`,
    ],
  }[len];
  const extra =
    pr === "soft"
      ? `<p class="ypsoft">${tr("Всё получится, план реальный")} 🙂</p>`
      : pr === "strict"
        ? `<p class="ypchk">${ic("check")}${tr("Сверила с памятью: дата старта — из решения от 12 октября")}</p>`
        : "";
  return `<div class="yphead"><span>${tr("Пример ответа")}</span><small>${tr("меняется вместе с настройками")}</small></div>
    <div class="ypq">${tr("Успеваем запустить пилот к ноябрю?")}</div>
    <div class="ypa"><span class="ypav">M</span><div class="ypt"><p>${hi} ${body[0]}</p>${body
      .slice(1)
      .map((x) => (x.startsWith("<ul") ? x : `<p>${x}</p>`))
      .join("")}${extra}</div></div>
    <div class="yptags"><span>${vy ? tr("на вы") : tr("на ты")}</span><span>${esc((ag.simple.length.choices || {})[len] || "")}</span><span>${esc(((ag.presets || {})[pr] || {}).name || "")}</span></div>`;
}
function youCard(prof, ag) {
  const simple = prof.simple || {},
    name = (prof.owner_name || "").trim();
  const addr = [
    ["ty", tr("на ты"), name ? `${tr("Привет")}, ${name}!` : `${tr("Привет")}!`],
    ["vy", tr("на вы"), name ? `${tr("Здравствуйте")}, ${name}!` : `${tr("Здравствуйте")}!`],
  ];
  const lens = [
    ["short", tr("коротко"), tr("одна-две фразы"), 1],
    ["normal", tr("по делу"), tr("суть и шаги"), 3],
    ["long", tr("подробно"), tr("с разбором и рисками"), 5],
  ];
  const lines = (n) =>
    `<i class="ylines">${Array.from({ length: n }, (_, k) => `<em style="--w:${[92, 78, 86, 64, 72][k]}%;--k:${k}"></em>`).join("")}</i>`;
  const pr = prof.preset || "business";
  return `<div class="card ycard" data-sec="style" id="c-you">
    <div class="ytop">
      <div class="yform">
        <div class="yrow"><div class="ylab">${tr("Как тебя зовут")}</div><label class="yname"><span class="yav">${esc((name || "?").slice(0, 1).toUpperCase())}</span><input id="oname" value="${esc(name)}" placeholder="${tr("имя")}"></label></div>
        <div class="yrow"><div class="ylab">${tr("Обращение")}</div><div class="yopts y2" data-seg="address">${addr
          .map(
            ([k, l, ex]) =>
              `<button data-v="${k}" class="yt ${(simple.address || "ty") === k ? "on" : ""}"><b>${l}</b><span class="ybub">${esc(ex)}</span></button>`,
          )
          .join("")}</div></div>
        <div class="yrow"><div class="ylab">${tr("Длина ответа")}</div><div class="yopts y3" data-seg="length">${lens
          .map(
            ([k, l, h, n]) =>
              `<button data-v="${k}" class="yt ${(simple.length || "normal") === k ? "on" : ""}">${lines(n)}<b>${l}</b><small>${h}</small></button>`,
          )
          .join("")}</div></div>
        <div class="yrow"><div class="ylab">${tr("Пол")}<small>${tr("для окончаний: прав или права")}</small></div><div class="seg yseg" data-seg="gender">${[
          ["m", tr("мужской")],
          ["f", tr("женский")],
          ["", tr("не указывать")],
        ]
          .map(([k, l]) => `<button data-v="${k}" class="${(prof.gender || "") === k ? "on" : ""}">${l}</button>`)
          .join("")}</div></div>
      </div>
      <div class="ypv" id="ypv">${youPreview(prof, ag)}</div>
    </div>
    <div class="ychar"><div class="ylab">${tr("Характер")}${hq("presets")}</div><div class="yprs">${Object.entries(
      ag.presets,
    )
      .map(([k, p], n) => {
        const [em, c1, c2, lvl] = YOU_LOOK[k] || ["✨", "#6366f1", "#22d3ee", 2];
        return `<button data-pr="${k}" class="ypr ${pr === k ? "on" : ""}" style="--c1:${c1};--c2:${c2};--d:${n * 0.06}s"><span class="medal2"><span>${em}</span><i class="spark"></i><i class="spark"></i><i class="spark"></i></span><span class="yprt"><b>${esc(p.name)}</b><span>${esc(p.note)}</span><span class="ylvl">${tr("Проверки")}<i>${[1, 2, 3].map((x) => `<em class="${x <= lvl ? "f" : ""}"></em>`).join("")}</i></span></span>${pr === k ? `<span class="yok">${ic("check")}</span>` : ""}</button>`;
      })
      .join("")}</div></div>
  </div>`;
}
