/* SaktiOS Custom UI Shell — client logic.
 *
 * Splash boot -> reveal shell; chat via /api/chat; automation via
 * /api/do ("do: <task>" in the dock); live logs poll /api/logs;
 * launcher from /api/apps; custom browser placeholder overlay.
 */
"use strict";

const $ = (id) => document.getElementById(id);

const bootLines = [
  "Initializing AI Core...",
  "Loading Modules...",
  "Starting interface...",
];

const state = { apps: [], logs: [] };

/* ------------------------------------------------------------- boot */
async function bootSplash() {
  const fill = $("splash-fill");
  const bootEl = $("splash-boot");
  const step = 100 / (bootLines.length + 1);
  let progress = 0;
  for (const line of bootLines) {
    bootEl.textContent = line;
    await sleep(450);
    progress += step;
    fill.style.width = progress + "%";
  }
  bootEl.textContent = "Welcome.";
  fill.style.width = "100%";
  await sleep(350);
  finishSplash();
}

function finishSplash() {
  const splash = $("splash");
  splash.classList.add("gone");
  $("shell").classList.remove("hidden");
  $("shell").classList.add("ready");
  setTimeout(() => splash.remove(), 700);
  initApp();
}

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

/* ---------------------------------------------------------- the app */
async function initApp() {
  const status = await fetchJSON("/api/status") || {};
  const pill = $("engine-pill");
  pill.textContent = status.ready ? "ready" : "offline";
  pill.classList.toggle("ready", !!status.ready);
  $("tag").textContent = status.engine || "offline";
  tickClock();
  setInterval(tickClock, 15_000);
  loadTheme();
  pollLogs();
  setInterval(pollLogs, 3_000);
  buildLauncher();
}

async function tickClock() {
  const now = new Date();
  $("clock").textContent = now.toLocaleTimeString([], { hour: "2-digit",
    minute: "2-digit" });
}

async function loadTheme() {
  const theme = await fetchJSON("/api/theme");
  if (!theme) return;
  const root = document.documentElement.style;
  if (theme.palette) {
    const p = theme.palette;
    if (p.primary) root.setProperty("--sakti-primary", p.primary.hex);
    if (p.secondary) root.setProperty("--sakti-secondary", p.secondary.hex);
    if (p.accent) root.setProperty("--sakti-accent", p.accent.hex);
  }
}

/* ------------------------------------------------------------- chat */
const chatForm = $("chat-form");
chatForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const text = $("chat-input").value.trim();
  if (!text) return;
  appendMsg("user", text);
  $("chat-input").value = "";
  const typing = appendTyping();
  const res = await sendChat(text, false);
  typing.remove();
  if (res && res.ok) {
    appendMsg("ai", res.reply);
  } else {
    appendMsg("err", (res && res.error) || (res && res.reply) ||
      "AI core did not reply.");
  }
});

async function sendChat(message, dry) {
  try {
    const res = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message, dry: !!dry }),
    });
    return await res.json();
  } catch (err) {
    return { ok: false, error: String(err) };
  }
}

function appendMsg(kind, text) {
  const el = document.createElement("div");
  el.className = "msg " + kind;
  el.textContent = text;
  $("chat-log").appendChild(el);
  $("chat-log").scrollTop = $("chat-log").scrollHeight;
  return el;
}

function appendTyping() {
  const el = document.createElement("div");
  el.className = "typing";
  el.textContent = "Thinking\u2026";
  $("chat-log").appendChild(el);
  $("chat-log").scrollTop = $("chat-log").scrollHeight;
  return el;
}

/* -------------------------------------------------------------- dock */
const dockForm = $("dock-form");
dockForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const text = $("dock-input").value.trim();
  if (!text) return;
  const doMatch = text.match(/^do[\s:]+(.+)$/i);
  if (doMatch) {
    await runAutomation(doMatch[1]);
  } else {
    await sendToChat(text);
  }
});

async function sendToChat(text) {
  appendMsg("user", text);
  $("dock-input").value = "";
  const typing = appendTyping();
  const res = await sendChat(text, false);
  typing.remove();
  appendMsg(res.ok ? "ai" : "err", res.reply || "no response");
}

