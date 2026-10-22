const $ = (s) => document.querySelector(s);
chrome.storage.local.get({ port: 7461, token: "" }, (s) => {
  $("#token").value = s.token;
  $("#port").value = s.port;
});
$("#save").onclick = async () => {
  await chrome.storage.local.set({ token: $("#token").value.trim(), port: Number($("#port").value) || 7461 });
  chrome.runtime.sendMessage({ type: "ping" }, (r) => {
    $("#st").textContent = r && r.ok ? "✓ Связь с Mnema есть" : "✗ " + ((r && r.error) || "нет ответа");
    $("#st").style.color = r && r.ok ? "#1f6b3e" : "#c2413d";
  });
};
