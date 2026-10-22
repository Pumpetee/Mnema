// A small "Память" panel inside ChatGPT and Gemini.
(() => {
  if (window.__mnema) return;
  window.__mnema = true;
  const CLIENT = location.hostname.includes("gemini") ? "gemini" : "chatgpt";

  const send = (msg) =>
    new Promise((res) =>
      chrome.runtime.sendMessage(msg, (r) => res(r || { ok: false, error: "расширение не ответило" })),
    );

  const box = document.createElement("div");
  box.id = "mnema-box";
  box.innerHTML = `
    <div class="mn-head"><span class="mn-dot"></span><b>Память</b><span class="mn-st">проверяю связь…</span></div>
    <div class="mn-acts">
      <button class="mn-ins" title="Добавить в сообщение то, что тебе разрешено знать обо мне">Подставить память</button>
      <button class="mn-save" title="Выдели текст в чате и нажми — он попадёт во входящие">Сохранить выделенное</button>
    </div>
    <div class="mn-toast"></div>`;
  document.documentElement.appendChild(box);
  const $ = (s) => box.querySelector(s);

  function toast(t, bad) {
    const e = $(".mn-toast");
    e.textContent = t;
    e.className = "mn-toast on" + (bad ? " bad" : "");
    clearTimeout(e._t);
    e._t = setTimeout(() => (e.className = "mn-toast"), 3500);
  }

  function composer() {
    return (
      document.querySelector("#prompt-textarea") ||
      document.querySelector("rich-textarea .ql-editor") ||
      document.querySelector('div[contenteditable="true"]') ||
      document.querySelector("textarea")
    );
  }

  function insert(text) {
    const el = composer();
    if (!el) return false;
    el.focus();
    if (el.tagName === "TEXTAREA") {
      el.value = text + (el.value ? "\n\n" + el.value : "");
      el.dispatchEvent(new Event("input", { bubbles: true }));
      return true;
    }
    // contenteditable (ChatGPT ProseMirror, Gemini Quill): put caret at start and type, so the editor sees it
    const sel = window.getSelection();
    const range = document.createRange();
    range.selectNodeContents(el);
    range.collapse(true);
    sel.removeAllRanges();
    sel.addRange(range);
    const ok = document.execCommand("insertText", false, text + "\n");
    if (!ok) {
      el.textContent = text + "\n\n" + el.textContent;
      el.dispatchEvent(new InputEvent("input", { bubbles: true }));
    }
    return true;
  }

  let learning = false;
  async function status() {
    const r = await send({ type: "ping" });
    learning = !!(r.ok && r.learn);
    $(".mn-dot").className = "mn-dot " + (r.ok ? "on" : "off");
    $(".mn-st").textContent = r.ok ? (learning ? "подключена · учусь" : "подключена") : r.error;
  }

  // Learning: when it's switched on in the Mnema app, the owner's sent messages are passed to Mnema.
  // Only what the owner writes, plus the AI's last answer as context for corrections.
  const SEND_BTN =
    'button[data-testid="send-button"], button.send-button, button[aria-label*="Send"], button[aria-label*="Отправ"]';
  const LAST_AI = '[data-message-author-role="assistant"], model-response';
  let lastSent = "";
  function draft() {
    const el = composer();
    return el ? (el.value !== undefined && el.tagName === "TEXTAREA" ? el.value : el.innerText || "").trim() : "";
  }
  let inserted = new Set(); // lines of memory we put in ourselves — not the owner's words
  function observe(text) {
    text = text
      .split("\n")
      .filter((l) => !inserted.has(l.trim()))
      .join("\n")
      .trim();
    if (!learning || !text || text === lastSent) return;
    lastSent = text;
    const ai = [...document.querySelectorAll(LAST_AI)].pop();
    send({
      type: "observe",
      client: CLIENT,
      url: location.href,
      title: document.title,
      text,
      prev: ai ? ai.innerText.slice(-700) : "",
    });
  }
  document.addEventListener(
    "keydown",
    (e) => {
      const el = composer();
      if (e.key === "Enter" && !e.shiftKey && !e.isComposing && el && (el === e.target || el.contains(e.target)))
        observe(draft());
    },
    true,
  );
  document.addEventListener(
    "click",
    (e) => {
      if (e.target.closest && e.target.closest(SEND_BTN)) observe(draft());
    },
    true,
  );
  setInterval(status, 60000);

  $(".mn-ins").onclick = async () => {
    const r = await send({ type: "context", client: CLIENT });
    if (!r.ok) return toast(r.error, true);
    if (!r.text) return toast("Доступ выключен в приложении Mnema", true);
    // editors turn every line break into a paragraph — drop empty lines so the block stays compact
    const body = r.text
      .split("\n")
      .filter((l) => l.trim())
      .join("\n");
    const text = "Контекст обо мне (из моей памяти Mnema, учитывай в ответе):\n" + body;
    inserted = new Set(
      text
        .split("\n")
        .map((l) => l.trim())
        .filter(Boolean),
    );
    insert(text) ? toast("Память подставлена в сообщение") : toast("Не нашёл поле ввода", true);
  };

  $(".mn-save").onclick = async () => {
    const picked = String(window.getSelection() || "").trim();
    const fact = window.prompt("Сохранить в память (можно поправить):", picked);
    if (!fact || !fact.trim()) return;
    const r = await send({ type: "remember", client: CLIENT, fact: fact.trim() });
    r.ok ? toast("Сохранено во входящие · можно откатить в журнале") : toast(r.error, true);
  };

  status();
})();
