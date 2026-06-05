const API = "";
let token = localStorage.getItem("fixnet_admin_token") || "";

const $ = (s) => document.querySelector(s);
const $$ = (s) => document.querySelectorAll(s);

async function api(path, opts = {}) {
  const headers = { "Content-Type": "application/json", ...(opts.headers || {}) };
  if (token) headers.Authorization = `Bearer ${token}`;
  const res = await fetch(`${API}${path}`, { ...opts, headers });
  if (res.status === 401) { logout(); throw new Error("Unauthorized"); }
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || res.statusText);
  }
  return res.json();
}

function showApp() {
  $("#loginScreen").classList.add("hidden");
  $("#app").classList.remove("hidden");
  loadAnalytics();
}

function logout() {
  token = "";
  localStorage.removeItem("fixnet_admin_token");
  $("#app").classList.add("hidden");
  $("#loginScreen").classList.remove("hidden");
}

$("#loginForm")?.addEventListener("submit", async (e) => {
  e.preventDefault();
  try {
    const data = await api("/api/admin/login", {
      method: "POST",
      body: JSON.stringify({ password: $("#password").value }),
    });
    token = data.token;
    localStorage.setItem("fixnet_admin_token", token);
    showApp();
  } catch (err) {
    $("#loginError").textContent = err.message;
    $("#loginError").classList.remove("hidden");
  }
});

$("#logoutBtn")?.addEventListener("click", logout);

$$(".nav-btn").forEach((btn) => {
  btn.addEventListener("click", () => {
    $$(".nav-btn").forEach((b) => b.classList.remove("active"));
    btn.classList.add("active");
    $$(".tab").forEach((t) => t.classList.remove("active"));
    $(`#tab-${btn.dataset.tab}`).classList.add("active");
    if (btn.dataset.tab === "analytics") loadAnalytics();
    if (btn.dataset.tab === "users") loadUsersKeys();
    if (btn.dataset.tab === "broadcast") { loadBroadcastHistory(); }
    if (btn.dataset.tab === "support") loadTickets("open");
    if (btn.dataset.tab === "channel") loadChannelLogs();
  });
});

let usersKeysCache = [];

async function loadUsersKeys() {
  usersKeysCache = await api("/api/admin/users-keys");
  renderUsersTable(usersKeysCache);
}

function renderUsersTable(rows) {
  const q = ($("#userSearch")?.value || "").toLowerCase().trim();
  const filtered = q
    ? rows.filter((r) =>
        [r.display_name, r.username, r.first_name, r.key, String(r.telegram_id)]
          .filter(Boolean)
          .some((v) => String(v).toLowerCase().includes(q))
      )
    : rows;

  if (!filtered.length) {
    $("#usersTable").innerHTML = '<p class="hint">Пользователей не найдено</p>';
    return;
  }

  $("#usersTable").innerHTML = `
    <table>
      <thead>
        <tr>
          <th>Пользователь</th>
          <th>Telegram ID</th>
          <th>Ключ активации</th>
          <th>Статус</th>
          <th>Истекает</th>
        </tr>
      </thead>
      <tbody>
        ${filtered.map((u) => `
          <tr>
            <td class="name-cell">${escapeHtml(u.display_name)}${u.username ? ` <span class="hint">@${escapeHtml(u.username)}</span>` : ""}</td>
            <td>${u.telegram_id}</td>
            <td class="key-cell">${u.key ? escapeHtml(u.key) : "—"}</td>
            <td><span class="badge ${u.is_active ? "active" : "inactive"}">${u.is_active ? "Активен" : "Неактивен"}</span></td>
            <td>${u.expires_at ? new Date(u.expires_at).toLocaleDateString("ru") : "—"}</td>
          </tr>
        `).join("")}
      </tbody>
    </table>
  `;
}

$("#userSearch")?.addEventListener("input", () => renderUsersTable(usersKeysCache));

