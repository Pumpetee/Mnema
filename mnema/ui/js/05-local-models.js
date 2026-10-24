// ---------------------------------------------------------------- local models: why, and the owner's own model
function lmIntro(d, cloud) {
  const hw = d.hardware || {},
    fitN = d.catalog.filter((m) => m.fit === "ok").length,
    biggest = d.catalog.filter((m) => m.fit !== "no").sort((a, b) => b.size - a.size)[0];
  return `<div class="lmwhy">
   <div class="lw"><i class="lwi free">${ic("check")}</i><div><b>${tr("Бесплатно и навсегда")}</b><span>${tr("Без ключей и подписок. Работает без интернета, твои тексты не уходят с компьютера.")}</span></div></div>
   <div class="lw"><i class="lwi hw">${ic("gear")}</i><div><b>${tr("Ум и скорость зависят от компьютера")}</b><span>${tr("Модель считает на твоём процессоре и памяти. Чем мощнее компьютер, тем умнее модель можно взять и тем быстрее она ответит.")}</span>
     <div class="lwhw"><span>${tr("Память")} <b>${hw.ram_gb || "—"} ${tr("ГБ")}</b></span><span>${tr("Подходят без тормозов")}: <b>${fitN}</b></span>${biggest ? `<span>${tr("Самая большая, что потянет")}: <b>${esc(biggest.name)}</b></span>` : ""}</div></div></div>
   <div class="lw"><i class="lwi ins">${ic("shield")}</i><div><b>${tr("Страховка")}</b><span>${cloud ? tr("Облачный ИИ у тебя подключён — локальная модель будет запасной: когда нет интернета, кончился лимит или нельзя отправлять текст наружу.") : tr("Пока не подключён ни один облачный ИИ. С локальной моделью можно работать уже сейчас, а когда подключишь Claude или ChatGPT, она останется запасной.")}</span></div></div></div>`;
}
function lmAddCard() {
  return `<div class="lmod lmadd" id="lmadd"><span class="lv">${tr("Своя модель")}</span><div class="lmaddi">${ic("plus")}</div><b>${tr("Добавить свою модель")}</b><p>${tr("Любая модель в формате GGUF: файл с компьютера или ссылка с Hugging Face.")}</p><div class="act"><button class="btn l" id="lmaddb">${tr("Как добавить")}</button></div></div>`;
}
function lmAddPanel(pop, redraw) {
  if ($(".lmaddp", pop)) return;
  const box = document.createElement("div");
  box.className = "lmaddp";
  box.innerHTML = `<div class="lmaddh"><b>${tr("Как добавить свою модель")}</b><button class="lmx" data-x>×</button></div>
   <div class="lmsteps">
    <div class="ls"><div class="lsn">1</div><div class="lsart a1"><span class="lsurl">huggingface.co</span><span class="lssearch">${ic("search")}<em>Qwen GGUF</em></span></div><b>${tr("Найди модель")}</b><span>${tr("На huggingface.co в поиске набери название модели и слово GGUF.")}</span></div>
    <div class="ls"><div class="lsn">2</div><div class="lsart a2"><i>Q2_K · 1,1 ГБ</i><i class="hit">Q4_K_M · 2,5 ГБ</i><i>Q8_0 · 4,3 ГБ</i></div><b>${tr("Выбери файл Q4_K_M")}</b><span>${tr("Лучший баланс размера и качества. Смотри, чтобы размер был меньше половины памяти компьютера.")}</span></div>
    <div class="ls"><div class="lsn">3</div><div class="lsart a3"><span class="lslink">…/resolve/main/model-Q4_K_M.gguf</span><span class="lsok">${ic("check")}</span></div><b>${tr("Вставь ссылку или выбери файл")}</b><span>${tr("Скопируй адрес файла со страницы или скачай его сам и укажи здесь.")}</span></div>
   </div>
   <div class="row" style="margin-top:12px"><input class="inp" id="lmurl" placeholder="https://huggingface.co/…/model-Q4_K_M.gguf" style="flex:1;min-width:260px"><button class="btn" id="lmurlb">${tr("Скачать по ссылке")}</button></div>
   <div class="row" style="margin-top:8px"><button class="btn l" id="lmfile">${ic("folder")}${tr("Выбрать файл на компьютере…")}</button><span class="hint">${tr("Файл останется на месте, Mnema его не копирует и не удаляет.")}</span></div><div class="hint lmaddr"></div>`;
  $("#lmadd", pop).after(box);
  box.scrollIntoView({ block: "nearest", behavior: "smooth" });
  const res = (t) => {
    $(".lmaddr", box).textContent = t;
  };
  $("[data-x]", box).onclick = () => box.remove();
  $("#lmurlb", box).onclick = async () => {
    const u = $("#lmurl", box).value.trim();
    if (!u) return res(tr("Вставь ссылку на файл .gguf"));
    res(tr("проверяю ссылку…"));
    try {
      await post("/api/local/add_url", { url: u });
      box.remove();
      redraw();
    } catch (e) {
      res(e.message);
    }
  };
  $("#lmfile", box).onclick = async () => {
    let p = "";
    if (window.pywebview && pywebview.api && pywebview.api.pick) p = await pywebview.api.pick("file");
    else p = (await askText("Путь к файлу .gguf", "", "", "C:\\models\\model.gguf")) || "";
    if (!p) return;
    try {
      const m = await post("/api/local/add_file", { path: p });
      box.remove();
      redraw();
      toast(tr("Добавлена") + ": " + m.name);
    } catch (e) {
      res(e.message);
    }
  };
}