async function runAutomation(task) {
  appendMsg("user", "do: " + task);
  $("dock-input").value = "";
  const typing = appendTyping();
  try {
    const res = await fetch("/api/do", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ task, dry: false }),
    });
    const report = await res.json();
    typing.remove();
    let summary = report.success
      ? "Done \u2014 all steps succeeded."
      : report.plan_error
        ? "Plan refused: " + report.plan_error
        : "Stopped: " + (report.failed_step || "unknown failure");
    appendMsg(report.success ? "ai" : "err", summary + "\nPlan:\n" +
      (report.steps || []).map((s) => s.order + ". " + s.description)
        .join("\n"));
  } catch (err) {
    typing.remove();
    appendMsg("err", "Automation error: " + err);
  }
}

/* ---------------------------------------------------------------- logs */
async function pollLogs() {
  const data = await fetchJSON("/api/logs?limit=50");
  if (!data || !data.entries || !data.entries.length) {
    if (!state.logs) $("log-view").textContent = "No activity yet.";
    return;
  }
  const view = $("log-view");
  const short = data.entries.slice(0, 40);
  let html = "";
  for (const e of short) {
    const cls = e.status === "success" ? "ok" :
      e.status === "fail" ? "fail" : "dim";
    const st = e.status === "success" ? "\u2713" :
      e.status === "fail" ? "\u2717" : "\u2013";
    const when = (e.timestamp || "").split("T")[1]?.slice(0, 8) || "";
    html += '<span class="log-line"><span class="' + cls + '">' +
      st + " " + when + "</span> <span>" + esc(e.command || "") +
      "</span></span>";
  }
  view.innerHTML = html;
  state.logs = true;
}

$("log-clear").addEventListener("click", () => {
  $("log-view").textContent = "";
  state.logs = false;
});

/* ------------------------------------------------------- launcher */
async function buildLauncher() {
  const data = await fetchJSON("/api/apps");
  if (!data || !data.apps) return;
  const grid = $("app-grid");
  for (const app of data.apps) {
    const btn = document.createElement("button");
    btn.className = "app";
    btn.innerHTML = '<div class="app-name">' + app.name + "</div>" +
      '<div class="app-desc">' + (app.desc || "") + "</div>";
    btn.addEventListener("click", () => {
      closeLauncher();
      launchApp(app);
    });
    grid.appendChild(btn);
  }
}

function launchApp(app) {
  if (app.action === "browser") {
    openBrowser();
  } else if (app.command) {
    runAutomation("launch " + app.command + " -- " + app.name);
  }
}

function openLauncher() {
  $("launcher").classList.remove("hidden");
  requestAnimationFrame(() => $("launcher").classList.add("open"));
  $("launcher").setAttribute("aria-hidden", "false");
}

function closeLauncher() {
  $("launcher").classList.remove("open");
  setTimeout(() => $("launcher").classList.add("hidden"), 260);
}

$("btn-launcher").addEventListener("click", openLauncher);
$("btn-launcher-close").addEventListener("click", closeLauncher);

/* -------------------------------------------------------- browser */
function openBrowser() {
  const b = $("browser");
  b.classList.remove("hidden");
  b.setAttribute("aria-hidden", "false");
  $("browser-url").focus();
}

function closeBrowser() {
  $("browser").classList.add("hidden");
  $("browser").setAttribute("aria-hidden", "true");
  const frame = $("browser-frame");
  frame.innerHTML = frame.innerHTML; // drop any live iframe
}

$("browser-close").addEventListener("click", closeBrowser);
$("browser-form").addEventListener("submit", (event) => {
  event.preventDefault();
  let url = $("browser-url").value.trim();
  if (!url) return;
  if (!/^https?:\/\/|^file:\/\//i.test(url)) url = "https://" + url;
  const frame = $("browser-frame");
  frame.innerHTML = '<iframe src="' + url +
    '" sandbox="allow-scripts allow-same-origin allow-forms"></iframe>';
});

/* ---------------------------------------------------------- utils */
async function fetchJSON(path) {
  try {
    const res = await fetch(path);
    return await res.json();
  } catch (err) {
    return null;
  }
}

function esc(text) {
  return String(text).replace(/[&<>"']/g, (ch) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
  }[ch]));
}

document.addEventListener("keydown", (event) => {
  if (event.key === "Escape") closeBrowser();
});

bootSplash();