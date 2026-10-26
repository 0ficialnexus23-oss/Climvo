"use strict";

/* ============================================================
   Elielsito AI — lógica de la interfaz
   ============================================================ */

const $ = (sel) => document.querySelector(sel);
const $$ = (sel) => Array.from(document.querySelectorAll(sel));

const state = {
  history: [],
  sending: false,
  controller: null,
};

/* ------------------------------------------------------------ utilidades */
async function api(path, options = {}) {
  const res = await fetch(path, {
    ...options,
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
  });
  if (!res.ok) {
    let detail = `Error ${res.status}`;
    try {
      const data = await res.json();
      if (data && data.detail) detail = typeof data.detail === "string" ? data.detail : JSON.stringify(data.detail);
    } catch (_) { /* cuerpo no JSON */ }
    throw new Error(detail);
  }
  if (res.status === 204) return null;
  return res.json();
}

let toastTimer = null;
function toast(message, isError = false) {
  let el = document.getElementById("toast");
  if (!el) {
    el = document.createElement("div");
    el.id = "toast";
    el.className = "toast";
    document.body.appendChild(el);
  }
  el.textContent = message;
  el.classList.toggle("error", isError);
  el.classList.add("show");
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => el.classList.remove("show"), 3200);
}

function fmtTime(iso) {
  if (!iso) return "";
  const d = new Date(iso);
  return Number.isNaN(d.getTime()) ? iso : d.toLocaleString("es-MX");
}

/* --------------------------------------------------------------- vistas */
function showView(name) {
  $$(".nav-item").forEach((b) => b.classList.toggle("is-active", b.dataset.view === name));
  $$(".view").forEach((v) => v.classList.toggle("is-active", v.id === `view-${name}`));
  if (name === "tools") loadTools();
  if (name === "memory") loadMemory();
  if (name === "audit") loadAudit();
  if (name === "status") loadStatus();
}

/* ---------------------------------------------------------------- chat */
function scrollToEnd() {
  const box = $("#messages");
  box.scrollTop = box.scrollHeight;
}

function addMessage(role, text, extra = {}) {
  const empty = $("#chat-empty");
  if (empty) empty.remove();

  const wrap = document.createElement("div");
  wrap.className = `msg ${role}`;

  const bubble = document.createElement("div");
  bubble.className = "bubble";

  if (role === "assistant") {
    const who = document.createElement("div");
    who.className = "who";
    who.textContent = "Elielsito";
    bubble.appendChild(who);
  }

  const body = document.createElement("div");
  body.textContent = text;
  bubble.appendChild(body);

  if (extra.data) {
    const meta = document.createElement("div");
    meta.className = "meta";
    const chips = [
      extra.data.model ? `modelo: ${extra.data.model}` : null,
      `pasos: ${extra.data.steps ?? 0}`,
      `herramientas: ${extra.data.tool_calls ?? 0}`,
      extra.data.stopped_reason && extra.data.stopped_reason !== "stop" ? `fin: ${extra.data.stopped_reason}` : null,
    ].filter(Boolean);
    chips.forEach((c) => {
      const chip = document.createElement("span");
      chip.className = "chip";
      chip.textContent = c;
      meta.appendChild(chip);
    });
    bubble.appendChild(meta);
  }

  if (extra.data && extra.data.trace && extra.data.trace.length) {
    const details = document.createElement("details");
    details.className = "trace";
    const summary = document.createElement("summary");
    summary.textContent = `${extra.data.trace.length} herramienta(s) usada(s)`;
    details.appendChild(summary);
    extra.data.trace.forEach((t) => {
      const line = document.createElement("div");
      const name = document.createElement("b");
      name.textContent = t.tool;
      line.appendChild(name);
      line.appendChild(document.createTextNode(`(${JSON.stringify(t.arguments)}) → ${String(t.result).slice(0, 220)}`));
      details.appendChild(line);
    });
    bubble.appendChild(details);
  }

  wrap.appendChild(bubble);
  $("#messages").appendChild(wrap);
  scrollToEnd();
  return wrap;
}

function addTyping() {
  const wrap = document.createElement("div");
  wrap.className = "msg assistant";
  const bubble = document.createElement("div");
  bubble.className = "bubble";
  const who = document.createElement("div");
  who.className = "who";
  who.textContent = "Elielsito";
  const dots = document.createElement("span");
  dots.className = "typing";
  dots.innerHTML = "<span></span><span></span><span></span>";
  bubble.appendChild(who);
  bubble.appendChild(dots);
  wrap.appendChild(bubble);
  $("#messages").appendChild(wrap);
  scrollToEnd();
  return wrap;
}

