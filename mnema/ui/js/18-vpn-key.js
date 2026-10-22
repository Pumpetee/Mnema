// ---------------------------------------------------------------- a VPN key: Mnema connects through it itself (vpnkey.py, Xray inside)
const VK_SVCS = ["Hiddify", "Happ", "v2rayN", "V2Box", "NekoBox", "Streisand", "Outline", "Другой сервис"];
async function bindVpnKey(prof) {
  const box = $("#netcard");
  if (!box) return;
  const svc = $("#vksvc", box),
    hint = $("#vkhint", box),
    stat = $("#vkstat", box),
    mb = $("#vkbox", box),
    msg = $("#vkmsg", box);
  const showHint = () => {
    hint.textContent =
      tr("Скопируй ключ в") +
      " " +
      (svc.value === "Другой сервис" ? tr("своём VPN-сервисе") : svc.value) +
      tr(
        ": ссылку, которая начинается с vless://, vmess://, trojan://, ss://, или ссылку подписки — и нажми «Импортировать ключ».",
      );
  };
  showHint();
  svc.onchange = showHint;
  const draw = (d) => {
    stat.innerHTML =
      d.on && d.error
        ? `<div class="vkon bad"><i></i><div><b>${tr("VPN по ключу не работает")}: <span data-noi18n>${esc(d.name || "")}</span></b><small>${esc(d.error)}</small></div><button class="btn g sm" id="vkoff">${tr("Отключить")}</button></div>`
        : d.on
          ? `<div class="vkon"><i></i><div><b>${tr("Подключено по ключу")}: <span data-noi18n>${esc(d.name || "")}</span></b><small>${esc(d.service || "")}${d.ms ? ` · ${d.ms} ${tr("мс до Anthropic")}` : ""}</small></div><button class="btn g sm" id="vkoff">${tr("Отключить")}</button></div>`
          : d.saved
            ? `<div class="vkon bad"><i></i><div><b>${tr("Ключ сохранён, но не подключён")}</b><small>${tr("нажми «Импортировать» или введи ключ ещё раз")}</small></div><button class="btn g sm" id="vkoff">${tr("Забыть ключ")}</button></div>`
            : "";
    const off = $("#vkoff", stat);
    if (off)
      off.onclick = async () => {
        draw(await post("/api/vpn", { action: "off" }));
        toast(tr("VPN по ключу отключён"));
        viewSettings(SETCUR);
      };
  };
  const connect = async (key) => {
    key = (key || "").trim();
    if (!key) {
      mb.hidden = false;
      $("#vkkey", box).focus();
      return;
    }
    mb.hidden = false;
    $("#vkkey", box).value = key;
    msg.textContent = tr("подключаюсь и проверяю связь с ИИ…");
    $("#vkgo", box).disabled = true;
    try {
      const d = await post("/api/vpn", { action: "connect", key, service: svc.value });
      msg.textContent = "";
      mb.hidden = true;
      draw(d);
      toast(tr("Подключено") + ": " + (d.name || ""));
      setTimeout(() => viewSettings(SETCUR), 900);
    } catch (e) {
      msg.textContent = e.message;
    } finally {
      $("#vkgo", box).disabled = false;
    }
  };
  $("#vkimp", box).onclick = async () => {
    let t = "";
    try {
      t = await navigator.clipboard.readText();
    } catch (e) {}
    if (!/^(vless|vmess|trojan|ss):\/\/|^https?:\/\//i.test((t || "").trim())) {
      mb.hidden = false;
      $("#vkkey", box).focus();
      msg.textContent = tr("В буфере нет ключа. Скопируй его в") + " " + svc.value + " " + tr("или вставь сюда сам.");
      return;
    }
    connect(t);
  };
  $("#vkman", box).onclick = () => {
    mb.hidden = !mb.hidden;
    if (!mb.hidden) $("#vkkey", box).focus();
  };
  $("#vkgo", box).onclick = () => connect($("#vkkey", box).value);
  try {
    draw(await api("/api/vpn"));
  } catch (e) {}
}
