from __future__ import annotations

# A single self-contained page (no external CSS/JS/fonts - this is a private
# single-household appliance, not a hosted SaaS product) served at GET /setup/accounts.
# Off-script per product owner: AGENTS.md's "UI surfaces use registered cards and
# declarative layouts" / kinward-dashboard.yaml's "no Kinward-owned frontend code is
# required" pattern is deliberately not followed here - connecting a Google/Microsoft
# account requires a real browser redirect to the provider's consent screen and back,
# which no Home Assistant card or service call can do.
ACCOUNTS_SETUP_HTML = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Kinward - Connect Accounts</title>
<style>
  :root {
    color-scheme: light dark;
    --bg: #f4f5f9;
    --card-bg: #ffffff;
    --text: #1c1e2b;
    --muted: #6b6f85;
    --border: #e3e4ee;
    --accent-a: #6a5cff;
    --accent-b: #3ecfd9;
    --ok: #1f9d55;
    --ok-bg: #e6f7ec;
    --warn: #b4740e;
    --warn-bg: #fbf0dd;
    --danger: #c93b3b;
    --danger-bg: #fbe9e9;
    --shadow: 0 1px 2px rgba(20, 20, 40, 0.04), 0 8px 24px rgba(20, 20, 40, 0.06);
  }
  @media (prefers-color-scheme: dark) {
    :root {
      --bg: #14151f;
      --card-bg: #1c1e2b;
      --text: #eef0fb;
      --muted: #9598b3;
      --border: #2c2e40;
      --ok-bg: #113420;
      --warn-bg: #3a2c0d;
      --danger-bg: #3a1414;
      --shadow: 0 1px 2px rgba(0, 0, 0, 0.25), 0 8px 28px rgba(0, 0, 0, 0.35);
    }
  }
  * { box-sizing: border-box; }
  body {
    margin: 0;
    min-height: 100vh;
    background: var(--bg);
    color: var(--text);
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
  }
  header.hero {
    padding: 2.5rem 1.5rem 3.5rem;
    background: linear-gradient(135deg, var(--accent-a), var(--accent-b));
    color: #fff;
    text-align: center;
  }
  header.hero h1 { margin: 0 0 0.35rem; font-size: 1.6rem; font-weight: 700; }
  header.hero p { margin: 0; opacity: 0.92; font-size: 0.95rem; }
  main {
    max-width: 720px;
    margin: -2.25rem auto 3rem;
    padding: 0 1.25rem;
  }
  .card {
    background: var(--card-bg);
    border: 1px solid var(--border);
    border-radius: 16px;
    box-shadow: var(--shadow);
    padding: 1.5rem;
    margin-bottom: 1.25rem;
  }
  .card h2 { margin: 0 0 0.9rem; font-size: 1.05rem; }
  .muted { color: var(--muted); font-size: 0.88rem; }
  #gate input {
    width: 100%;
    padding: 0.65rem 0.8rem;
    border-radius: 10px;
    border: 1px solid var(--border);
    background: transparent;
    color: var(--text);
    font-size: 0.95rem;
    margin: 0.75rem 0;
  }
  button {
    font: inherit;
    cursor: pointer;
    border-radius: 10px;
    border: 1px solid var(--border);
    background: var(--card-bg);
    color: var(--text);
    padding: 0.55rem 0.9rem;
    transition: transform 0.06s ease, box-shadow 0.15s ease;
  }
  button:hover:not(:disabled) { box-shadow: var(--shadow); }
  button:active:not(:disabled) { transform: scale(0.98); }
  button:disabled { opacity: 0.45; cursor: not-allowed; }
  button.primary {
    background: linear-gradient(135deg, var(--accent-a), var(--accent-b));
    color: #fff;
    border: none;
    font-weight: 600;
  }
  button.danger { color: var(--danger); }
  .person-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 0.75rem;
    padding: 0.75rem 0;
    border-top: 1px solid var(--border);
  }
  .person-row:first-of-type { border-top: none; }
  .person-row .name { font-weight: 600; }
  .actions { display: flex; gap: 0.5rem; flex-wrap: wrap; }
  .account-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 0.75rem;
    padding: 0.85rem 0;
    border-top: 1px solid var(--border);
  }
  .account-row:first-of-type { border-top: none; }
  .account-meta .email { font-weight: 600; }
  .account-meta .sub { color: var(--muted); font-size: 0.82rem; margin-top: 0.15rem; }
  .pill {
    display: inline-block;
    font-size: 0.75rem;
    font-weight: 600;
    padding: 0.15rem 0.55rem;
    border-radius: 999px;
    margin-left: 0.5rem;
  }
  .pill.connected { color: var(--ok); background: var(--ok-bg); }
  .pill.reauth { color: var(--warn); background: var(--warn-bg); }
  .empty { color: var(--muted); font-size: 0.9rem; padding: 0.5rem 0; }
  #banner {
    max-width: 720px;
    margin: 1rem auto 0;
    padding: 0 1.25rem;
    display: none;
  }
  #banner .box {
    border-radius: 12px;
    padding: 0.75rem 1rem;
    font-size: 0.9rem;
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 0.75rem;
  }
  #banner.ok .box { background: var(--ok-bg); color: var(--ok); }
  #banner.err .box { background: var(--danger-bg); color: var(--danger); }
  #banner button { background: transparent; border: none; color: inherit; font-weight: 700; }
  .badge {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 1.6rem;
    height: 1.6rem;
    border-radius: 8px;
    font-size: 0.78rem;
    font-weight: 700;
    margin-right: 0.6rem;
    color: #fff;
  }
  .badge.google { background: #4285f4; }
  .badge.microsoft { background: #00849c; }
</style>
</head>
<body>

<header class="hero">
  <h1>Connect Accounts</h1>
  <p>Link a Google or Microsoft calendar so Kinward can watch it for you.</p>
</header>

<div id="banner"><div class="box"><span id="bannerText"></span><button onclick="dismissBanner()">&times;</button></div></div>

<main>
  <section id="gate" class="card">
    <h2>Setup token</h2>
    <p class="muted">Enter the deployment's accounts setup token (KINWARD_ACCOUNTS_SETUP_TOKEN) to manage account connections.</p>
    <input id="tokenInput" type="password" placeholder="Setup token" autocomplete="off">
    <button class="primary" onclick="saveToken()">Continue</button>
    <p id="gateError" class="muted" style="color: var(--danger); display:none;"></p>
  </section>

  <section id="app" style="display:none;">
    <div class="card" id="peopleCard">
      <h2>Connect a new account</h2>
      <div id="providerNotice" class="muted" style="display:none; margin-bottom: 0.75rem;"></div>
      <div id="peopleList"></div>
    </div>

    <div class="card" id="accountsCard">
      <h2>Connected accounts</h2>
      <div id="accountsList"></div>
    </div>

    <p class="muted" style="text-align:center;">
      <button onclick="signOut()">Use a different setup token</button>
    </p>
  </section>
</main>

<script>
const TOKEN_KEY = 'kinwardAccountsSetupToken';
let providers = { google: false, microsoft: false };

function qs(id) { return document.getElementById(id); }

function dismissBanner() {
  qs('banner').style.display = 'none';
  const url = new URL(window.location.href);
  url.search = '';
  window.history.replaceState({}, '', url.toString());
}

function showBanner(kind, text) {
  const banner = qs('banner');
  banner.className = kind;
  qs('bannerText').textContent = text;
  banner.style.display = 'block';
}

function readBannerFromQuery() {
  const params = new URLSearchParams(window.location.search);
  const status = params.get('status');
  if (!status) return;
  if (status === 'connected') {
    const provider = params.get('provider') || 'account';
    const email = params.get('email') || '';
    showBanner('ok', 'Connected ' + provider + (email ? (' (' + email + ')') : '') + '.');
  } else if (status === 'error') {
    showBanner('err', 'Connection failed: ' + (params.get('message') || 'unknown error'));
  }
}

function saveToken() {
  const value = qs('tokenInput').value.trim();
  if (!value) return;
  sessionStorage.setItem(TOKEN_KEY, value);
  qs('gateError').style.display = 'none';
  boot();
}

function signOut() {
  sessionStorage.removeItem(TOKEN_KEY);
  qs('app').style.display = 'none';
  qs('gate').style.display = 'block';
}

async function apiFetch(path, opts) {
  const token = sessionStorage.getItem(TOKEN_KEY);
  const headers = Object.assign({}, (opts && opts.headers) || {}, { 'X-Accounts-Setup-Token': token || '' });
  const response = await fetch(path, Object.assign({}, opts, { headers }));
  if (response.status === 401) {
    qs('gateError').textContent = 'That setup token was rejected.';
    qs('gateError').style.display = 'block';
    signOut();
    throw new Error('invalid token');
  }
  if (response.status === 503) {
    qs('gateError').textContent = 'Account connections are not configured on this deployment yet.';
    qs('gateError').style.display = 'block';
    throw new Error('not configured');
  }
  return response;
}

function relativeTime(iso) {
  if (!iso) return 'never synced';
  const then = new Date(iso).getTime();
  const diffMin = Math.round((Date.now() - then) / 60000);
  if (diffMin < 1) return 'synced just now';
  if (diffMin < 60) return 'synced ' + diffMin + 'm ago';
  const diffHr = Math.round(diffMin / 60);
  if (diffHr < 24) return 'synced ' + diffHr + 'h ago';
  return 'synced ' + Math.round(diffHr / 24) + 'd ago';
}

function renderProviderNotice() {
  const notice = qs('providerNotice');
  const missing = [];
  if (!providers.google) missing.push('Google');
  if (!providers.microsoft) missing.push('Microsoft');
  if (missing.length) {
    notice.style.display = 'block';
    notice.textContent = missing.join(' and ') + " client credentials aren't configured yet - those buttons stay disabled until they are.";
  } else {
    notice.style.display = 'none';
  }
}

async function startConnect(provider, personId, button) {
  button.disabled = true;
  try {
    const response = await apiFetch('/api/v1/setup/accounts/' + provider + '/connect', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ personId: personId }),
    });
    if (!response.ok) {
      const body = await response.json().catch(() => ({}));
      showBanner('err', (body.detail && body.detail.message) || 'Could not start the connection.');
      button.disabled = false;
      return;
    }
    const body = await response.json();
    window.location.href = body.authorizeUrl;
  } catch (err) {
    button.disabled = false;
  }
}

