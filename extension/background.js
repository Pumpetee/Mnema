// Talks to the local Mnema app. Runs in the extension's service worker, so pages never see the token.
async function settings() {
  const s = await chrome.storage.local.get({ port: 7461, token: "" });
  return { base: `http://127.0.0.1:${s.port}`, token: s.token };
}

async function call(path, body) {
  const { base, token } = await settings();
  if (!token) throw new Error("Нет токена: открой настройки расширения и вставь токен из приложения Mnema");
  const r = await fetch(base + path, {
    method: body ? "POST" : "GET",
    headers: { "X-Mnema-Token": token, "Content-Type": "application/json" },
    body: body ? JSON.stringify(body) : undefined,
  });
  const d = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error(d.error || `ошибка ${r.status}`);
  return d;
}

chrome.runtime.onMessage.addListener((msg, _sender, reply) => {
  (async () => {
    try {
      if (msg.type === "context")
        return reply({ ok: true, ...(await call(`/api/context?client=${encodeURIComponent(msg.client)}`)) });
      if (msg.type === "remember")
        return reply({
          ok: true,
          ...(await call("/api/remember", { fact: msg.fact, where: "inbox", client: msg.client })),
        });
      if (msg.type === "observe")
        return reply({
          ok: true,
          ...(await call("/api/observe", {
            client: msg.client,
            url: msg.url,
            title: msg.title,
            text: msg.text,
            prev: msg.prev,
          })),
        });
      if (msg.type === "ping") return reply({ ok: true, ...(await call("/api/ping")) });
      reply({ ok: false, error: "неизвестная команда" });
    } catch (e) {
      reply({
        ok: false,
        error: String(e.message || e).includes("Failed to fetch")
          ? "Нет связи с Mnema: запусти приложение на компьютере"
          : String(e.message || e),
      });
    }
  })();
  return true; // async reply
});
