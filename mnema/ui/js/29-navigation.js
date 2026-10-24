// ---------------------------------------------------------------- navigation: the rail, views by #hash, the waiting count
const VIEWS = { chat: viewChat, memory: viewMemory, settings: viewSettings };
function go(v, arg) {
  arg = arg ? decodeURIComponent(arg) : arg;
  if (!(v in VIEWS)) v = "chat";
  document.body.classList.remove("drawer-open");
  $$(".rail button").forEach((b) => b.classList.toggle("on", b.dataset.v === v));
  if (v !== "chat") {
    clearInterval(CHAT.feedTimer);
    CHAT.feedTimer = null;
  }
  (Object.hasOwn(VIEWS, v) ? VIEWS[v] : VIEWS.chat)(arg) // only the known views: «#constructor» opens the chat
    .then(() => drawGear()) // the orange «без обучения» dot belongs to the chat only
    .catch((e) => toast(e.message));
  badge();
  if (location.hash.slice(1).split("/")[0] !== v) history.replaceState(null, "", "#" + v);
}
// «Чаты» opens the conversation the owner was in last; «Новый разговор» and Ctrl+N start a new one
$$(".rail button").forEach(
  (b) => (b.onclick = () => go(b.dataset.v, b.dataset.v === "chat" ? LS.get("lastchat", "") : undefined)),
);
(function logoLife() {
  const go = () => {
    const l = $(".logo");
    if (l && !document.hidden) {
      const k = Math.random() < 0.35 ? "hop" : "spin";
      l.classList.remove("spin", "hop");
      void l.offsetWidth;
      l.classList.add(k);
      setTimeout(() => l.classList.remove(k), 1400);
    }
    setTimeout(go, 9000 + Math.random() * 14000);
  };
  setTimeout(go, 2500);
})();
window.addEventListener("hashchange", () => {
  const [v, ...a] = location.hash.slice(1).split("/");
  go(v, a.join("/"));
});
// there is no waiting queue any more: what needs the owner is asked in the conversation itself
async function badge() {
  STATUS.wait = 0;
  return 0;
}