async function sendMessage() {
  const input = $("#input");
  const text = input.value.trim();
  if (!text || state.sending) return;

  state.sending = true;
  $("#send").disabled = true;
  $("#stop").hidden = false;
  input.value = "";
  autoResize(input);

  addMessage("user", text);
  const typing = addTyping();

  state.controller = new AbortController();
  try {
    const data = await api("/api/chat", {
      method: "POST",
      body: JSON.stringify({ message: text, history: state.history.slice(-20) }),
      signal: state.controller.signal,
    });
    typing.remove();
    addMessage("assistant", data.reply || "(respuesta vacía)", { data });
    state.history.push({ role: "user", content: text });
    state.history.push({ role: "assistant", content: data.reply || "" });
    if (state.history.length > 40) state.history = state.history.slice(-40);
  } catch (err) {
    typing.remove();
    if (err && err.name === "AbortError") {
      addMessage("assistant", "Detuve la respuesta, jefe.");
    } else {
      addMessage("assistant", `No pude responder: ${err.message || err}`);
    }
  } finally {
    state.sending = false;
    $("#send").disabled = false;
    $("#stop").hidden = true;
    state.controller = null;
    input.focus();
  }
}

function autoResize(el) {
  el.style.height = "auto";
  el.style.height = `${Math.min(el.scrollHeight, 180)}px`;
}

/* -------------------------------------------------------------- estado */
async function loadStatus() {
  try {
    const s = await api("/api/status");
    setConn(true);
    $("#model-line").textContent = `${s.provider} · ${s.model}`;
    $("#chat-sub").textContent = `Modelo: ${s.model} (${s.provider}) — se ejecuta en tu equipo.`;
    renderStatus(s);
  } catch (err) {
    setConn(false);
    toast(`No pude leer el estado: ${err.message}`, true);
  }
}

function setConn(ok) {
  const text = ok ? "Conectado" : "Sin conexión";
  const cls = ok ? "dot ok" : "dot bad";
  const pairs = [
    ["#dot", "#conn-text"],
    ["#dot-m", "#conn-text-m"],
  ];
  pairs.forEach(([dotSel, textSel]) => {
    const dot = $(dotSel);
    const label = $(textSel);
    if (dot) dot.className = cls;
    if (label) label.textContent = text;
  });
}

function card(title, value, sub, badge) {
  const el = document.createElement("div");
  el.className = "card";
  const k = document.createElement("div");
  k.className = "k";
  k.textContent = title;
  const v = document.createElement("div");
  v.className = "value";
  v.textContent = value;
  const p = document.createElement("p");
  p.textContent = sub || "";
  el.appendChild(k);
  el.appendChild(v);
  el.appendChild(p);
  if (badge) {
    const b = document.createElement("span");
    b.className = `badge ${badge.tone || ""}`;
    b.textContent = badge.text;
    el.appendChild(b);
  }
  return el;
}

function renderStatus(s) {
  const grid = $("#status-grid");
  grid.innerHTML = "";
  grid.appendChild(card("Identidad", s.identity?.name || "Elielsito", s.identity?.role || ""));
  grid.appendChild(card("Proveedor", s.provider, s.base_url || "—"));
  grid.appendChild(card("Modelo", s.model, "Modelo activo"));
  grid.appendChild(card("Herramientas", String(s.tools), "Registradas"));
  const total = s.memory ? s.memory._total ?? 0 : 0;
  grid.appendChild(card("Recuerdos", String(total), "En memoria persistente"));
  grid.appendChild(
    card("Límites", `${s.limits.max_steps} pasos`, `máximo ${s.limits.max_seconds} s`, {
      text: s.shell_allowed ? "shell permitido" : "shell desactivado",
      tone: s.shell_allowed ? "danger" : "read",
    }),
  );
}

/* ----------------------------------------------------------- herramientas */
async function loadTools() {
  const grid = $("#tools-grid");
  try {
    const tools = await api("/api/tools");
    grid.innerHTML = "";
    if (!tools.length) {
      grid.appendChild(card("Sin herramientas", "0", "No hay herramientas registradas."));
      return;
    }
    tools.forEach((t) => {
      const el = document.createElement("div");
      el.className = "card";
      const h = document.createElement("h3");
      h.textContent = t.name;
      const p = document.createElement("p");
      p.textContent = t.description;
      const b = document.createElement("span");
      b.className = `badge ${t.permission}`;
      b.textContent = t.permission;
      el.appendChild(h);
      el.appendChild(p);
      el.appendChild(b);
      grid.appendChild(el);
    });
  } catch (err) {
    toast(`No pude cargar las herramientas: ${err.message}`, true);
  }
}

