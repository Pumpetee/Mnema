// ---------------------------------------------------------------- markdown
function inline(s) {
  return esc(s)
    .replace(/`([^`]+)`/g, "<code>$1</code>")
    .replace(/\*\*(.+?)\*\*/g, "<b>$1</b>")
    .replace(/(^|[^*])\*([^*\n]+)\*/g, "$1<i>$2</i>")
    .replace(/\[([^\]]+)\]\((https?:[^)\s]+)\)/g, '<a href="$2" target="_blank">$1</a>')
    .replace(/(^|[\s(])(https?:\/\/[^\s<)]+)/g, '$1<a href="$2" target="_blank">$2</a>');
}
// a list item that starts with a short label ("Бульон. Мясо залей…", "свёкла — 2 средние") gets the label in bold
function leadIn(t) {
  if (/\*\*/.test(t)) return inline(t);
  const m = t.match(/^([^.:—!?*`\[]{2,40}?)(\.|:|\s—)\s+(\S[\s\S]*)$/);
  if (m && m[1].trim().split(/\s+/).length <= 4 && m[3].length > m[1].length / 2)
    return `<b class="ld">${esc(m[1])}${m[2] === "." || m[2] === ":" ? esc(m[2]) : ""}</b>${m[2].trim() === "—" ? " — " : " "}${inline(m[3])}`;
  return inline(t);
}
function md(src, live) {
  src = String(src || "").replace(/^---[\s\S]*?\n---\n/, "");
  const out = [];
  let list = null,
    table = null,
    code = null;
  const flush = () => {
    if (list) {
      out.push(`</${list}>`);
      list = null;
    }
    if (table) {
      out.push(
        "<table>" +
          table
            .map(
              (r, i) =>
                "<tr>" + r.map((c) => (i ? `<td>${inline(c)}</td>` : `<th>${inline(c)}</th>`)).join("") + "</tr>",
            )
            .join("") +
          "</table>",
      );
      table = null;
    }
  };
  for (const l of src.split("\n")) {
    if (code !== null) {
      if (/^```/.test(l)) {
        out.push(code.lang === "ask" ? askBlock(code.body, live) : `<pre><code>${esc(code.body)}</code></pre>`);
        code = null;
      } else code.body += (code.body ? "\n" : "") + l;
      continue;
    }
    const f = l.match(/^```(\w*)/);
    if (f) {
      flush();
      code = { lang: f[1], body: "" };
      continue;
    }
    if (/^\|.*\|\s*$/.test(l.trim())) {
      if (/^\|[-:\s|]+\|$/.test(l.trim())) continue;
      if (list) flush();
      (table = table || []).push(
        l
          .trim()
          .slice(1, -1)
          .split("|")
          .map((c) => c.trim()),
      );
      continue;
    }
    const ul = l.match(/^\s*[-*•] (.*)/),
      ol = l.match(/^\s*\d+[.)] (.*)/);
    if (ul || ol) {
      if (table) flush();
      const t = ul ? "ul" : "ol";
      if (list !== t) {
        if (list) out.push(`</${list}>`);
        out.push(`<${t}>`);
        list = t;
      }
      out.push("<li>" + leadIn((ul || ol)[1]) + "</li>");
      continue;
    }
    flush();
    const h = l.match(/^(#{1,4})\s+(.*)/);
    if (h) {
      out.push(h[1].length <= 2 ? `<h2>${inline(h[2])}</h2>` : `<h3>${inline(h[2])}</h3>`);
      continue;
    }
    if (/^[^.!?]{2,60}:\s*$/.test(l.trim()) && !/\*\*/.test(l)) {
      out.push('<p class="lead">' + inline(l.trim()) + "</p>");
      continue;
    }
    if (l.startsWith("> ")) {
      out.push('<p style="color:var(--ink2)">' + inline(l.slice(2)) + "</p>");
      continue;
    }
    if (l.trim()) out.push("<p>" + inline(l) + "</p>");
  }
  if (code !== null && code.lang !== "ask") out.push(`<pre><code>${esc(code.body)}</code></pre>`);
  flush();
  return out.join("");
}
// A question from the model: ```ask {"question", "why"?, "options": ["…"] or [{"label", "hint"}]}
function askBlock(body, live) {
  let q;
  try {
    q = JSON.parse(body);
  } catch (e) {
    return "";
  }
  const opts = (q.options || [])
    .slice(0, 6)
    .map((o) =>
      typeof o === "string" ? { label: o, hint: "" } : { label: String(o.label || ""), hint: String(o.hint || "") },
    )
    .filter((o) => o.label);
  return `<div class="ask ${live ? "live" : "done"}">
    <div class="askh"><span class="aski">${ic("hint")}</span><span class="askl">${tr("Нужно уточнить")}</span>
      <button class="askset" data-askset title="${tr("Как задавать вопросы")}">${ic("gear")}</button></div>
    <div class="askq">${esc(q.question)}</div>${q.why ? `<div class="askw">${esc(q.why)}</div>` : ""}
    <div class="askopts">${opts
      .map(
        (o, k) =>
          `<button class="askopt" data-ans="${esc(o.label)}"><span class="askn">${k + 1}</span><span class="askt"><b>${esc(o.label)}</b>${o.hint ? `<small>${esc(o.hint)}</small>` : ""}</span>${ic("check")}</button>`,
      )
      .join("")}</div>
    <form class="askown"><input placeholder="${tr("Или ответь своими словами…")}" aria-label="${tr("Свой ответ")}"><button title="${tr("Ответить")}"><svg class="i" viewBox="0 0 24 24" style="fill:currentColor;stroke:none"><path d="M3 20l18-8L3 4v6l12 2-12 2z"/></svg></button></form>
    <div class="askdone">${ic("check")}<span></span></div></div>`;
}
