// ---------------------------------------------------------------- the paper clip: a file, a screenshot, a note from memory, a page by link
function clipMenu(anchor) {
  if ($(".clipm")) {
    $(".clipm").remove();
    return;
  }
  closeMenus();
  MENU_ANCHOR = anchor;
  const m = document.createElement("div");
  m.className = "menu clipm";
  m.innerHTML =
    [
      ["file", "file", "Файл с компьютера", "PDF, Word, Excel, фото, аудио"],
      ["shot", "copy", "Скриншот из буфера", "сделай Win+Shift+S и нажми сюда"],
      ["note", "book", "Заметку из памяти", "карточку, проект, человека"],
      ["url", "globe", "Страницу по ссылке", "прочитаю и приложу текст"],
    ]
      .map(
        ([k, i, t, d]) => `<button data-c="${k}">${ic(i)}<span><b>${tr(t)}</b><small>${tr(d)}</small></span></button>`,
      )
      .join("") + `<div class="cliphint">${tr("Ещё можно перетащить файл в поле или вставить Ctrl+V")}</div>`;
  document.body.appendChild(m);
  const r = anchor.getBoundingClientRect();
  m.style.left = Math.max(8, r.left) + "px";
  m.style.top = r.top - m.offsetHeight - 8 + "px";
  $$("[data-c]", m).forEach(
    (b) =>
      (b.onclick = () => {
        m.remove();
        ({ file: () => $("#fpick").click(), shot: clipShot, note: clipNote, url: clipUrl })[b.dataset.c]();
      }),
  );
}
async function clipShot() {
  try {
    const items = await navigator.clipboard.read();
    for (const it of items) {
      const t = it.types.find((x) => x.startsWith("image/"));
      if (t) {
        const blob = await it.getType(t);
        addFiles([
          new File(
            [blob],
            "скриншот-" + new Date().toTimeString().slice(0, 5).replace(":", "-") + "." + (t.split("/")[1] || "png"),
            { type: t },
          ),
        ]);
        return;
      }
    }
    toast(tr("В буфере нет картинки. Сделай снимок Win+Shift+S и нажми ещё раз"), 4000);
  } catch (e) {
    toast(tr("Нет доступа к буферу. Вставь снимок в поле ввода сочетанием Ctrl+V"), 4000);
    $("#inp").focus();
  }
}
async function clipNote() {
  const all = (await api("/api/notes"))
    .filter((n) => !/^(90 System|95 Saves|99 Archive)\//.test(n.rel))
    .sort((a, b) => a.title.localeCompare(b.title));
  const pop = document.createElement("div");
  pop.className = "modal clipn";
  document.body.appendChild(pop);
  pop.onclick = (e) => {
    if (e.target === pop) pop.remove();
  };
  pop.innerHTML = `<div class="card"><div class="cmhead"><div class="cmic">${ic("book")}</div><div><h2>${tr("Приложить заметку из памяти")}</h2><p>${tr("ИИ увидит её целиком вместе с вопросом.")}</p></div><button class="lmx" data-x>×</button></div>
    <input class="inp" id="cnq" placeholder="${tr("Найти: проект, человек, тема…")}" style="width:100%"><div class="cnlist" id="cnl"></div></div>`;
  const list = (q) => {
    q = (q || "").toLowerCase();
    $("#cnl", pop).innerHTML =
      all
        .filter((n) => !q || n.title.toLowerCase().includes(q) || n.rel.toLowerCase().includes(q))
        .slice(0, 60)
        .map(
          (n) =>
            `<button data-r="${esc(n.rel)}"><b data-noi18n>${esc(n.title)}</b><small data-noi18n>${esc(n.rel.split("/").slice(0, -1).join(" / ") || "")}</small></button>`,
        )
        .join("") || `<div class="hint">${tr("Ничего не нашла")}</div>`;
    $$("[data-r]", pop).forEach(
      (b) =>
        (b.onclick = async () => {
          const t = await raw(b.dataset.r);
          pop.remove();
          addFiles([new File([t], ($("b", b).textContent || "заметка") + ".md", { type: "text/markdown" })]);
        }),
    );
  };
  list("");
  $("#cnq", pop).oninput = (e) => list(e.target.value);
  $("#cnq", pop).focus();
  $("[data-x]", pop).onclick = () => pop.remove();
}
function clipUrl() {
  const pop = document.createElement("div");
  pop.className = "modal clipn";
  document.body.appendChild(pop);
  pop.onclick = (e) => {
    if (e.target === pop) pop.remove();
  };
  pop.innerHTML = `<div class="card"><div class="cmhead"><div class="cmic">${ic("globe")}</div><div><h2>${tr("Приложить страницу по ссылке")}</h2><p>${tr("Mnema прочитает страницу у себя и приложит её текст к вопросу.")}</p></div><button class="lmx" data-x>×</button></div>
    <div class="row" style="gap:8px"><input class="inp" id="cuq" placeholder="https://…" style="flex:1"><button class="btn" id="cugo">${tr("Приложить")}</button></div><div class="hint" id="cum" style="margin-top:8px"></div></div>`;
  const go = async () => {
    const u = $("#cuq", pop).value.trim();
    if (!/^https?:\/\//.test(u)) {
      $("#cum", pop).textContent = tr("Нужна ссылка, начинающаяся с http");
      return;
    }
    $("#cum", pop).textContent = tr("читаю страницу…");
    $("#cugo", pop).disabled = true;
    try {
      const d = await post("/api/web/page", { url: u });
      pop.remove();
      addFiles([
        new File(
          [`${d.title}\n${d.url}\n\n${d.text}`],
          (d.title || "страница").slice(0, 60).replace(/[\\/:*?"<>|]/g, " ") + ".txt",
          { type: "text/plain" },
        ),
      ]);
      toast(tr("Страница приложена"));
    } catch (e) {
      $("#cum", pop).textContent = e.message;
      $("#cugo", pop).disabled = false;
    }
  };
  $("#cugo", pop).onclick = go;
  $("#cuq", pop).onkeydown = (e) => {
    if (e.key === "Enter") go();
  };
  $("#cuq", pop).focus();
  $("[data-x]", pop).onclick = () => pop.remove();
}