/* ---------------------------------------------------------------- memoria */
async function loadMemory(query) {
  const list = $("#memory-list");
  try {
    const q = query !== undefined ? query : $("#mem-search").value.trim();
    const url = q ? `/api/memory?q=${encodeURIComponent(q)}&limit=100` : "/api/memory?limit=100";
    const items = await api(url);
    list.innerHTML = "";
    if (!items.length) {
      list.appendChild(card("Vacío", "0", q ? "Sin resultados para esa búsqueda." : "Todavía no hay recuerdos."));
      return;
    }
    items.forEach((item) => {
      const el = document.createElement("div");
      el.className = "item";

      const body = document.createElement("div");
      body.className = "body";

      const p = document.createElement("p");
      p.textContent = item.content;
      body.appendChild(p);

      const sub = document.createElement("div");
      sub.className = "sub";
      const parts = [
        item.category,
        item.kind === "fact" ? "hecho" : "hipótesis",
        item.source ? `fuente: ${item.source}` : null,
        fmtTime(item.updated_at),
      ].filter(Boolean);
      parts.forEach((text) => {
        const chip = document.createElement("span");
        chip.className = "chip";
        chip.textContent = text;
        sub.appendChild(chip);
      });
      body.appendChild(sub);

      const del = document.createElement("button");
      del.className = "x";
      del.title = "Eliminar recuerdo";
      del.type = "button";
      del.textContent = "×";
      del.addEventListener("click", () => deleteMemory(item.id));

      el.appendChild(body);
      el.appendChild(del);
      list.appendChild(el);
    });
  } catch (err) {
    toast(`No pude cargar la memoria: ${err.message}`, true);
  }
}

async function addMemory(event) {
  event.preventDefault();
  const content = $("#mem-content").value.trim();
  if (!content) return;
  try {
    const data = await api("/api/memory", {
      method: "POST",
      body: JSON.stringify({
        content,
        category: $("#mem-category").value,
        kind: $("#mem-kind").value,
      }),
    });
    $("#mem-content").value = "";
    toast(data.created ? "Recuerdo guardado." : "Recuerdo actualizado.");
    loadMemory("");
    loadStatus();
  } catch (err) {
    toast(`No se pudo guardar: ${err.message}`, true);
  }
}

async function deleteMemory(id) {
  if (!window.confirm("¿Eliminar este recuerdo?")) return;
  try {
    await api(`/api/memory/${id}`, { method: "DELETE" });
    toast("Recuerdo eliminado.");
    loadMemory();
    loadStatus();
  } catch (err) {
    toast(`No se pudo eliminar: ${err.message}`, true);
  }
}

/* -------------------------------------------------------------- auditoría */
async function loadAudit() {
  const list = $("#audit-list");
  try {
    const events = await api("/api/audit?limit=100");
    list.innerHTML = "";
    if (!events.length) {
      list.appendChild(card("Sin eventos", "0", "Todavía no hay actividad registrada."));
      return;
    }
    events.slice().reverse().forEach((ev) => {
      const el = document.createElement("div");
      el.className = "item";

      const body = document.createElement("div");
      body.className = "body";

      const p = document.createElement("p");
      p.textContent = ev.event + (ev.tool ? ` · ${ev.tool}` : "");
      body.appendChild(p);

      const sub = document.createElement("div");
      sub.className = "sub";
      const chips = [fmtTime(ev.ts)];
      if (ev.ok !== undefined) chips.push(ev.ok ? "ok" : "error");
      if (ev.duration_ms !== undefined) chips.push(`${ev.duration_ms} ms`);
      chips.forEach((text) => {
        const chip = document.createElement("span");
        chip.className = "chip";
        chip.textContent = text;
        sub.appendChild(chip);
      });
      body.appendChild(sub);

      el.appendChild(body);
      list.appendChild(el);
    });
  } catch (err) {
    toast(`No pude cargar la auditoría: ${err.message}`, true);
  }
}

/* ----------------------------------------------------------------- inicio */
function init() {
  $$(".nav-item").forEach((b) => b.addEventListener("click", () => showView(b.dataset.view)));

  $("#composer").addEventListener("submit", (e) => {
    e.preventDefault();
    sendMessage();
  });

  const input = $("#input");
  input.addEventListener("input", () => autoResize(input));
  input.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  });

  $("#stop").addEventListener("click", () => {
    if (state.controller) state.controller.abort();
  });

  $("#clear-chat").addEventListener("click", () => {
    state.history = [];
    $("#messages").innerHTML = "";
    const empty = document.createElement("div");
    empty.className = "empty";
    empty.id = "chat-empty";
    const logo = document.createElement("div");
    logo.className = "empty-logo";
    logo.textContent = "E";
    const p = document.createElement("p");
    p.textContent = "Aquí estoy, jefe. ¿Qué vamos a hacer hoy?";
    empty.appendChild(logo);
    empty.appendChild(p);
    $("#messages").appendChild(empty);
  });

  $("#memory-form").addEventListener("submit", addMemory);
  $("#mem-search-btn").addEventListener("click", () => loadMemory());
  $("#mem-search").addEventListener("keydown", (e) => {
    if (e.key === "Enter") { e.preventDefault(); loadMemory(); }
  });

  $("#refresh-tools").addEventListener("click", loadTools);
  $("#refresh-audit").addEventListener("click", loadAudit);
  $("#refresh-status").addEventListener("click", loadStatus);

  loadStatus();
  input.focus();
  setInterval(loadStatus, 20000);
}

document.addEventListener("DOMContentLoaded", init);