async function disconnectAccount(accountId, button) {
  if (!window.confirm('Disconnect this account? Kinward will stop reading its calendar.')) return;
  button.disabled = true;
  try {
    const response = await apiFetch('/api/v1/setup/accounts/' + accountId, { method: 'DELETE' });
    if (response.ok || response.status === 204) {
      await loadAccounts();
    } else {
      button.disabled = false;
    }
  } catch (err) {
    button.disabled = false;
  }
}

async function loadPeople() {
  const response = await apiFetch('/api/v1/setup/accounts/people');
  const people = response.ok ? await response.json() : [];
  const list = qs('peopleList');
  list.innerHTML = '';
  if (!people.length) {
    list.innerHTML = '<p class="empty">No household people found yet.</p>';
    return;
  }
  for (const person of people) {
    const row = document.createElement('div');
    row.className = 'person-row';
    const googleBtn = '<button ' + (providers.google ? '' : 'disabled') + ' onclick="startConnect(\\'google\\', \\'' + person.id + '\\', this)">Connect Google</button>';
    const msBtn = '<button ' + (providers.microsoft ? '' : 'disabled') + ' onclick="startConnect(\\'microsoft\\', \\'' + person.id + '\\', this)">Connect Microsoft</button>';
    row.innerHTML = '<span class="name">' + person.displayName + '</span><span class="actions">' + googleBtn + msBtn + '</span>';
    list.appendChild(row);
  }
}

