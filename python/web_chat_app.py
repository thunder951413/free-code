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
      background: var(--secondary-btn, #33406f);
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
      border: 1px solid var(--msg-border, rgba(255, 255, 255, 0.08));
    }
    .message.user { background: var(--user-bg, rgba(31, 122, 77, 0.25)); border-color: var(--user-border, rgba(31, 122, 77, 0.45)); }
    .message.assistant { background: var(--assistant-bg, rgba(36, 63, 143, 0.28)); border-color: var(--assistant-border, rgba(91, 140, 255, 0.4)); }
    .message.system { background: var(--system-bg, rgba(91, 95, 115, 0.25)); color: var(--system-text, #d6dbf5); }
    .message.error { background: var(--error-bg, rgba(161, 59, 83, 0.28)); border-color: var(--error-border, rgba(210, 95, 124, 0.4)); }
    .message .role {
      display: block;
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: 0.08em;
      color: var(--muted);
      margin-bottom: 6px;
    }
    .tool-call-block {
      display: block;
      font-size: 12px;
      color: var(--tool-text, #e8a0a0);
      margin: 4px 0;
      padding: 4px 8px;
      border-left: 2px solid var(--tool-border, rgba(232, 160, 160, 0.4));
      white-space: pre-wrap;
      word-break: break-word;
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
    .theme-btn {
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
      position: relative;
    }
    .theme-btn:hover {
      background: var(--panel-2);
      color: var(--text);
    }
    .theme-dropdown {
      position: absolute;
      top: calc(100% + 8px);
      right: 0;
      background: var(--panel);
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 6px;
      min-width: 160px;
      box-shadow: 0 8px 24px rgba(0,0,0,0.4);
      z-index: 2000;
      display: none;
    }
    .theme-dropdown.active {
      display: block;
    }
    .theme-option {
      display: flex;
      align-items: center;
      gap: 10px;
      padding: 10px 12px;
      border-radius: 8px;
      cursor: pointer;
      transition: background 0.15s;
      font-size: 14px;
      color: var(--text);
      border: 0;
      background: transparent;
      width: 100%;
      text-align: left;
    }
    .theme-option:hover {
      background: var(--hover);
    }
    .theme-option.active {
      background: var(--active);
    }
    .theme-swatch {
      width: 20px;
      height: 20px;
      border-radius: 6px;
      border: 2px solid var(--border);
      flex-shrink: 0;
    }
    .theme-option.active .theme-swatch {
      border-color: var(--accent);
      box-shadow: 0 0 0 2px var(--accent);
    }
    @media (max-width: 720px) {
      .sidebar { width: 200px; min-width: 200px; }
      .composer { flex-direction: column; }
      .composer button { width: 100%; }
    }
    .content p { margin: 0 0 8px; }
    .content p:last-child { margin-bottom: 0; }
    .content h1, .content h2, .content h3, .content h4, .content h5, .content h6 {
      margin: 8px 0 4px;
      font-weight: 600;
      line-height: 1.3;
    }
    .content h1 { font-size: 1.4em; }
    .content h2 { font-size: 1.25em; }
    .content h3 { font-size: 1.15em; }
    .content h4 { font-size: 1.05em; }
    .content ul, .content ol { margin: 4px 0; padding-left: 20px; }
    .content li { margin: 2px 0; }
    .content code {
      background: var(--panel-2);
      padding: 1px 4px;
      border-radius: 4px;
      font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
      font-size: 0.92em;
    }
    .content pre {
      background: var(--panel-2);
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 10px;
      margin: 8px 0;
      overflow-x: auto;
    }
    .content pre code {
      background: transparent;
      padding: 0;
      border-radius: 0;
      font-size: 0.9em;
    }
    .content blockquote {
      border-left: 3px solid var(--accent);
      margin: 8px 0;
      padding: 4px 12px;
      background: rgba(91, 140, 255, 0.08);
      border-radius: 0 6px 6px 0;
    }
    .content a {
      color: var(--accent);
      text-decoration: none;
    }
    .content a:hover { text-decoration: underline; }
    .content hr {
      border: 0;
      border-top: 1px solid var(--border);
      margin: 12px 0;
    }
    .content table {
      border-collapse: collapse;
      margin: 8px 0;
      width: auto;
      max-width: 100%;
    }
    .content th, .content td {
      border: 1px solid var(--border);
      padding: 6px 10px;
      text-align: left;
    }
    .content th {
      background: var(--panel-2);
      font-weight: 600;
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
              <div style="position:relative;">
                <button id="themeBtn" class="theme-btn" title="切换主题">🎨</button>
                <div id="themeDropdown" class="theme-dropdown">
                  <button class="theme-option active" data-theme="dark">
                    <span class="theme-swatch" style="background:#0b1020;"></span>
                    深色
                  </button>
                  <button class="theme-option" data-theme="light">
                    <span class="theme-swatch" style="background:#f5f5f5;"></span>
                    浅色
                  </button>
                  <button class="theme-option" data-theme="blue">
                    <span class="theme-swatch" style="background:#0a1628;"></span>
                    蓝色
                  </button>
                  <button class="theme-option" data-theme="vscode">
                    <span class="theme-swatch" style="background:#1e1e1e;"></span>
                    VS Code
                  </button>
                  <button class="theme-option" data-theme="github">
                    <span class="theme-swatch" style="background:#0d1117;"></span>
                    GitHub
                  </button>
                </div>
              </div>
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
          <label>
            CLI Session ID (--session-id)
            <input id="cliSessionId" placeholder="留空自动生成，或指定 UUID" />
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
    const cliSessionInput = document.getElementById("cliSessionId");
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
    const CLI_SESSION_KEY = "free-code-web-chat-cli-session-ids";
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

    function createSession(title = "新对话", cwd = "", cliSessionId = "") {
      const id = makeSessionId();
      const session = {
        id,
        title,
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
        messages: [],
        cwd: cwd || "",
        cliSessionId: cliSessionId || ""
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

    async function switchToSession(id) {
      currentSessionId = id;
      localStorage.setItem(CURRENT_KEY, id);
      const session = getCurrentSession();
      if (session) {
        sessionInput.value = id;
        cliSessionInput.value = session.cliSessionId || "";
        updateCwdDisplay(session.cwd);
        renderSessionList();
        renderMessages();
        setStatus("已切换到：" + (session.title || id.slice(0, 16)));
        await ensureSession(id);
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

    function escapeHtml(text) {
      return text
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;");
    }

    function renderInline(text) {
      const codes = [];
      text = text.replace(/`([^`]+)`/g, (match, code) => {
        codes.push(escapeHtml(code));
        return "\x00" + (codes.length - 1) + "\x00";
      });
      text = text.replace(/\\*\\*([^*]+)\\*\\*/g, "<strong>$1</strong>");
      text = text.replace(/__([^_]+)__/g, "<strong>$1</strong>");
      text = text.replace(/\\*([^*]+)\\*/g, "<em>$1</em>");
      text = text.replace(/_([^_]+)_/g, "<em>$1</em>");
      text = text.replace(/\\[([^\\]]+)\\]\\(([^)]+)\\)/g, '<a href="$2" target="_blank" rel="noopener">$1</a>');
      text = text.replace(/\x00(\\d+)\x00/g, (match, idx) => `<code>${codes[parseInt(idx)]}</code>`);
      return text;
    }

    function renderMarkdown(text) {
      if (!text) return "";
      const lines = text.split("\n");
      let html = "";
      let inCodeBlock = false;
      let codeBlockLang = "";
      let codeBlockContent = [];
      let inList = false;
      let listType = "";

      for (let i = 0; i < lines.length; i++) {
        let line = lines[i];
        const codeBlockMatch = line.match(/^```(\\w*)\\s*$/);
        if (codeBlockMatch) {
          if (!inCodeBlock) {
            inCodeBlock = true;
            codeBlockLang = codeBlockMatch[1] || "";
            codeBlockContent = [];
            continue;
          } else {
            inCodeBlock = false;
            const langClass = codeBlockLang ? ` class="language-${escapeHtml(codeBlockLang)}"` : "";
            html += `<pre><code${langClass}>${escapeHtml(codeBlockContent.join("\n"))}</code></pre>\n`;
            codeBlockLang = "";
            continue;
          }
        }
        if (inCodeBlock) {
          codeBlockContent.push(line);
          continue;
        }
        if (!line.trim()) {
          if (inList) { html += `</${listType}>\n`; inList = false; listType = ""; }
          html += "<br>\n";
          continue;
        }
        if (/^---+\\s*$/.test(line) || /^\\*\\*\\*+\\s*$/.test(line)) {
          if (inList) { html += `</${listType}>\n`; inList = false; listType = ""; }
          html += "<hr>\n";
          continue;
        }
        if (line.startsWith("> ")) {
          if (inList) { html += `</${listType}>\n`; inList = false; listType = ""; }
          html += `<blockquote>${renderInline(line.slice(2))}</blockquote>\n`;
          continue;
        }
        const ulMatch = line.match(/^(\\s*)[-*]\\s+(.*)$/);
        if (ulMatch) {
          if (!inList || listType !== "ul") {
            if (inList) html += `</${listType}>\n`;
            html += "<ul>\n";
            inList = true; listType = "ul";
          }
          html += `<li>${renderInline(ulMatch[2])}</li>\n`;
          continue;
        }
        const olMatch = line.match(/^(\\s*)\\d+\\.\\s+(.*)$/);
        if (olMatch) {
          if (!inList || listType !== "ol") {
            if (inList) html += `</${listType}>\n`;
            html += "<ol>\n";
            inList = true; listType = "ol";
          }
          html += `<li>${renderInline(olMatch[2])}</li>\n`;
          continue;
        }
        const hMatch = line.match(/^(#{1,6})\\s+(.*)$/);
        if (hMatch) {
          if (inList) { html += `</${listType}>\n`; inList = false; listType = ""; }
          const level = hMatch[1].length;
          html += `<h${level}>${renderInline(hMatch[2])}</h${level}>\n`;
          continue;
        }
        if (inList) { html += `</${listType}>\n`; inList = false; listType = ""; }
        html += `<p>${renderInline(line)}</p>\n`;
      }
      if (inCodeBlock) {
        const langClass = codeBlockLang ? ` class="language-${escapeHtml(codeBlockLang)}"` : "";
        html += `<pre><code${langClass}>${escapeHtml(codeBlockContent.join("\n"))}</code></pre>\n`;
      }
      if (inList) { html += `</${listType}>\n`; }
      return html;
    }

    function addMessage(role, text) {
      const wrapper = document.createElement("div");
      wrapper.className = "message " + role;

      const roleEl = document.createElement("span");
      roleEl.className = "role";
      roleEl.textContent = role;

      const contentEl = document.createElement("div");
      contentEl.className = "content";
      if (text && role !== "user") {
        contentEl.innerHTML = renderMarkdown(text);
      } else {
        contentEl.textContent = text || "";
      }

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
      cleaned = cleaned.replace(/<｜DSML｜function_calls/g, "...");
      cleaned = cleaned.replace(/<｜DSML｜\\/function_calls>/g, "");
      cleaned = cleaned.replace(/<｜begin▁of▁sentence｜>/g, "");
      cleaned = cleaned.replace(/<｜end▁of▁sentence｜>/g, "");
      cleaned = cleaned.replace(/<｜EOT｜>/g, "");
      return cleaned;
    }

    let parseState = "normal";
    let parseBuffer = "";

    const THINK_START = ["<thinking>"];
    const THINK_END = ["</thinking>"];
    const TOOL_START = [
      "<｜tool▁calls▁begin｜>",
      "```tool_call"
    ];
    const TOOL_END = [
      "<｜tool▁calls▁end｜>",
      "```"
    ];

    function findEarliest(text, patterns) {
      let best = -1;
      let bestPat = null;
      for (const pat of patterns) {
        const i = text.indexOf(pat);
        if (i !== -1 && (best === -1 || i < best)) { best = i; bestPat = pat; }
      }
      return best === -1 ? null : { index: best, pattern: bestPat };
    }

    function feedParse(text) {
      const segments = [];
      let remaining = text;

      while (remaining.length > 0) {
        if (parseState === "thinking") {
          parseBuffer += remaining;
          remaining = "";
          const end = findEarliest(parseBuffer, THINK_END);
          if (end) {
            remaining = parseBuffer.slice(end.index + end.pattern.length);
            parseBuffer = "";
            parseState = "normal";
          }
          continue;
        }

        if (parseState === "tool_call") {
          parseBuffer += remaining;
          remaining = "";
          const end = findEarliest(parseBuffer, TOOL_END);
          if (end) {
            const content = parseBuffer.slice(0, end.index).trim();
            if (content) segments.push({ type: "tool_call", content });
            remaining = parseBuffer.slice(end.index + end.pattern.length);
            parseBuffer = "";
            parseState = "normal";
            continue;
          }
          const nextStart = findEarliest(parseBuffer, [...THINK_START, ...TOOL_START]);
          if (nextStart && nextStart.index > 0) {
            const content = parseBuffer.slice(0, nextStart.index).trim();
            if (content) segments.push({ type: "tool_call", content });
            remaining = parseBuffer.slice(nextStart.index);
            parseBuffer = "";
            parseState = "normal";
          }
          continue;
        }

        const thinkMatch = findEarliest(remaining, THINK_START);
        const toolMatch = findEarliest(remaining, TOOL_START);

        let earliestType = null;
        let earliestIdx = remaining.length;
        let earliestPat = null;

        if (thinkMatch && thinkMatch.index < earliestIdx) {
          earliestIdx = thinkMatch.index; earliestType = "thinking"; earliestPat = thinkMatch.pattern;
        }
        if (toolMatch && toolMatch.index < earliestIdx) {
          earliestIdx = toolMatch.index; earliestType = "tool_call"; earliestPat = toolMatch.pattern;
        }

        if (earliestType) {
          const before = remaining.slice(0, earliestIdx);
          if (before) segments.push({ type: "text", content: before });
          parseBuffer = remaining.slice(earliestIdx + earliestPat.length);
          parseState = earliestType;
          remaining = "";

          if (earliestType === "thinking") {
            const end = findEarliest(parseBuffer, THINK_END);
            if (end) {
              remaining = parseBuffer.slice(end.index + end.pattern.length);
              parseBuffer = "";
              parseState = "normal";
            }
          } else {
            const end = findEarliest(parseBuffer, TOOL_END);
            if (end) {
              const content = parseBuffer.slice(0, end.index).trim();
              if (content) segments.push({ type: "tool_call", content });
              remaining = parseBuffer.slice(end.index + end.pattern.length);
              parseBuffer = "";
              parseState = "normal";
            } else {
              const nextStart = findEarliest(parseBuffer, [...THINK_START, ...TOOL_START]);
              if (nextStart && nextStart.index > 0) {
                const content = parseBuffer.slice(0, nextStart.index).trim();
                if (content) segments.push({ type: "tool_call", content });
                remaining = parseBuffer.slice(nextStart.index);
                parseBuffer = "";
                parseState = "normal";
              }
            }
          }
        } else {
          if (remaining) segments.push({ type: "text", content: remaining });
          remaining = "";
        }
      }
      return segments;
    }

    function extractAssistantSegments(event) {
      let raw = "";
      if (event.type === "assistant_partial") {
        raw = typeof event.delta === "string" ? event.delta : "";
      } else {
        const message = event.message;
        if (!message || !Array.isArray(message.content)) return [];
        raw = message.content
          .filter((block) => block && block.type === "text" && typeof block.text === "string")
          .map((block) => block.text)
          .join("");
      }
      raw = cleanAssistantText(raw);
      return feedParse(raw);
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
      parseState = "normal";
      parseBuffer = "";
    }

    async function ensureSession(sessionId) {
      const session = getCurrentSession();
      const settingsPath = localStorage.getItem(SETTINGS_PATH_KEY) || "";
      const cwd = session?.cwd || "";
      const cliSessionId = session?.cliSessionId || "";
      const resp = await fetch("/sessions", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          session_id: sessionId,
          cli_session_id: cliSessionId || undefined,
          settings_path: settingsPath || undefined,
          cwd: cwd || undefined
        }),
      });
      if (resp.ok) {
        const data = await resp.json();
        if (data.cli_session_id && session) {
          session.cliSessionId = data.cli_session_id;
          cliSessionInput.value = data.cli_session_id;
          saveSessions();
        }
      }
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
            const segments = extractAssistantSegments(event);
            for (const seg of segments) {
              if (!activeAssistantBubble) {
                activeAssistantBubble = addMessage("assistant", "");
              }
              if (seg.type === "text") {
                activeAssistantBubble.appendChild(document.createTextNode(seg.content));
                fullText += seg.content;
              } else if (seg.type === "tool_call") {
                const tcEl = document.createElement("span");
                tcEl.className = "tool-call-block";
                tcEl.textContent = "tool_call: " + seg.content;
                activeAssistantBubble.appendChild(tcEl);
                fullText += "[tool_call: " + seg.content + "]";
              }
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
              if (activeAssistantBubble) {
                activeAssistantBubble.innerHTML = renderMarkdown(fullText);
              }
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

    cliSessionInput.addEventListener("change", () => {
      const session = getCurrentSession();
      if (session) {
        session.cliSessionId = cliSessionInput.value.trim();
        saveSessions();
        setStatus("CLI Session ID 已更新（新会话生效）");
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

    const THEME_KEY = "free-code-web-chat-theme";
    const THEMES = {
      dark: {
        "color-scheme": "dark",
        "--bg": "#0b1020",
        "--panel": "#121933",
        "--panel-2": "#1a2347",
        "--text": "#e8ecff",
        "--muted": "#9aa6d1",
        "--accent": "#5b8cff",
        "--border": "#2b376c",
        "--user": "#1f7a4d",
        "--assistant": "#243f8f",
        "--system": "#5b5f73",
        "--error": "#a13b53",
        "--hover": "#1e2a52",
        "--active": "#2a3a6e",
        "--body-bg": "linear-gradient(180deg, #0a0f1d 0%, #111831 100%)",
        "--chat-bg": "rgba(12, 17, 34, 0.85)",
        "--msg-border": "rgba(255, 255, 255, 0.08)",
        "--user-bg": "rgba(31, 122, 77, 0.25)",
        "--user-border": "rgba(31, 122, 77, 0.45)",
        "--assistant-bg": "rgba(36, 63, 143, 0.28)",
        "--assistant-border": "rgba(91, 140, 255, 0.4)",
        "--system-bg": "rgba(91, 95, 115, 0.25)",
        "--system-text": "#d6dbf5",
        "--error-bg": "rgba(161, 59, 83, 0.28)",
        "--error-border": "rgba(210, 95, 124, 0.4)",
        "--secondary-btn": "#33406f",
        "--tool-text": "#e8a0a0",
        "--tool-border": "rgba(232, 160, 160, 0.4)"
      },
      light: {
        "color-scheme": "light",
        "--bg": "#ffffff",
        "--panel": "#f6f8fa",
        "--panel-2": "#e8ecf0",
        "--text": "#1f2328",
        "--muted": "#656d76",
        "--accent": "#0969da",
        "--border": "#d0d7de",
        "--user": "#1a7f37",
        "--assistant": "#0969da",
        "--system": "#6e7781",
        "--error": "#cf222e",
        "--hover": "#e8ecf0",
        "--active": "#d0d7de",
        "--body-bg": "linear-gradient(180deg, #f6f8fa 0%, #ffffff 100%)",
        "--chat-bg": "rgba(255, 255, 255, 0.9)",
        "--msg-border": "rgba(0, 0, 0, 0.08)",
        "--user-bg": "rgba(26, 127, 55, 0.12)",
        "--user-border": "rgba(26, 127, 55, 0.3)",
        "--assistant-bg": "rgba(9, 105, 218, 0.1)",
        "--assistant-border": "rgba(9, 105, 218, 0.3)",
        "--system-bg": "rgba(110, 119, 129, 0.1)",
        "--system-text": "#1f2328",
        "--error-bg": "rgba(207, 34, 46, 0.1)",
        "--error-border": "rgba(207, 34, 46, 0.3)",
        "--secondary-btn": "#d0d7de",
        "--tool-text": "#cf222e",
        "--tool-border": "rgba(207, 34, 46, 0.3)"
      },
      blue: {
        "color-scheme": "dark",
        "--bg": "#0a1628",
        "--panel": "#0f1f3c",
        "--panel-2": "#162d54",
        "--text": "#c9e1ff",
        "--muted": "#7ba1d4",
        "--accent": "#3b9eff",
        "--border": "#1e3a5f",
        "--user": "#0e8a5e",
        "--assistant": "#1a5cb0",
        "--system": "#4a5568",
        "--error": "#c53030",
        "--hover": "#162d54",
        "--active": "#1e3a5f",
        "--body-bg": "linear-gradient(180deg, #071020 0%, #0f1f3c 100%)",
        "--chat-bg": "rgba(10, 22, 40, 0.9)",
        "--msg-border": "rgba(59, 158, 255, 0.1)",
        "--user-bg": "rgba(14, 138, 94, 0.2)",
        "--user-border": "rgba(14, 138, 94, 0.4)",
        "--assistant-bg": "rgba(26, 92, 176, 0.25)",
        "--assistant-border": "rgba(59, 158, 255, 0.35)",
        "--system-bg": "rgba(74, 85, 104, 0.2)",
        "--system-text": "#c9e1ff",
        "--error-bg": "rgba(197, 48, 48, 0.2)",
        "--error-border": "rgba(197, 48, 48, 0.4)",
        "--secondary-btn": "#1e3a5f",
        "--tool-text": "#f0a0a0",
        "--tool-border": "rgba(240, 160, 160, 0.3)"
      },
      vscode: {
        "color-scheme": "dark",
        "--bg": "#1e1e1e",
        "--panel": "#252526",
        "--panel-2": "#2d2d2d",
        "--text": "#cccccc",
        "--muted": "#858585",
        "--accent": "#0078d4",
        "--border": "#3c3c3c",
        "--user": "#388a34",
        "--assistant": "#264f78",
        "--system": "#6a9955",
        "--error": "#f44747",
        "--hover": "#2a2d2e",
        "--active": "#37373d",
        "--body-bg": "linear-gradient(180deg, #1e1e1e 0%, #252526 100%)",
        "--chat-bg": "rgba(30, 30, 30, 0.9)",
        "--msg-border": "rgba(255, 255, 255, 0.06)",
        "--user-bg": "rgba(56, 138, 52, 0.18)",
        "--user-border": "rgba(56, 138, 52, 0.35)",
        "--assistant-bg": "rgba(38, 79, 120, 0.22)",
        "--assistant-border": "rgba(0, 120, 212, 0.35)",
        "--system-bg": "rgba(106, 153, 85, 0.15)",
        "--system-text": "#cccccc",
        "--error-bg": "rgba(244, 71, 71, 0.18)",
        "--error-border": "rgba(244, 71, 71, 0.35)",
        "--secondary-btn": "#3c3c3c",
        "--tool-text": "#ce9178",
        "--tool-border": "rgba(206, 145, 120, 0.3)"
      },
      github: {
        "color-scheme": "dark",
        "--bg": "#0d1117",
        "--panel": "#161b22",
        "--panel-2": "#21262d",
        "--text": "#e6edf3",
        "--muted": "#8b949e",
        "--accent": "#58a6ff",
        "--border": "#30363d",
        "--user": "#238636",
        "--assistant": "#1f6feb",
        "--system": "#8b949e",
        "--error": "#f85149",
        "--hover": "#21262d",
        "--active": "#30363d",
        "--body-bg": "linear-gradient(180deg, #0d1117 0%, #161b22 100%)",
        "--chat-bg": "rgba(13, 17, 23, 0.9)",
        "--msg-border": "rgba(255, 255, 255, 0.06)",
        "--user-bg": "rgba(35, 134, 54, 0.15)",
        "--user-border": "rgba(35, 134, 54, 0.35)",
        "--assistant-bg": "rgba(31, 111, 235, 0.15)",
        "--assistant-border": "rgba(88, 166, 255, 0.35)",
        "--system-bg": "rgba(139, 148, 158, 0.1)",
        "--system-text": "#e6edf3",
        "--error-bg": "rgba(248, 81, 73, 0.15)",
        "--error-border": "rgba(248, 81, 73, 0.35)",
        "--secondary-btn": "#30363d",
        "--tool-text": "#f85149",
        "--tool-border": "rgba(248, 81, 73, 0.3)"
      }
    };

    function applyTheme(name) {
      const theme = THEMES[name];
      if (!theme) return;
      const root = document.documentElement;
      root.style.colorScheme = theme["color-scheme"];
      for (const [key, value] of Object.entries(theme)) {
        if (key.startsWith("--")) root.style.setProperty(key, value);
      }
      document.body.style.background = theme["--body-bg"];
      const chatEl = document.getElementById("chat");
      if (chatEl) chatEl.style.background = theme["--chat-bg"];
      document.querySelectorAll(".theme-option").forEach(opt => {
        opt.classList.toggle("active", opt.dataset.theme === name);
      });
    }

    function initTheme() {
      const saved = localStorage.getItem(THEME_KEY) || "dark";
      applyTheme(saved);
    }

    const themeBtn = document.getElementById("themeBtn");
    const themeDropdown = document.getElementById("themeDropdown");

    themeBtn.addEventListener("click", (e) => {
      e.stopPropagation();
      themeDropdown.classList.toggle("active");
    });

    document.addEventListener("click", (e) => {
      if (!themeDropdown.contains(e.target) && e.target !== themeBtn) {
        themeDropdown.classList.remove("active");
      }
    });

    themeDropdown.addEventListener("click", (e) => {
      const option = e.target.closest(".theme-option");
      if (!option) return;
      const name = option.dataset.theme;
      localStorage.setItem(THEME_KEY, name);
      applyTheme(name);
      themeDropdown.classList.remove("active");
    });

    initTheme();

    async function init() {
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
      await switchToSession(currentSessionId);
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
