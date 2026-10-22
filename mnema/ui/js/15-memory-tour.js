// ---------------------------------------------------------------- the memory guide: chapters on the left, a big scene, an example and a way to check it yourself
const MEMTOUR = [
  {
    t: "Твоя память — папка на этом компьютере",
    d: "Mnema хранит всё обычными файлами у тебя. Их можно открыть, поправить или удалить в любой момент. Своего облака у Mnema нет.",
    ex: [
      [
        "note",
        "Открой папку — внутри обычные .md файлы: профиль, проекты, люди, правила. Их читает любой редактор, в том числе Obsidian.",
      ],
    ],
    try: ["folder", "Открыть папку памяти"],
    scene: `<div class="ms ms1"><div class="msfold">${"📁"}</div><div class="msfile f1">Профиль.md</div><div class="msfile f2">Проекты</div><div class="msfile f3">Люди</div><div class="msfile f4">Правила.md</div><div class="mspc">💻 <span>этот компьютер</span></div></div>`,
  },
  {
    t: "Как устроена папка памяти",
    d: "У каждого вида знаний своя папка. Факт — одна строка с датой. Новый статус заменяет старый, а старый уходит в архив фактов. Тег #money прячет раздел от облачных ИИ.",
    ex: [
      ["you", "Бюджет теперь 150 тысяч"],
      ["mem", "Карточка «Деньги»: 100 тыс. → 150 тыс., старая строка — в архиве фактов"],
    ],
    try: ["files", "Посмотреть файлы памяти"],
    scene: `<div class="ms ms8"><div class="mstree">${[
      ["📥", "00 Inbox", "неразобранное", ""],
      ["📌", "10 Now.md", "сводка на сегодня", ""],
      ["📁", "20 Projects", "проекты и их документы", ""],
      ["👤", "30 People", "люди", ""],
      ["🗓", "60 Events", "решения по месяцам", ""],
      ["🧠", "70 Memory", "профиль, правила, мысли", ""],
      ["", "Cards", "карточки тем", "tsub thot"],
      ["", "Fact archive", "заменённые факты", "tsub tarc"],
      ["🎙", "80 Meetings", "встречи", ""],
      ["⚙", "90 System", "журнал и рецепты", ""],
      ["💾", "95 Saves", "копии до правки", ""],
      ["🗄", "99 Archive", "закрытые проекты", ""],
    ]
      .map(
        ([e, n, h, c], i) =>
          `<i class="${c}" style="--i:${i}"><b>${c.includes("tsub") ? "└" : e} ${n}</b><span>${h}</span></i>`,
      )
      .join(
        "",
      )}</div><div class="msfcard"><div class="mshd">Cards/<span>Деньги</span>.md</div><div class="mstag">## Бюджет <em>#money 🔒</em></div><div class="msslot"><span class="old">- 01.09.2026 · Бюджет 100 тыс.</span><span class="new">- 21.10.2026 · Бюджет 150 тыс.</span></div><div class="msarc">🗄 Fact archive<span>01.09.2026 · Бюджет 100 тыс.</span></div></div></div>`,
  },
  {
    t: "Дата факта — когда ты это сказал",
    d: "Mnema ставит дату твоего сообщения, а не дату, когда она его прочитала. Переписка месячной давности не выдаётся за новость, а решение попадает в события того месяца.",
    ex: [
      [
        "note",
        "Сегодня Mnema прочитала выгрузку Telegram за сентябрь: «Переехал в Казань» записано с датой 12.09, а не сегодняшней.",
      ],
    ],
    try: ["history", "Открыть историю памяти"],
    scene: `<div class="ms ms9"><div class="m9msg"><small>Telegram · 12 сентября</small><span>Переехал в Казань</span></div><div class="m9read"><i></i><small>прочитано сегодня</small></div><div class="m9fact"><small>70 Memory/Profile.md</small><span><b>12.09.2026</b> · Живёт в Казани</span><em>60 Events/2026-09.md</em></div></div>`,
  },
  {
    t: "Ты говоришь — Mnema учится",
    d: "Из разговоров она замечает факты, решения и правила. Уверенное записывает сама, спорное и личное — спрашивает. Всё видно в ленте «Что поняла».",
    ex: [
      ["you", "Пилот запускаем 3 ноября в Казани"],
      ["mem", "Проекты: пилот — 3 ноября, Казань"],
    ],
    try: ["learn", "Где Mnema учится"],
    scene: `<div class="ms ms2"><div class="msbub">Пилот запускаем 3 ноября в Казани</div><div class="msspark">✨</div><div class="mscard">📌 <b>Проекты</b><span>Пилот — 3 ноября, Казань</span></div><div class="msmem">🧠 память</div></div>`,
  },
  {
    t: "Записать сразу или спросить",
    d: "У каждого факта своя уверенность. От 80% и не личное — Mnema записывает сама. От 60 до 80% — спрашивает одним вопросом под разговором. Ниже — ждёт, пока встретится ещё раз: два раза по 60% дают 84%.",
    ex: [
      ["you", "Кажется, с декабря перейду на четыре дня в неделю"],
      ["ask", "Запомнить, что с декабря ты работаешь четыре дня в неделю?"],
    ],
    try: ["learn", "Насколько сама учится"],
    scene: `<div class="ms ms10"><div class="m10bar"><i class="z1"><small>жду повтора</small></i><i class="z2"><small>спрошу</small></i><i class="z3"><small>запишу сама</small></i><b class="t60">60%</b><b class="t80">80%</b></div><em class="m10d d1" style="--x:91%">«По пятницам из дома» · 92%</em><em class="m10d d2" style="--x:62%">«Кажется, переезжаю» · 70%</em><em class="m10d d3" style="--x:24%">«Может, бросить кофе» · 50%</em></div>`,
  },
  {
    t: "Поправки становятся правилами",
    d: "Если ты поправляешь ответ, Mnema понимает, что так делать не надо, и записывает правило. Дальше его получает каждый ИИ — не нужно повторять одно и то же в каждом чате.",
    ex: [
      ["you", "Нет, слишком длинно. Пиши короче и без таблиц."],
      ["mem", "Правило: отвечать коротко, без таблиц"],
    ],
    try: ["rules", "Открыть правила для ИИ"],
    scene: `<div class="ms ms11"><div class="m11ai"><span class="ln"></span><span class="ln"></span><span class="ln"></span><span class="ln s"></span><span class="ln"></span><span class="ln s"></span></div><div class="m11me">Нет, короче и без таблиц</div><div class="m11rule"><small>70 Memory/Rules.md</small><span>- Отвечай коротко, без таблиц <em>выучено</em></span></div></div>`,
  },
  {
    t: "Перед ответом — только нужное",
    d: "ИИ получает не всю память, а только то, что относится к вопросу. Остальное остаётся на компьютере — и токенов уходит меньше.",
    ex: [
      ["you", "Когда пилот?"],
      ["note", "К вопросу ушли две строки: дата пилота и город. Здоровье, деньги и хобби остались на компьютере."],
    ],
    scene: `<div class="ms ms3"><div class="msq">Когда пилот?</div><div class="msstack"><i>Здоровье</i><i class="hot">Пилот — 3 ноября</i><i>Деньги</i><i class="hot">Казань, 3 автосервиса</i><i>Хобби</i></div><div class="msai">🤖</div></div>`,
  },
  {
    t: "Каждому ИИ — свои права",
    d: "Деньги, здоровье и личное скрыты от облачных ИИ. Модель на компьютере видит всё — она ничего не отправляет. Меняется в таблице «Кто что видит».",
    ex: [
      [
        "note",
        "Спросишь ChatGPT про бюджет — он не увидит карточку «Деньги». Модель на компьютере ответит, она ничего не отправляет наружу.",
      ],
    ],
    try: ["access", "Кто из ИИ что видит"],
    scene: `<div class="ms ms4"><div class="mscoin">💰 Деньги</div><div class="msais"><span class="ok">💻<small>на компьютере</small></span><span class="no">✳<small>Claude</small></span><span class="no">◎<small>ChatGPT</small></span></div></div>`,
  },
  {
    t: "Секреты не уходят",
    d: "Номера карт, пароли, ключи и телефоны заменяются метками до отправки. В ответе Mnema подставляет настоящие значения уже у тебя.",
    ex: [
      ["you", "Оплати картой 4276 1300 2468 5512"],
      ["note", "Облачный ИИ увидел [КАРТА-1]. В ответе у тебя на экране снова настоящий номер."],
    ],
    try: ["out", "Что ушло наружу"],
    scene: `<div class="ms ms5"><div class="mssec"><span class="real">4276 1300 2468 5512</span><span class="mask">[КАРТА-1]</span></div><div class="msarrow">→ ☁️ →</div><div class="msback">Оплати картой <span class="mask2">[КАРТА-1]</span><span class="real2">4276 …5512</span></div></div>`,
  },
  {
    t: "Старое — переспросит, а не выдумает",
    d: "Mnema знает дату каждого статуса. Если разговор касается статуса старше месяца, она скажет, от какой он даты, и уточнит, в силе ли он.",
    ex: [
      ["you", "Сколько компаний в пилоте?"],
      ["say", "По памяти цель — пять компаний, но это статус от 1 августа. Он ещё в силе?"],
    ],
    scene: `<div class="ms ms12"><div class="m12card"><small>20 Projects/Mnema</small><span>Цель — пять компаний в пилоте</span><em>статус 01.08.2026</em><b class="m12age">больше месяца</b></div><div class="m12ask">Это от 1 августа. Ещё в силе?</div></div>`,
  },
  {
    t: "Всё под контролем",
    d: "Каждое изменение памяти записано в историю: кто, что и когда. Любое откатывается одним нажатием, а откат выученного значит «нет» — это не вернётся.",
    ex: [
      [
        "note",
        "Mnema записала лишнее — в «Истории» нажми «Откатить». Строка исчезнет, и Mnema больше этому не учится.",
      ],
    ],
    try: ["history", "Открыть историю"],
    scene: `<div class="ms ms6"><div class="mstl"><i><b>14:02</b> записала: пилот 3 ноября</i><i class="undo"><b>14:05</b> записала: созвоны до обеда <em>Откатить</em></i><i><b>14:11</b> ты поправил: Казань</i></div></div>`,
  },
  {
    t: "Модель на компьютере — ничего не уходит",
    d: "Встроенная модель работает без интернета. Такой разговор вообще не покидает компьютер — даже то, что разрешено облачным ИИ.",
    ex: [["note", "Выбери встроенную модель сверху слева в чате — и можно говорить о деньгах и здоровье без облака."]],
    try: ["local", "Встроенная модель"],
    scene: `<div class="ms ms7"><div class="mslap">💻<span class="chip">🧠</span></div><div class="mswifi">📶<i></i></div></div>`,
  },
];
const MT_WHO = { you: "Ты", say: "Mnema", ask: "Mnema спросит", mem: "В памяти" };
const MT_TRY = {
  folder: () => post("/api/memory/open").catch((e) => toast(e.message)),
  files: () => (location.hash = "memory/files"),
  history: () => (location.hash = "memory/history"),
  rules: async () => {
    location.hash = "memory/portrait";
    for (let n = 0; n < 30 && !$(".rcard"); n++) await new Promise((r) => setTimeout(r, 100));
    const c = $(".rcard");
    if (c) c.scrollIntoView({ behavior: "smooth", block: "start" });
  },
  learn: () => goSet("learn/c-learn"),
  access: () => goSet("security/c-access"),
  out: () => outgoingModal(7),
  local: () => goSet("ai/c-prov"),
};
function memTour() {
  const pop = document.createElement("div");
  pop.className = "modal mtour";
  document.body.appendChild(pop);
  let k = 0;
  const N = MEMTOUR.length;
  const close = () => {
      pop.remove();
      removeEventListener("keydown", key);
    },
    key = (e) => {
      if (e.key === "ArrowRight") go(1);
      else if (e.key === "ArrowLeft") go(-1);
      else if (e.key === "Escape") close();
    };
  addEventListener("keydown", key);
  pop.onclick = (e) => {
    if (e.target === pop) close();
  };
  const go = (d) => {
    k = Math.max(0, Math.min(N, k + d));
    draw();
  };
  const side = () =>
    `<aside class="mtside"><div class="mtsh"><b>${tr("Гид по памяти")}</b><small>${N} ${tr("глав")}</small></div><ol class="mtch">${MEMTOUR.map(
      (s, i) =>
        `<li><button data-i="${i}" class="${i === k ? "on" : i < k ? "done" : ""}"><em>${i < k ? ic("check") : i + 1}</em><span>${esc(tr(s.t))}</span></button></li>`,
    ).join(
      "",
    )}<li><button data-i="${N}" class="${k === N ? "on" : ""}"><em>🎉</em><span>${tr("Проверь сам")}</span></button></li></ol></aside>`;
  const exHtml = (ex) =>
    ex && ex.length
      ? `<div class="mtex"><div class="mtexh">${tr("Пример")}</div>${ex
          .map(([w, t]) =>
            w === "note"
              ? `<p class="mtnote">${esc(tr(t))}</p>`
              : `<div class="mtl k-${w}"><span>${tr(MT_WHO[w])}</span><p>${esc(tr(t))}</p></div>`,
          )
          .join("")}</div>`
      : "";
  const draw = () => {
    let main;
    if (k === N) {
      main = `<div class="mtmain mtfinal"><div class="mtstep">${tr("Готово")}</div><div class="mtdone">🎉</div><h2>${tr("Теперь ты знаешь, как устроена память")}</h2><p class="mtd">${tr("Проверить всё можно самому:")}</p>
        <div class="mtfin"><button data-a="folder">${ic("folder")}<span><b>${tr("Открыть папку")}</b><small>${tr("файлы памяти")}</small></span></button><button data-a="access">${ic("lock")}<span><b>${tr("Кто что видит")}</b><small>${tr("права каждого ИИ")}</small></span></button><button data-a="out">${ic("eye")}<span><b>${tr("Что ушло наружу")}</b><small>${tr("отчёт за неделю")}</small></span></button></div>
        <div class="mtnav"><button class="btn g" data-p>${tr("Назад")}</button><button class="btn" data-x>${tr("Готово")}</button></div></div>`;
    } else {
      const sl = MEMTOUR[k];
      main = `<div class="mtmain"><div class="mtstep">${tr("Глава")} ${k + 1} ${tr("из")} ${N}</div><h2>${tr(sl.t)}</h2>
        <div class="mtscene"><div class="mtbox">${sl.scene}</div></div>
        <div class="mtbody"><p class="mtd">${tr(sl.d)}</p>${exHtml(sl.ex)}</div>
        <div class="mtnav"><div class="mtprog"><i style="width:${((k + 1) / N) * 100}%"></i></div>${sl.try ? `<button class="btn g sm mttry" data-a="${sl.try[0]}">${ic("eye")}${tr(sl.try[1])}</button>` : ""}<span class="mtsp"></span>${k ? `<button class="btn g" data-p>${tr("Назад")}</button>` : ""}<button class="btn" data-n>${tr("Дальше")} →</button></div></div>`;
    }
    pop.innerHTML = `<div class="card mtc mtg"><button class="lmx" data-x>×</button>${side()}${main}</div>`;
    $$("[data-a]", pop).forEach(
      (b) =>
        (b.onclick = () => {
          close();
          (MT_TRY[b.dataset.a] || (() => {}))();
        }),
    );
    $$("[data-x]", pop).forEach((b) => (b.onclick = close));
    $$("[data-p]", pop).forEach((b) => (b.onclick = () => go(-1)));
    $$("[data-n]", pop).forEach((b) => (b.onclick = () => go(1)));
    $$("[data-i]", pop).forEach(
      (b) =>
        (b.onclick = () => {
          k = +b.dataset.i;
          draw();
        }),
    );
    const cur = $(".mtch button.on", pop);
    if (cur) cur.scrollIntoView({ block: "nearest" });
  };
  draw();
}
