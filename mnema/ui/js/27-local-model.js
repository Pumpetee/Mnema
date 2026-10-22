// ---------------------------------------------------------------- built-in local model
function mbps(bps) {
  return (
    (bps / 1e6).toLocaleString(locale(), { minimumFractionDigits: 1, maximumFractionDigits: 1 }) + " " + tr("МБ/с")
  );
}
function fmtSize(b) {
  return b >= 1e9
    ? (b / 1e9).toLocaleString(locale(), { minimumFractionDigits: 2, maximumFractionDigits: 2 }) + " " + tr("ГБ")
    : Math.round(b / 1e6) + " " + tr("МБ");
}
function fmtEta(s) {
  if (!s) return "";
  if (s < 60) return "меньше минуты";
  const m = Math.round(s / 60);
  return m < 60 ? m + " мин" : Math.floor(m / 60) + " ч " + (m % 60) + " мин";
}
let LM_T = null;
async function localModal(first, onClose) {
  if ($(".lm")) return;
  const pop = document.createElement("div");
  pop.className = "modal lm";
  document.body.appendChild(pop);
  const close = async (dismiss) => {
    clearTimeout(LM_T);
    pop.remove();
    if (dismiss) await post("/api/local/offer", { state: "dismissed" }).catch(() => {});
    if (onClose) onClose();
  };
  pop.onclick = (e) => {
    if (e.target === pop && !first) close(false);
  };
  let probed = false,
    cloud = false;
  try {
    const pv = await api("/api/models");
    cloud = pv.providers.some((p) => p.ready && p.id !== "local");
  } catch (e) {}
  const draw = async () => {
    let d;
    try {
      d = await api("/api/local" + (probed ? "" : "?probe=1"));
    } catch (e) {
      return;
    }
    probed = true;
    if (!document.body.contains(pop)) return;
    const dl = d.download,
      busy = dl.status === "downloading",
      bps = d.probe.bps;
    const DLBOX =
      busy || dl.status === "paused" || dl.status === "error"
        ? `<div class="dlbox" style="margin-bottom:6px"><b>${esc((d.catalog.find((x) => x.id === dl.id) || {}).name || "")}</b> — ${dl.status === "paused" ? "на паузе" : dl.status === "error" ? '<span style="color:var(--bad)">ошибка: ' + esc(dl.error) + "</span>" : "скачиваю"}
       <div class="bar"><i style="width:${dl.total ? Math.round((dl.done / dl.total) * 100) : 0}%"></i></div>
       <div class="nums"><span><b>${dl.total ? Math.round((dl.done / dl.total) * 100) : 0}%</b> · ${fmtSize(dl.done)} из ${fmtSize(dl.total)}</span><span>${busy && dl.bps ? mbps(dl.bps) + " · " + tr("осталось") + " " + fmtEta(dl.eta) : ""}</span></div>
       <div class="row" style="margin-top:8px">${busy ? '<button class="btn g sm" id="lmpause">Пауза</button>' : '<button class="btn sm" data-dl="' + dl.id + '">Продолжить</button>'}<button class="btn g sm" id="lmcancel">Отменить</button></div></div>`
        : "";
    const html = `<div class="card"><div class="lmhead"><h2>${first ? "Своя модель прямо на компьютере" : "Локальная модель"}${hq("models")}</h2><button class="lmx" id="lmx" title="Закрыть">×</button></div>
     ${lmIntro(d, cloud)}
     ${DLBOX}${(d.groups || [""])
       .map((g) => {
         const ms = d.catalog.filter((m) => !g || m.group === g);
         return ms.length
           ? `${g ? `<div class="lmg">${esc(g)}</div>` : ""}<div class="lmods">${ms
               .map(
                 (
                   m,
                 ) => `<div class="lmod ${m.recommended ? "rec" : ""}">${m.recommended ? '<span class="rb">советую</span>' : ""}<span class="lv">${esc(m.level)}</span><b>${esc(m.name)}</b><p>${esc(m.purpose)}</p>
       <div class="facts2"><span>Весит: <b>${fmtSize(m.size)}</b></span><span>Нужно памяти: <b>от ${m.ram_gb} ГБ</b></span><span>Скачается: <b>${m.installed ? "уже скачана" : m.eta ? "≈ " + fmtEta(m.eta) : d.probe.running || !d.probe.at ? "замеряю скорость…" : "—"}</b></span></div>
       <div class="fitc ${m.fit}">${esc(m.fit_why)}</div>
       <div class="act">${
         m.installed
           ? `<div class="inst"><span>✓ Скачана</span><button class="btn g sm" data-del="${m.id}">Удалить</button></div><button class="btn" data-use="${m.id}">Поговорить с ней</button>`
           : busy && dl.id === m.id
             ? `<button class="btn" disabled>Скачивается… ${dl.total ? Math.round((dl.done / dl.total) * 100) : 0}%</button>`
             : `<button class="btn ${m.recommended ? "" : "l"}" data-dl="${m.id}" ${busy || (m.fit === "no" && /диске/.test(m.fit_why)) ? "disabled" : ""}>${m.partial ? "Докачать" : "Скачать"} · ${fmtSize(m.size)}</button>`
       }</div></div>`,
               )
               .join("")}</div>`
           : "";
       })
       .join("")}
     <div class="lmods">${lmAddCard()}</div>
     <div class="lmfoot"><span class="hint">Компьютер: память ${d.hardware.ram_gb} ГБ · свободно на диске ${d.hardware.disk_free_gb} ГБ${bps ? " · " + tr("скорость интернета") + " " + mbps(bps) : ""}. Модели лежат в папке Mnema.</span>
       <button class="btn g sm" id="lmclose">${first ? "Не сейчас" : "Закрыть"}</button></div></div>`;
    if (html !== pop._html && !$(".lmaddp", pop)) {
      const c0 = $(".card", pop),
        keep = c0 ? c0.scrollTop : 0;
      pop.innerHTML = html;
      pop._html = html;
      const c1 = $(".card", pop);
      if (c1) c1.scrollTop = keep;
    } // redraw without jumping to the top
    $$("[data-dl]", pop).forEach(
      (b) =>
        (b.onclick = async () => {
          try {
            await post("/api/local/download", { id: b.dataset.dl });
            draw();
          } catch (e) {
            toast(e.message);
          }
        }),
    );
    if ($("#lmaddb", pop))
      $("#lmaddb", pop).onclick = () =>
        lmAddPanel(pop, () => {
          pop._html = "";
          draw();
        });
    $$("[data-del]", pop).forEach(
      (b) =>
        (b.onclick = async () => {
          if (!confirm("Удалить модель с компьютера?")) return;
          await post("/api/local/delete", { id: b.dataset.del });
          draw();
        }),
    );
    $$("[data-use]", pop).forEach(
      (b) =>
        (b.onclick = async () => {
          await post("/api/local/offer", { state: "done" });
          close(false);
          if (!$("#chatgrid")) {
            location.hash = "chat";
            await viewChat();
          } else await refreshProviders();
          CHAT.model = "local:" + b.dataset.use;
          drawModelLabel();
          if (!CHAT.id) renderEmpty();
          $("#inp") && $("#inp").focus();
        }),
    );
    if ($("#lmpause", pop))
      $("#lmpause", pop).onclick = async () => {
        await post("/api/local/pause");
        setTimeout(draw, 400);
      };
    if ($("#lmcancel", pop))
      $("#lmcancel", pop).onclick = async () => {
        await post("/api/local/cancel");
        draw();
      };
    $("#lmclose", pop).onclick = () => close(first);
    $("#lmx", pop).onclick = () => close(first);
    clearTimeout(LM_T);
    LM_T = setTimeout(draw, busy || d.probe.running || !d.probe.at ? 800 : 4000);
    if (dl.status === "done" && !pop._shown) {
      pop._shown = 1;
      const m = d.catalog.find((x) => x.id === dl.id) || {};
      clearTimeout(LM_T);
      pop._html = "";
      pop.innerHTML = `<div class="card"><div class="lmdone"><div class="ok">✓</div><div class="big">Всё установлено и готово</div><p class="sub2">Модель: <b>${esc(m.name || "")}</b> · работает на этом компьютере, без интернета и ключей.</p>
        <div class="row" style="justify-content:center"><button class="btn" id="lmuse">Выбрать её для чата</button><button class="btn g" id="lmmore">К списку моделей</button></div></div></div>`;
      $("#lmuse", pop).onclick = async () => {
        await post("/api/local/offer", { state: "done" });
        close(false);
        if (!$("#chatgrid")) {
          location.hash = "chat";
          await viewChat();
        } else await refreshProviders();
        CHAT.model = "local:" + m.id;
        drawModelLabel();
        if (!CHAT.id) renderEmpty();
        $("#inp") && $("#inp").focus();
      };
      $("#lmmore", pop).onclick = () => {
        pop._shown = 1;
        post("/api/local/cancel").then(draw);
      };
    }
  };
  pop.innerHTML =
    '<div class="card"><h2>Локальная модель</h2><p class="sub2">Проверяю компьютер и скорость интернета…</p></div>';
  draw();
}
