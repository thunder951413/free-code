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
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: ui-sans-serif, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      background: linear-gradient(180deg, #0a0f1d 0%, #111831 100%);
      color: var(--text);
    }
    .page {
      max-width: 980px;
      margin: 0 auto;
      padding: 24px 16px 40px;
    }
    .header {
      margin-bottom: 16px;
    }
    .header h1 {
      margin: 0 0 8px;
      font-size: 28px;
    }
    .header p {
      margin: 0;
      color: var(--muted);
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
    .chat {
      background: rgba(12, 17, 34, 0.85);
      border: 1px solid var(--border);
      border-radius: 16px;
      min-height: 420px;
      max-height: 60vh;
      overflow: auto;
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
    }
    .composer textarea {
      flex: 1;
      min-height: 110px;
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
    }
    .status {
      margin-top: 12px;
      color: var(--muted);
      font-size: 14px;
    }
    @media (max-width: 720px) {
      .composer { flex-direction: column; }
      .composer button { width: 100%; }
    }
  </style>
</head>
<body>
  <div class="page">
    <div class="header">
      <h1>free-code Web Chat</h1>
      <p>一个最小可用的网页对话界面，后端通过 Python bridge 驱动 free-code CLI。</p>
    </div>

    <div class="toolbar">
      <label>
        Session ID
        <input id="sessionId" />
      </label>
      <button id="newSessionBtn" class="secondary" type="button">新会话</button>
      <button id="clearBtn" class="secondary" type="button">清空消息</button>
    </div>

    <div id="chat" class="chat"></div>

    <form id="chatForm" class="composer">
      <textarea id="messageInput" placeholder="输入你想对 free-code 说的话，例如：请帮我概览当前项目结构"></textarea>
      <button id="sendBtn" type="submit">发送</button>
    </form>

    <div id="status" class="status">就绪</div>
    <div class="footer">默认使用流式接口 `/chat/{session_id}/stream`。</div>
  </div>

  <script>
    const chatEl = document.getElementById("chat");
    const statusEl = document.getElementById("status");
    const formEl = document.getElementById("chatForm");
    const inputEl = document.getElementById("messageInput");
    const sendBtn = document.getElementById("sendBtn");
    const sessionInput = document.getElementById("sessionId");
    const newSessionBtn = document.getElementById("newSessionBtn");
    const clearBtn = document.getElementById("clearBtn");

    const STORAGE_KEY = "free-code-web-chat-session-id";
    let activeAssistantBubble = null;
    let sending = false;

    function makeSessionId() {
      return "web-" + (crypto.randomUUID ? crypto.randomUUID() : String(Date.now()));
    }

    function getSessionId() {
      let value = localStorage.getItem(STORAGE_KEY);
      if (!value) {
        value = makeSessionId();
        localStorage.setItem(STORAGE_KEY, value);
      }
      sessionInput.value = value;
      return value;
    }

    function setSessionId(value) {
      localStorage.setItem(STORAGE_KEY, value);
      sessionInput.value = value;
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

    function extractAssistantText(event) {
      if (event.type === "assistant_partial") {
        return typeof event.delta === "string" ? event.delta : "";
      }
      const message = event.message;
      if (!message || !Array.isArray(message.content)) return "";
      return message.content
        .filter((block) => block && block.type === "text" && typeof block.text === "string")
        .map((block) => block.text)
        .join("");
    }

    function setSending(next) {
      sending = next;
      sendBtn.disabled = next;
      inputEl.disabled = next;
      sessionInput.disabled = next;
      newSessionBtn.disabled = next;
    }

    function resetAssistantBubble() {
      activeAssistantBubble = null;
    }

    async function ensureSession(sessionId) {
      await fetch("/sessions", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ session_id: sessionId }),
      });
    }

    async function sendMessage(message) {
      const sessionId = sessionInput.value.trim() || getSessionId();
      setSessionId(sessionId);
      await ensureSession(sessionId);

      addMessage("user", message);
      setSending(true);
      setStatus("发送中...");
      resetAssistantBubble();

      const response = await fetch("/chat/" + encodeURIComponent(sessionId) + "/stream", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message, timeout: 180 }),
      });

      if (!response.ok || !response.body) {
        throw new Error(await response.text() || "请求失败");
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder("utf-8");
      let buffer = "";

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
              scrollToBottom();
            }
            continue;
          }

          if (event.type === "system" && event.subtype === "init") {
            setStatus("已连接，模型：" + (event.model || "unknown"));
            continue;
          }

          if (event.type === "result") {
            setStatus("本轮完成");
            continue;
          }

          if (event.type === "error") {
            addMessage("error", event.error || "未知错误");
            setStatus("发生错误");
            continue;
          }
        }
      }
    }

    formEl.addEventListener("submit", async (event) => {
      event.preventDefault();
      if (sending) return;
      const message = inputEl.value.trim();
      if (!message) return;

      inputEl.value = "";
      try {
        await sendMessage(message);
      } catch (error) {
        addMessage("error", error instanceof Error ? error.message : String(error));
        setStatus("请求失败");
      } finally {
        setSending(false);
        resetAssistantBubble();
        inputEl.focus();
      }
    });

    newSessionBtn.addEventListener("click", () => {
      const next = makeSessionId();
      setSessionId(next);
      addMessage("system", "已创建新会话：" + next);
      setStatus("已切换到新会话");
    });

    clearBtn.addEventListener("click", () => {
      chatEl.innerHTML = "";
      setStatus("已清空页面消息");
    });

    sessionInput.addEventListener("change", () => {
      const value = sessionInput.value.trim();
      if (value) {
        setSessionId(value);
        setStatus("已更新会话 ID");
      }
    });

    getSessionId();
    addMessage("system", "页面已就绪，输入消息后即可与 free-code 对话。");
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