async function loadAccounts() {
  const response = await apiFetch('/api/v1/setup/accounts');
  const accounts = response.ok ? await response.json() : [];
  const list = qs('accountsList');
  list.innerHTML = '';
  if (!accounts.length) {
    list.innerHTML = '<p class="empty">No accounts connected yet.</p>';
    return;
  }
  for (const account of accounts) {
    const row = document.createElement('div');
    row.className = 'account-row';
    const badge = '<span class="badge ' + account.provider + '">' + (account.provider === 'google' ? 'G' : 'M') + '</span>';
    const pill = account.status === 'connected'
      ? '<span class="pill connected">Connected</span>'
      : '<span class="pill reauth">Needs reconnect</span>';
    const meta = document.createElement('div');
    meta.className = 'account-meta';
    meta.innerHTML = '<div class="email">' + badge + account.providerAccountEmail + pill + '</div>' +
      '<div class="sub">' + account.ownerDisplayName + ' &middot; ' + relativeTime(account.lastSyncedAt) +
      (account.lastSyncError ? ' &middot; ' + account.lastSyncError : '') + '</div>';
    const disconnectBtn = document.createElement('button');
    disconnectBtn.className = 'danger';
    disconnectBtn.textContent = 'Disconnect';
    disconnectBtn.onclick = () => disconnectAccount(account.id, disconnectBtn);
    row.appendChild(meta);
    row.appendChild(disconnectBtn);
    list.appendChild(row);
  }
}

async function boot() {
  qs('gate').style.display = 'none';
  qs('app').style.display = 'block';
  try {
    const response = await fetch('/api/v1/setup/accounts/providers');
    providers = response.ok ? await response.json() : { google: false, microsoft: false };
    renderProviderNotice();
    await Promise.all([loadPeople(), loadAccounts()]);
    readBannerFromQuery();
  } catch (err) {
    // apiFetch already surfaced the reason and reset the gate.
  }
}

if (sessionStorage.getItem(TOKEN_KEY)) {
  boot();
}
</script>
</body>
</html>
"""