async function loadAnalytics() {
  const d = await api("/api/admin/analytics");
  $("#statsGrid").innerHTML = `
    <div class="stat-card"><div class="value">${d.users.total}</div><div class="label">Пользователей</div></div>
    <div class="stat-card"><div class="value">${d.users.new_7d}</div><div class="label">Новых за 7 дней</div></div>
    <div class="stat-card"><div class="value">${d.keys.active}</div><div class="label">Активных ключей</div></div>
    <div class="stat-card"><div class="value">${d.keys.total}</div><div class="label">Всего ключей</div></div>
    <div class="stat-card"><div class="value">${d.support.open}</div><div class="label">Открытых тикетов</div></div>
    <div class="stat-card"><div class="value">${d.broadcasts}</div><div class="label">Рассылок</div></div>
    <div class="stat-card"><div class="value">${d.channel_forwards}</div><div class="label">Пересылок с канала</div></div>
  `;
}

$$(".emoji-btn").forEach((btn) => {
  btn.addEventListener("click", () => {
    const ta = $("#broadcastText");
    ta.value += btn.dataset.e;
    ta.focus();
  });
});

$("#sendBroadcast")?.addEventListener("click", async () => {
  const text = $("#broadcastText").value.trim();
  if (!text) return;
  let buttons = [];
  try {
    const raw = $("#broadcastButtons").value.trim();
    if (raw) buttons = JSON.parse(raw);
  } catch { alert("Неверный JSON кнопок"); return; }

  $("#sendBroadcast").disabled = true;
  try {
    const r = await api("/api/admin/broadcast", {
      method: "POST",
      body: JSON.stringify({ text, parse_mode: "HTML", buttons }),
    });
    $("#broadcastResult").textContent = `✅ Отправлено: ${r.sent}, ошибок: ${r.failed}`;
    loadBroadcastHistory();
  } catch (err) {
    $("#broadcastResult").textContent = `❌ ${err.message}`;
  }
  $("#sendBroadcast").disabled = false;
});

async function loadBroadcastHistory() {
  const items = await api("/api/admin/broadcasts");
  $("#broadcastHistory").innerHTML = items.map((b) =>
    `<div class="item"><b>#${b.id}</b> — ${b.sent_count} отправлено · ${new Date(b.created_at).toLocaleString("ru")}<br><span class="hint">${escapeHtml(b.text)}</span></div>`
  ).join("") || '<p class="hint">Пока нет рассылок</p>';
}

let supportStatus = "open";
$$(".tab-btn").forEach((btn) => {
  btn.addEventListener("click", () => {
    $$(".tab-btn").forEach((b) => b.classList.remove("active"));
    btn.classList.add("active");
    supportStatus = btn.dataset.status;
    loadTickets(supportStatus);
  });
});

async function loadTickets(status) {
  const tickets = await api(`/api/admin/support?status=${status}`);
  $("#ticketsList").innerHTML = tickets.map((t) => `
    <div class="ticket" data-id="${t.id}">
      <div class="meta">#${t.id} · @${t.username || t.telegram_id} · ${new Date(t.created_at).toLocaleString("ru")}</div>
      <div class="msg">${escapeHtml(t.message)}</div>
      ${t.admin_reply ? `<div class="hint">Ответ: ${escapeHtml(t.admin_reply)}</div>` : ""}
      ${status === "open" ? `
        <textarea placeholder="Ваш ответ..." id="reply-${t.id}"></textarea>
        <div class="ticket-actions">
          <button class="btn-reply" onclick="replyTicket(${t.id})">Ответить</button>
          <button class="btn-close" onclick="closeTicket(${t.id})">Закрыть</button>
        </div>` : ""}
    </div>
  `).join("") || '<p class="hint">Нет тикетов</p>';
}

window.replyTicket = async (id) => {
  const text = $(`#reply-${id}`).value.trim();
  if (!text) return;
  await api(`/api/admin/support/${id}/reply`, { method: "POST", body: JSON.stringify({ reply: text }) });
  loadTickets(supportStatus);
};

window.closeTicket = async (id) => {
  await api(`/api/admin/support/${id}/close`, { method: "POST" });
  loadTickets(supportStatus);
};

async function loadChannelLogs() {
  const logs = await api("/api/admin/channel/logs");
  $("#channelLogs").innerHTML = logs.map((l) =>
    `<div class="item">Пост #${l.channel_message_id} → ${l.forwarded_count} пользователей · ${new Date(l.created_at).toLocaleString("ru")}</div>`
  ).join("") || '<p class="hint">Пересылок пока не было</p>';
}

function escapeHtml(s) {
  return s.replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;");
}

if (token) {
  api("/api/admin/analytics").then(showApp).catch(logout);
}
