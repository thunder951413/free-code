"""Simple browser chat UI for talking to free-code through FastAPI."""

from __future__ import annotations

from typing import Any, Dict, Iterable, Optional

try:
    from .api_server import create_app as create_api_app
except ImportError:
    from api_server import create_app as create_api_app


CHAT_HTML = """<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>free-code Web Chat</title>
  <style>
    :root {
      color-scheme: dark;
      --bg: #0b1020;
      --panel: #121933;
      --panel-2: #1a2347;
      --text: #e8ecff;
      --muted: #9aa6d1;
      --accent: #5b8cff;
      --border: #2b376c;
      --user: #1f7a4d;
      --assistant: #243f8f;
      --system: #5b5f73;
      --error: #a13b53;
      --hover: #1e2a52;
      --active: #2a3a6e;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: ui-sans-serif, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      background: linear-gradient(180deg, #0a0f1d 0%, #111831 100%);
      color: var(--text);
    }
    .layout {
      display: flex;
      height: 100vh;
      overflow: hidden;
    }
    .sidebar {
      width: 260px;
      min-width: 260px;
      background: var(--panel);
      border-right: 1px solid var(--border);
      display: flex;
      flex-direction: column;
    }
    .sidebar-header {
      padding: 16px;
      border-bottom: 1px solid var(--border);
    }
    .sidebar-header h2 {
      margin: 0 0 12px;
      font-size: 16px;
      color: var(--text);
    }
    .new-chat-btn {
      width: 100%;
      border: 0;
      border-radius: 10px;
      background: var(--accent);
      color: white;
      padding: 10px 14px;
      cursor: pointer;
      font-size: 14px;
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 6px;
    }
    .session-list {
      flex: 1;
      overflow-y: auto;
      padding: 8px;
    }
    .session-item {
      display: flex;
      align-items: center;
      gap: 8px;
      padding: 10px 12px;
      border-radius: 10px;
      cursor: pointer;
      margin-bottom: 4px;
      transition: background 0.15s;
    }
    .session-item:hover {
      background: var(--hover);
    }
    .session-item.active {
      background: var(--active);
    }
    .session-icon {
      width: 32px;
      height: 32px;
      border-radius: 8px;
      background: var(--panel-2);
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 14px;
      flex-shrink: 0;
    }
    .session-info {
      flex: 1;
      min-width: 0;
    }
    .session-title {
      font-size: 13px;
      color: var(--text);
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }
    .session-time {
      font-size: 11px;
      color: var(--muted);
      margin-top: 2px;
    }
    .session-delete {
      width: 24px;
      height: 24px;
      border: 0;
      border-radius: 6px;
      background: transparent;
      color: var(--muted);
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      opacity: 0;
      transition: opacity 0.15s, background 0.15s;
    }
    .session-item:hover .session-delete {
      opacity: 1;
    }
    .session-delete:hover {
      background: var(--error);
      color: white;
    }
    .header-row {
      display: flex;
      align-items: center;
      justify-content: space-between;
      margin-bottom: 4px;
    }
    .header-actions {
      display: flex;
      align-items: center;
      gap: 8px;
    }
    .cwd-btn {
      height: 36px;
      border: 0;
      border-radius: 10px;
      background: var(--panel);
      color: var(--muted);
      cursor: pointer;
      display: flex;
      align-items: center;
      gap: 6px;
      padding: 0 14px;
      font-size: 13px;
      max-width: 320px;
      transition: background 0.15s, color 0.15s;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }
    .cwd-btn:hover {
      background: var(--panel-2);
      color: var(--text);
    }
    .cwd-btn .cwd-icon {
      flex-shrink: 0;
      font-size: 16px;
    }
    .cwd-btn .cwd-text {
      overflow: hidden;
      text-overflow: ellipsis;
    }
    .settings-btn {
      width: 36px;
      height: 36px;
      border: 0;
      border-radius: 10px;
      background: var(--panel);
      color: var(--muted);
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 18px;
      transition: background 0.15s, color 0.15s;
      flex-shrink: 0;
    }
    .settings-btn:hover {
      background: var(--panel-2);
      color: var(--text);
    }
    .modal-overlay {
      position: fixed;
      top: 0;
      left: 0;
      right: 0;
      bottom: 0;
      background: rgba(0, 0, 0, 0.7);
      display: none;
      align-items: center;
      justify-content: center;
      z-index: 1000;
      padding: 20px;
    }
    .modal-overlay.active {
      display: flex;
    }
    .modal {
      background: var(--panel);
      border: 1px solid var(--border);
      border-radius: 16px;
      width: 100%;
      max-width: 600px;
      max-height: 80vh;
      display: flex;
      flex-direction: column;
      overflow: hidden;
    }
    .modal-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 16px 20px;
      border-bottom: 1px solid var(--border);
    }
    .modal-header h3 {
      margin: 0;
      font-size: 18px;
    }
    .modal-close {
      width: 32px;
      height: 32px;
      border: 0;
      border-radius: 8px;
      background: transparent;
      color: var(--muted);
      cursor: pointer;
      font-size: 20px;
      display: flex;
      align-items: center;
      justify-content: center;
    }
    .modal-close:hover {
      background: var(--panel-2);
      color: var(--text);
    }
    .modal-body {
      flex: 1;
      overflow-y: auto;
      padding: 20px;
    }
    .modal-footer {
      display: flex;
      gap: 12px;
      justify-content: flex-end;
      padding: 16px 20px;
      border-top: 1px solid var(--border);
    }
    .modal-footer button {
      border: 0;
      border-radius: 10px;
      padding: 10px 20px;
      cursor: pointer;
      font-size: 14px;
    }
    .modal-footer .btn-secondary {
      background: var(--panel-2);
      color: var(--text);
    }
    .modal-footer .btn-primary {
      background: var(--accent);
      color: white;
    }
    .setting-group {
      margin-bottom: 20px;
    }
    .setting-group label {
      display: block;
      font-size: 13px;
      color: var(--muted);
      margin-bottom: 8px;
    }
    .setting-group input,
    .setting-group textarea {
      width: 100%;
      border: 1px solid var(--border);
      border-radius: 10px;
      background: var(--bg);
      color: var(--text);
      padding: 12px 14px;
      font-size: 14px;
      font-family: inherit;
    }
    .setting-group textarea {
      min-height: 200px;
      resize: vertical;
      font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
      font-size: 13px;
      line-height: 1.5;
    }
    .setting-hint {
      font-size: 12px;
      color: var(--muted);
      margin-top: 6px;
    }
    .main {
      flex: 1;
      display: flex;
      flex-direction: column;
      min-width: 0;
    }
    .page {
      flex: 1;
      display: flex;
      flex-direction: column;
      padding: 20px 24px 24px;
      overflow: hidden;
    }
    .header {
      margin-bottom: 16px;
      flex-shrink: 0;
    }
    .header h1 {
      margin: 0 0 4px;
      font-size: 22px;
    }
    .header p {
      margin: 0;
      color: var(--muted);
      font-size: 13px;
    }
    .toolbar {
      display: flex;
      gap: 12px;
      flex-wrap: wrap;
      align-items: center;
      background: var(--panel);
      border: 1px solid var(--border);
      border-radius: 14px;
      padding: 12px;
      margin-bottom: 16px;
      flex-shrink: 0;
    }
    .toolbar label {
      display: flex;
      flex-direction: column;
      gap: 6px;
      color: var(--muted);
      font-size: 13px;
      min-width: 220px;
      flex: 1;
    }
    .toolbar input {
      width: 100%;
      border: 1px solid var(--border);
      border-radius: 10px;
      background: var(--panel-2);
      color: var(--text);
      padding: 10px 12px;
      font-size: 14px;
    }
    .toolbar button,
    .composer button {
      border: 0;
      border-radius: 10px;
      background: var(--accent);
      color: white;
      padding: 10px 14px;
      cursor: pointer;
      font-size: 14px;
    }
    .toolbar button.secondary {
      background: #33406f;
    }
    .chat-container {
      flex: 1;
      display: flex;
      flex-direction: column;
      min-height: 0;
      overflow: hidden;
    }
    .chat {
      background: rgba(12, 17, 34, 0.85);
      border: 1px solid var(--border);
      border-radius: 16px;
      flex: 1;
      overflow-y: auto;
      padding: 16px;
      display: flex;
      flex-direction: column;
      gap: 12px;
    }
    .message {
      padding: 12px 14px;
      border-radius: 14px;
      line-height: 1.5;
      white-space: pre-wrap;
      word-break: break-word;
      border: 1px solid rgba(255, 255, 255, 0.08);
    }
    .message.user { background: rgba(31, 122, 77, 0.25); border-color: rgba(31, 122, 77, 0.45); }
    .message.assistant { background: rgba(36, 63, 143, 0.28); border-color: rgba(91, 140, 255, 0.4); }
    .message.system { background: rgba(91, 95, 115, 0.25); color: #d6dbf5; }
    .message.error { background: rgba(161, 59, 83, 0.28); border-color: rgba(210, 95, 124, 0.4); }
    .message .role {
      display: block;
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: 0.08em;
      color: var(--muted);
      margin-bottom: 6px;
    }
    .composer {
      margin-top: 16px;
      display: flex;
      gap: 12px;
      align-items: flex-end;
      flex-shrink: 0;
    }
    .composer textarea {
      flex: 1;
      min-height: 90px;
      max-height: 200px;
      resize: vertical;
      border: 1px solid var(--border);
      border-radius: 14px;
      background: var(--panel);
      color: var(--text);
      padding: 12px 14px;
      font-size: 15px;
      line-height: 1.5;
    }
    .footer {
      margin-top: 12px;
      font-size: 13px;
      color: var(--muted);
      flex-shrink: 0;
    }
    .status {
      margin-top: 12px;
      color: var(--muted);
      font-size: 14px;
      flex-shrink: 0;
    }
    .empty-state {
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      height: 100%;
      color: var(--muted);
      text-align: center;
      gap: 12px;
    }
    .empty-state-icon {
      font-size: 48px;
      opacity: 0.5;
    }
    @media (max-width: 720px) {
      .sidebar { width: 200px; min-width: 200px; }
      .composer { flex-direction: column; }
      .composer button { width: 100%; }
    }
    @media (max-width: 560px) {
      .sidebar { display: none; }
    }
  </style>
</head>
<body>
  <div class="layout">
    <aside class="sidebar">
      <div class="sidebar-header">
        <h2>对话历史</h2>
        <button id="newChatBtn" class="new-chat-btn" type="button">
          <span>+</span> 新对话
        </button>
      </div>
      <div id="sessionList" class="session-list"></div>
    </aside>

    <main class="main">
      <div class="page">
        <div class="header">
          <div class="header-row">
            <h1>free-code Web Chat</h1>
            <div class="header-actions">
              <button id="cwdBtn" class="cwd-btn" title="工作路径">
                <span class="cwd-icon">📁</span>
                <span id="cwdText" class="cwd-text">点击设置路径</span>
              </button>
              <button id="settingsBtn" class="settings-btn" title="设置">⚙️</button>
            </div>
          </div>
          <p>一个最小可用的网页对话界面，后端通过 Python bridge 驱动 free-code CLI。</p>
        </div>

        <div class="toolbar">
          <label>
            Session ID
            <input id="sessionId" readonly />
          </label>
          <button id="clearBtn" class="secondary" type="button">清空消息</button>
        </div>

        <div class="chat-container">
          <div id="chat" class="chat"></div>
        </div>

        <form id="chatForm" class="composer">
          <textarea id="messageInput" placeholder="输入你想对 free-code 说的话，例如：请帮我概览当前项目结构"></textarea>
          <button id="sendBtn" type="submit">发送</button>
          <button id="stopBtn" type="button" style="display:none;border:0;border-radius:10px;background:var(--error);color:white;padding:10px 14px;cursor:pointer;font-size:14px;">终止</button>
        </form>

        <div id="status" class="status">就绪</div>
        <div class="footer">默认使用流式接口 `/chat/{session_id}/stream`。</div>
      </div>
    </main>
  </div>

  <div id="settingsModal" class="modal-overlay">
    <div class="modal">
      <div class="modal-header">
        <h3>设置 (settings.json)</h3>
        <button id="modalCloseBtn" class="modal-close">×</button>
      </div>
      <div class="modal-body">
        <div class="setting-group">
          <label>settings.json 文件路径</label>
          <div style="display:flex;gap:8px;">
            <input type="text" id="settingFilePath" placeholder="例如：/path/to/.freecode/settings.json" style="flex:1;">
            <button id="loadFileBtn" type="button" style="border:0;border-radius:10px;background:var(--panel-2);color:var(--text);padding:10px 14px;cursor:pointer;font-size:13px;white-space:nowrap;">加载</button>
          </div>
          <div class="setting-hint">指定路径后点击“加载”读取文件内容，保存时写入该文件</div>
        </div>
        <div class="setting-group">
          <label>OpenAI API Key</label>
          <input type="password" id="settingApiKey" placeholder="sk-...">
        </div>
        <div class="setting-group">
          <label>Base URL</label>
          <input type="text" id="settingBaseUrl" placeholder="https://api.openai.com/v1">
        </div>
        <div class="setting-group">
          <label>模型</label>
          <input type="text" id="settingModel" placeholder="gpt-4">
        </div>
        <div class="setting-group">
          <label>小型快速模型</label>
          <input type="text" id="settingSmallModel" placeholder="gpt-3.5-turbo">
        </div>
        <div class="setting-group">
          <label>环境变量 (每行 KEY=VALUE)</label>
          <textarea id="settingEnv" placeholder="CLAUDE_CODE_USE_OPENAI=1"></textarea>
          <div class="setting-hint">格式：每行一个 KEY=VALUE</div>
        </div>
        <div class="setting-group">
          <label>settings.json 预览</label>
          <textarea id="settingPreview" readonly style="min-height: 150px; opacity: 0.7;"></textarea>
        </div>
      </div>
      <div class="modal-footer">
        <button id="modalCancelBtn" class="btn-secondary">取消</button>
        <button id="modalSaveBtn" class="btn-primary">保存</button>
      </div>
    </div>
  </div>

  <script>
    const chatEl = document.getElementById("chat");
    const statusEl = document.getElementById("status");
    const formEl = document.getElementById("chatForm");
    const inputEl = document.getElementById("messageInput");
    const sendBtn = document.getElementById("sendBtn");
    const stopBtn = document.getElementById("stopBtn");
    const sessionInput = document.getElementById("sessionId");
    const newChatBtn = document.getElementById("newChatBtn");
    const clearBtn = document.getElementById("clearBtn");
    const sessionListEl = document.getElementById("sessionList");
    const settingsBtn = document.getElementById("settingsBtn");
    const cwdBtn = document.getElementById("cwdBtn");
    const cwdText = document.getElementById("cwdText");
    const settingsModal = document.getElementById("settingsModal");
    const modalCloseBtn = document.getElementById("modalCloseBtn");
    const modalCancelBtn = document.getElementById("modalCancelBtn");
    const modalSaveBtn = document.getElementById("modalSaveBtn");
    const loadFileBtn = document.getElementById("loadFileBtn");
    const settingFilePath = document.getElementById("settingFilePath");

    const SESSIONS_KEY = "free-code-web-chat-sessions";
    const CURRENT_KEY = "free-code-web-chat-current-session";
    const SETTINGS_KEY = "free-code-web-chat-settings";
    const SETTINGS_PATH_KEY = "free-code-web-chat-settings-path";
    const CWD_KEY = "free-code-web-chat-cwd";
    let sessions = [];
    let currentSessionId = null;
    let activeAssistantBubble = null;
    let currentAbortController = null;
    let sending = false;

    let currentSettings = {
      env: {},
      openaiApiKey: "",
      openaiBaseUrl: "",
      openaiModel: "",
      openaiSmallFastModel: ""
    };

    function makeSessionId() {
      return "web-" + (crypto.randomUUID ? crypto.randomUUID() : String(Date.now()));
    }

    function formatTime(date) {
      const now = new Date();
      const d = new Date(date);
      const isToday = d.toDateString() === now.toDateString();
      if (isToday) {
        return d.toLocaleTimeString("zh-CN", { hour: "2-digit", minute: "2-digit" });
      }
      return d.toLocaleDateString("zh-CN", { month: "short", day: "numeric" });
    }

    function loadSessions() {
      try {
        const data = localStorage.getItem(SESSIONS_KEY);
        sessions = data ? JSON.parse(data) : [];
      } catch {
        sessions = [];
      }
    }

    function saveSessions() {
      localStorage.setItem(SESSIONS_KEY, JSON.stringify(sessions));
    }

    function getCurrentSession() {
      return sessions.find(s => s.id === currentSessionId);
    }

    function createSession(title = "新对话", cwd = "") {
      const id = makeSessionId();
      const session = {
        id,
        title,
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
        messages: [],
        cwd: cwd || ""
      };
      sessions.unshift(session);
      saveSessions();
      return session;
    }

    function deleteSession(id) {
      const index = sessions.findIndex(s => s.id === id);
      if (index === -1) return false;
      sessions.splice(index, 1);
      saveSessions();
      if (currentSessionId === id) {
        if (sessions.length > 0) {
          switchToSession(sessions[0].id);
        } else {
          const newSession = createSession();
          switchToSession(newSession.id);
        }
      } else {
        renderSessionList();
      }
      return true;
    }

    function switchToSession(id) {
      currentSessionId = id;
      localStorage.setItem(CURRENT_KEY, id);
      const session = getCurrentSession();
      if (session) {
        sessionInput.value = id;
        updateCwdDisplay(session.cwd);
        renderSessionList();
        renderMessages();
        setStatus("已切换到：" + (session.title || id.slice(0, 16)));
      }
    }

    function updateCwdDisplay(cwd) {
      if (cwd) {
        cwdText.textContent = cwd;
        cwdBtn.title = "工作路径：" + cwd;
      } else {
        cwdText.textContent = "点击设置路径";
        cwdBtn.title = "点击设置工作路径";
      }
    }

    function updateSessionTitleFromMessage(text) {
      const session = getCurrentSession();
      if (!session) return;
      if (session.title === "新对话" && text.length > 0) {
        session.title = text.slice(0, 30) + (text.length > 30 ? "..." : "");
        saveSessions();
        renderSessionList();
      }
    }

    function addMessageToSession(role, text) {
      const session = getCurrentSession();
      if (!session) return;
      session.messages.push({ role, text, time: new Date().toISOString() });
      session.updatedAt = new Date().toISOString();
      if (role === "user" && session.title === "新对话") {
        updateSessionTitleFromMessage(text);
      }
      saveSessions();
      renderSessionList();
    }

    function renderSessionList() {
      sessionListEl.innerHTML = "";
      sessions.forEach(session => {
        const item = document.createElement("div");
        item.className = "session-item" + (session.id === currentSessionId ? " active" : "");
        item.onclick = (e) => {
          if (e.target.closest(".session-delete")) return;
          switchToSession(session.id);
        };

        const icon = document.createElement("div");
        icon.className = "session-icon";
        icon.textContent = "💬";

        const info = document.createElement("div");
        info.className = "session-info";

        const title = document.createElement("div");
        title.className = "session-title";
        title.textContent = session.title || session.id.slice(0, 16);

        const time = document.createElement("div");
        time.className = "session-time";
        time.textContent = formatTime(session.updatedAt);

        info.appendChild(title);
        info.appendChild(time);

        const delBtn = document.createElement("button");
        delBtn.className = "session-delete";
        delBtn.textContent = "✕";
        delBtn.title = "删除对话";
        delBtn.onclick = (e) => {
          e.stopPropagation();
          if (confirm("确定要删除这个对话吗？")) {
            deleteSession(session.id);
          }
        };

        item.appendChild(icon);
        item.appendChild(info);
        item.appendChild(delBtn);
        sessionListEl.appendChild(item);
      });
    }

    function renderMessages() {
      chatEl.innerHTML = "";
      const session = getCurrentSession();
      if (!session || session.messages.length === 0) {
        chatEl.innerHTML = `
          <div class="empty-state">
            <div class="empty-state-icon">🤖</div>
            <div>开始一个新的对话吧</div>
          </div>
        `;
        return;
      }
      session.messages.forEach(msg => {
        const contentEl = addMessage(msg.role, msg.text);
        if (msg.role === "assistant") {
          activeAssistantBubble = contentEl;
        }
      });
    }

    function scrollToBottom() {
      chatEl.scrollTop = chatEl.scrollHeight;
    }

    function addMessage(role, text) {
      const wrapper = document.createElement("div");
      wrapper.className = "message " + role;

      const roleEl = document.createElement("span");
      roleEl.className = "role";
      roleEl.textContent = role;

      const contentEl = document.createElement("div");
      contentEl.className = "content";
      contentEl.textContent = text || "";

      wrapper.appendChild(roleEl);
      wrapper.appendChild(contentEl);
      chatEl.appendChild(wrapper);
      scrollToBottom();
      return contentEl;
    }

    function setStatus(text) {
      statusEl.textContent = text;
    }

    function cleanAssistantText(text) {
      if (!text) return "";
      let cleaned = text;
      cleaned = cleaned.replace(/<｜DSML｜[^>]*>/g, "");
      cleaned = cleaned.replace(/<｜begin▁of▁sentence｜>/g, "");
      cleaned = cleaned.replace(/<｜end▁of▁sentence｜>/g, "");
      cleaned = cleaned.replace(/<｜EOT｜>/g, "");
      cleaned = cleaned.replace(/<thinking>[\s\S]*?<\/thinking>/g, "");
      cleaned = cleaned.replace(/<think>[\s\S]*?<\/think>/g, "");
      cleaned = cleaned.replace(/<tool_call>[\s\S]*?<\/tool_call>/g, "");
      cleaned = cleaned.replace(/<｜tool▁calls▁begin｜>[\s\S]*?<｜tool▁calls▁end｜>/g, "");
      cleaned = cleaned.replace(/```tool_call[\s\S]*?```/g, "");
      cleaned = cleaned.trim();
      return cleaned;
    }

    function extractAssistantText(event) {
      let raw = "";
      if (event.type === "assistant_partial") {
        raw = typeof event.delta === "string" ? event.delta : "";
      } else {
        const message = event.message;
        if (!message || !Array.isArray(message.content)) return "";
        raw = message.content
          .filter((block) => block && block.type === "text" && typeof block.text === "string")
          .map((block) => block.text)
          .join("");
      }
      return cleanAssistantText(raw);
    }

    function setSending(next) {
      sending = next;
      sendBtn.disabled = next;
      inputEl.disabled = next;
      sendBtn.style.display = next ? "none" : "";
      stopBtn.style.display = next ? "" : "none";
    }

    function resetAssistantBubble() {
      activeAssistantBubble = null;
    }

    async function ensureSession(sessionId) {
      const session = getCurrentSession();
      const settingsPath = localStorage.getItem(SETTINGS_PATH_KEY) || "";
      const cwd = session?.cwd || "";
      await fetch("/sessions", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          session_id: sessionId,
          settings_path: settingsPath || undefined,
          cwd: cwd || undefined
        }),
      });
    }

    async function sendMessage(message) {
      const session = getCurrentSession();
      if (!session) return;

      addMessage("user", message);
      addMessageToSession("user", message);
      currentAbortController = new AbortController();
      setSending(true);
      setStatus("发送中...");
      resetAssistantBubble();

      await ensureSession(session.id);

      const response = await fetch("/chat/" + encodeURIComponent(session.id) + "/stream", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message }),
        signal: currentAbortController?.signal,
      });

      if (!response.ok || !response.body) {
        throw new Error(await response.text() || "请求失败");
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder("utf-8");
      let buffer = "";
      let fullText = "";

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const chunks = buffer.split("\\n\\n");
        buffer = chunks.pop() || "";

        for (const chunk of chunks) {
          if (!chunk.startsWith("data: ")) continue;
          const event = JSON.parse(chunk.slice(6));

          if (event.type === "assistant" || event.type === "assistant_partial") {
            const text = extractAssistantText(event);
            if (text) {
              if (!activeAssistantBubble) {
                activeAssistantBubble = addMessage("assistant", "");
              }
              activeAssistantBubble.textContent += text;
              fullText += text;
              scrollToBottom();
            }
            continue;
          }

          if (event.type === "system" && event.subtype === "init") {
            setStatus("已连接，模型：" + (event.model || "unknown"));
            continue;
          }

          if (event.type === "result") {
            if (fullText) {
              addMessageToSession("assistant", fullText);
            }
            setStatus("本轮完成");
            continue;
          }

          if (event.type === "error") {
            addMessage("error", event.error || "未知错误");
            addMessageToSession("error", event.error || "未知错误");
            setStatus("发生错误");
            continue;
          }
        }
      }
    }

    stopBtn.addEventListener("click", () => {
      if (currentAbortController) {
        currentAbortController.abort();
      }
    });

    formEl.addEventListener("submit", async (event) => {
      event.preventDefault();
      if (sending) return;
      const message = inputEl.value.trim();
      if (!message) return;

      inputEl.value = "";
      try {
        await sendMessage(message);
      } catch (error) {
        if (error.name === "AbortError") {
          addMessage("system", "已手动终止");
          addMessageToSession("system", "已手动终止");
          setStatus("已终止");
        } else {
          const errorMsg = error instanceof Error ? error.message : String(error);
          addMessage("error", errorMsg);
          addMessageToSession("error", errorMsg);
          setStatus("请求失败");
        }
      } finally {
        currentAbortController = null;
        setSending(false);
        resetAssistantBubble();
        inputEl.focus();
      }
    });

    newChatBtn.addEventListener("click", () => {
      const savedCwd = localStorage.getItem(CWD_KEY) || "";
      const newSession = createSession("新对话", savedCwd);
      switchToSession(newSession.id);
      setStatus("已创建新会话");
    });

    cwdBtn.addEventListener("click", () => {
      const session = getCurrentSession();
      const current = session?.cwd || localStorage.getItem(CWD_KEY) || "";
      const path = prompt("设置工作路径（CLI 启动目录）：", current);
      if (path === null) return;
      const trimmed = path.trim();
      if (session) {
        session.cwd = trimmed;
        saveSessions();
      }
      localStorage.setItem(CWD_KEY, trimmed);
      updateCwdDisplay(trimmed);
      if (trimmed) {
        setStatus("工作路径已设置为：" + trimmed + "（新会话生效）");
      } else {
        setStatus("已清除工作路径（新会话生效）");
      }
    });

    clearBtn.addEventListener("click", () => {
      const session = getCurrentSession();
      if (session) {
        session.messages = [];
        saveSessions();
        renderMessages();
        setStatus("已清空当前会话消息");
      }
    });

    function loadSettings() {
      try {
        const data = localStorage.getItem(SETTINGS_KEY);
        if (data) {
          currentSettings = { ...currentSettings, ...JSON.parse(data) };
        }
      } catch (e) {
        console.error("Failed to load settings:", e);
      }
    }

    function saveSettingsToStorage() {
      localStorage.setItem(SETTINGS_KEY, JSON.stringify(currentSettings));
    }

    function applySettingsToForm(settings) {
      document.getElementById("settingApiKey").value = settings.openaiApiKey || "";
      document.getElementById("settingBaseUrl").value = settings.openaiBaseUrl || "";
      document.getElementById("settingModel").value = settings.openaiModel || "";
      document.getElementById("settingSmallModel").value = settings.openaiSmallFastModel || "";
      document.getElementById("settingEnv").value = Object.entries(settings.env || {})
        .map(([k, v]) => k + "=" + v)
        .join("\\n");
    }

    function openSettingsModal() {
      settingFilePath.value = localStorage.getItem(SETTINGS_PATH_KEY) || "";
      applySettingsToForm(currentSettings);
      updateSettingsPreview();
      settingsModal.classList.add("active");
    }

    function closeSettingsModal() {
      settingsModal.classList.remove("active");
    }

    function updateSettingsPreview() {
      const preview = buildSettingsFromForm();
      document.getElementById("settingPreview").value = JSON.stringify(preview, null, 2);
    }

    function buildSettingsFromForm() {
      const envText = document.getElementById("settingEnv").value || "";
      const env = {};
      envText.split("\\n").forEach(line => {
        const eq = line.indexOf("=");
        if (eq > 0) {
          env[line.slice(0, eq).trim()] = line.slice(eq + 1).trim();
        }
      });

      return {
        env,
        openaiApiKey: document.getElementById("settingApiKey").value || "",
        openaiBaseUrl: document.getElementById("settingBaseUrl").value || "",
        openaiModel: document.getElementById("settingModel").value || "",
        openaiSmallFastModel: document.getElementById("settingSmallModel").value || ""
      };
    }

    settingsBtn.addEventListener("click", openSettingsModal);
    modalCloseBtn.addEventListener("click", closeSettingsModal);
    modalCancelBtn.addEventListener("click", closeSettingsModal);

    loadFileBtn.addEventListener("click", async () => {
      const path = settingFilePath.value.trim();
      if (!path) {
        alert("请输入文件路径");
        return;
      }
      try {
        loadFileBtn.disabled = true;
        loadFileBtn.textContent = "加载中...";
        const resp = await fetch("/settings?path=" + encodeURIComponent(path));
        if (!resp.ok) {
          const err = await resp.json();
          throw new Error(err.detail || "加载失败");
        }
        const result = await resp.json();
        currentSettings = { ...currentSettings, ...result.data };
        localStorage.setItem(SETTINGS_PATH_KEY, path);
        applySettingsToForm(currentSettings);
        updateSettingsPreview();
        setStatus("已从文件加载设置：" + result.path);
      } catch (e) {
        alert("加载失败：" + (e instanceof Error ? e.message : String(e)));
      } finally {
        loadFileBtn.disabled = false;
        loadFileBtn.textContent = "加载";
      }
    });

    modalSaveBtn.addEventListener("click", async () => {
      currentSettings = buildSettingsFromForm();
      saveSettingsToStorage();
      const path = settingFilePath.value.trim();
      if (path) {
        try {
          modalSaveBtn.disabled = true;
          modalSaveBtn.textContent = "保存中...";
          const resp = await fetch("/settings", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ path, data: currentSettings })
          });
          if (!resp.ok) {
            const err = await resp.json();
            throw new Error(err.detail || "保存失败");
          }
          localStorage.setItem(SETTINGS_PATH_KEY, path);
          closeSettingsModal();
          setStatus("设置已保存到文件：" + path);
        } catch (e) {
          alert("保存到文件失败：" + (e instanceof Error ? e.message : String(e)));
        } finally {
          modalSaveBtn.disabled = false;
          modalSaveBtn.textContent = "保存";
        }
      } else {
        closeSettingsModal();
        setStatus("设置已保存到浏览器");
      }
    });
    settingsModal.addEventListener("click", (e) => {
      if (e.target === settingsModal) closeSettingsModal();
    });
    ["settingApiKey", "settingBaseUrl", "settingModel", "settingSmallModel", "settingEnv", "settingFilePath"].forEach(id => {
      document.getElementById(id).addEventListener("input", updateSettingsPreview);
    });

    function init() {
      loadSessions();
      loadSettings();
      const savedCurrent = localStorage.getItem(CURRENT_KEY);
      if (savedCurrent && sessions.find(s => s.id === savedCurrent)) {
        currentSessionId = savedCurrent;
      } else if (sessions.length > 0) {
        currentSessionId = sessions[0].id;
      } else {
        const newSession = createSession();
        currentSessionId = newSession.id;
      }
      switchToSession(currentSessionId);
    }

    init();
  </script>
</body>
</html>
"""


def create_web_chat_app(
    *,
    cli_path: Optional[str] = None,
    cwd: Optional[str] = None,
    extra_args: Optional[Iterable[str]] = None,
    env: Optional[Dict[str, str]] = None,
    auto_permission_handler=None,
) -> Any:
    app = create_api_app(
        cli_path=cli_path,
        cwd=cwd,
        extra_args=extra_args,
        env=env,
        auto_permission_handler=auto_permission_handler,
    )

    try:
        from fastapi.responses import HTMLResponse, RedirectResponse
    except ImportError as exc:
        raise RuntimeError(
            "This module requires FastAPI. Install it with: pip install fastapi uvicorn"
        ) from exc

    @app.get("/", include_in_schema=False)
    def home() -> HTMLResponse:
        return HTMLResponse(CHAT_HTML)

    @app.get("/chat", include_in_schema=False)
    def chat_page() -> HTMLResponse:
        return HTMLResponse(CHAT_HTML)

    @app.get("/favicon.ico", include_in_schema=False)
    def favicon() -> RedirectResponse:
        return RedirectResponse(url="/")

    return app
