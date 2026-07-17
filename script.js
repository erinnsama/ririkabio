/* RIRIKA 自我介紹站 — 讀 data/profile.json 動態渲染 */

const esc = (s) =>
  String(s == null ? "" : s)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");

async function load() {
  const app = document.getElementById("app");
  try {
    const res = await fetch("data/profile.json?t=" + Date.now());
    if (!res.ok) throw new Error("HTTP " + res.status);
    const data = await res.json();
    render(data);
  } catch (e) {
    app.innerHTML =
      '<div class="loading">載入失敗：' + esc(e.message) + "</div>";
  }
}

function render(d) {
  const app = document.getElementById("app");
  const parts = [];

  parts.push(header(d.profile));
  parts.push(about(d.about));
  parts.push(interests(d.interests));
  parts.push(links(d.links));
  (d.fandoms || []).forEach((f) => parts.push(fandom(f)));
  parts.push(hobbies(d.hobbies));
  parts.push(concerts(d.concerts));
  parts.push(support(d.support));

  app.innerHTML = parts.filter(Boolean).join("");
  renderFooter(d.footer);
}

/* ── 區塊 ── */

function header(p) {
  if (!p) return "";
  const tags = (p.tags || [])
    .map((t) => `<span class="tag">${esc(t)}</span>`)
    .join("");
  const initials = esc((p.name || "R").slice(0, 1));
  const avatar = p.avatar
    ? `<img src="${esc(p.avatar)}" alt="${esc(p.name)}" onerror="this.replaceWith(Object.assign(document.createElement('span'),{className:'avatar-fallback',textContent:'${initials}'}))" />`
    : `<span class="avatar-fallback">${initials}</span>`;
  return `
  <section class="hero">
    <div class="avatar">${avatar}</div>
    <h1 class="name">${esc(p.name)}</h1>
    ${p.nameZh ? `<p class="name-zh">${esc(p.nameZh)}</p>` : ""}
    <div class="tags">${tags}</div>
  </section>`;
}

function about(a) {
  if (!a) return "";
  const lines = (a.lines || [])
    .map((l) => `<p>${esc(l)}</p>`)
    .join("");
  return card(a.title || "關於我", `<div class="about-text">${lines}</div>`);
}

function interests(i) {
  if (!i) return "";
  const chips = (i.items || [])
    .map((x) => `<span class="chip">${esc(x)}</span>`)
    .join("");
  return card(i.title || "日常", `<div class="chips">${chips}</div>`);
}

function links(list) {
  if (!list || !list.length) return "";
  const rows = list
    .map(
      (l) => `
    <a class="link-row" href="${esc(l.url)}" target="_blank" rel="noopener">
      <span class="link-icon">${platformIcon(l.platform)}</span>
      <span class="link-body">
        <span class="link-platform">${esc(l.platform)}</span>
        <span class="link-label">${esc(l.label)}</span>
        ${l.note ? `<span class="link-note">${esc(l.note)}</span>` : ""}
      </span>
      <span class="link-arrow">↗</span>
    </a>`
    )
    .join("");
  return card("社群連結", rows);
}

function fandom(f) {
  if (!f) return "";
  const accent = f.accent || "#4f7cff";
  const tl = (f.timeline || [])
    .map(
      (t) => `
    <li class="tl-item">
      <span class="tl-when">${esc(t.when)}</span>
      <span class="tl-what">${esc(t.what)}</span>
    </li>`
    )
    .join("");
  const notes = (f.notes || [])
    .map((n) => `<li>${esc(n)}</li>`)
    .join("");
  return `
  <section class="card fandom" style="--accent:${esc(accent)}">
    <div class="fandom-head">
      <span class="level-badge">${esc(f.level)}</span>
      <h2 class="fandom-group">${esc(f.group)}</h2>
      ${f.bias ? `<span class="bias">${esc(f.bias)}</span>` : ""}
    </div>
    ${tl ? `<ul class="timeline">${tl}</ul>` : ""}
    ${notes ? `<ul class="notes">${notes}</ul>` : ""}
  </section>`;
}

function hobbies(h) {
  if (!h || !h.items) return "";
  const items = h.items
    .map(
      (x) => `
    <li class="hobby">
      <div class="hobby-head">
        <span class="hobby-name">${esc(x.name)}</span>
        ${x.when ? `<span class="hobby-when">${esc(x.when)}</span>` : ""}
      </div>
      ${
        x.bias
          ? `<div class="hobby-bias"><span class="bias-label">主推</span>${splitChars(
              x.bias
            )
              .map((c) => `<span class="char-badge">${esc(c)}</span>`)
              .join("")}</div>`
          : ""
      }
      ${x.note ? `<p class="hobby-note">${esc(x.note)}</p>` : ""}
    </li>`
    )
    .join("");
  const foot = h.footnote
    ? `<p class="hobby-footnote">${esc(h.footnote)}</p>`
    : "";
  return card(h.title || "興趣坑", `<ul class="hobby-list">${items}</ul>${foot}`);
}

function concerts(c) {
  if (!c || !c.items) return "";
  const items = c.items
    .map(
      (x) => `
    <li class="concert">
      <span class="concert-date">${esc(x.date)}</span>
      <span class="concert-main">
        <span class="concert-title">${esc(x.title)}</span>
        <span class="concert-meta">
          ${x.group ? `<span class="concert-group">${esc(x.group)}</span>` : ""}
          ${x.city ? `<span class="concert-city">${esc(x.city)}</span>` : ""}
        </span>
      </span>
    </li>`
    )
    .join("");
  return card(c.title || "演唱會", `<ul class="concert-list">${items}</ul>`);
}

function support(s) {
  if (!s || !s.items) return "";
  const items = s.items
    .map((x) => {
      if (x.type === "link") {
        return `
      <a class="support-item support-link" href="${esc(x.url)}" target="_blank" rel="noopener">
        <span class="support-date">${esc(x.date)}</span>
        <span class="support-title">${esc(x.title)} ↗</span>
        ${x.note ? `<span class="support-note">${esc(x.note)}</span>` : ""}
      </a>`;
      }
      const img = x.image
        ? `<img class="support-img" src="${esc(x.image)}" alt="${esc(x.title)}" loading="lazy" />`
        : `<div class="support-img placeholder">1080 × 1080</div>`;
      return `
      <div class="support-item">
        ${img}
        <span class="support-date">${esc(x.date)}</span>
        <span class="support-title">${esc(x.title)}</span>
        ${x.note ? `<span class="support-note">${esc(x.note)}</span>` : ""}
      </div>`;
    })
    .join("");
  return card(s.title || "應援相關", `<div class="support-grid">${items}</div>`);
}

function renderFooter(f) {
  if (!f) return;
  const el = document.getElementById("footer");
  el.innerHTML = `
    <a href="${esc(f.url || "#")}" target="_blank" rel="noopener">${esc(
    f.handle || ""
  )}</a>`;
}

/* ── helpers ── */

function card(title, inner) {
  return `
  <section class="card">
    <h2 class="card-title">${esc(title)}</h2>
    ${inner}
  </section>`;
}

function splitChars(s) {
  return String(s == null ? "" : s)
    .split(/[、，,／\/]+/)
    .map((x) => x.trim())
    .filter(Boolean);
}

function platformIcon(p) {
  const key = String(p || "").toLowerCase();
  if (key.includes("thread")) return "@";
  if (key.includes("insta")) return "◎";
  return "🔗";
}

load();
