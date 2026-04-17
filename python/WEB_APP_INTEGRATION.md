# 网页应用对接文档

这份文档说明你的网页应用如何与当前仓库里的 CLI 能力对接。

目标不是让网页直接调用命令行，而是：

- 网页前端
- Python Web 后端
- Python bridge
- 本地 `free-code` CLI

组成一条稳定的服务链路。

---

## 1. 总体架构

推荐的调用关系如下：

```text
Browser / Web Frontend
        |
        v
Python Web Backend
        |
        v
FreeCodeWebBridge / FastAPI API Server
        |
        v
free-code CLI (--print --input-format stream-json --output-format stream-json)
```

也就是：

1. 网页前端不要直接启动 CLI
2. 网页前端只调用你自己的 Python Web 服务
3. Python Web 服务通过本仓库提供的 Python bridge 与 CLI 通信
4. CLI 再去完成模型调用、工具调用、上下文管理

---

## 2. 仓库里已经提供的能力

当前已经提供这些文件：

- [free_code_cli_client.py](file:///Users/surfing/tools/free-code/python/free_code_cli_client.py)
  - 底层 CLI 子进程封装
  - 负责 stdin/stdout 的 NDJSON 协议通信

- [web_bridge.py](file:///Users/surfing/tools/free-code/python/web_bridge.py)
  - 面向 Web 会话的封装
  - 一个网页会话对应一个 CLI 子进程

- [api_server.py](file:///Users/surfing/tools/free-code/python/api_server.py)
  - 可直接跑起来的 FastAPI 服务

- [run_api_server.py](file:///Users/surfing/tools/free-code/python/run_api_server.py)
  - 用于启动 HTTP API 服务

- [test_cli_client.py](file:///Users/surfing/tools/free-code/python/test_cli_client.py)
  - 测试 Python 直连 CLI

- [test_api_server.py](file:///Users/surfing/tools/free-code/python/test_api_server.py)
  - 测试网页后端 HTTP API

---

## 3. 你这边需要做什么

你网页应用侧只需要做两件事：

1. 在 Python Web 后端里接入本仓库提供的 bridge
2. 前端通过 HTTP 或 SSE 调用这个后端

换句话说，网页应用不需要了解 CLI 的底层 `stream-json` 协议。

---

## 4. 推荐接入方式

推荐分两层：

### 方案 A：直接在你的 Python Web 项目里 import

适合你已经有自己的 Flask / FastAPI / Django 项目。

你在自己的后端代码里直接引用：

```python
from python.web_bridge import FreeCodeWebBridge
```

然后自己定义接口。

优点：

- 和你现有项目融合最好
- 鉴权、日志、数据库、用户体系都能复用
- 更适合正式项目

### 方案 B：把这里的 API server 独立跑起来

适合先快速联调。

直接启动：

```bash
python3 python/run_api_server.py \
  --cli /Users/surfing/tools/free-code/cli \
  --cwd /Users/surfing/tools/free-code \
  --cli-arg=--dangerously-skip-permissions
```

然后你的网页应用调用：

```text
http://127.0.0.1:8000
```

优点：

- 接入最快
- 便于前后端先打通链路

缺点：

- 生产环境里你通常还是会希望把它并入自己的 Python Web 服务

---

## 5. 后端接法

### 5.1 最小接法

如果你的后端本身就是 Python，推荐直接这样封装：

```python
from python.web_bridge import FreeCodeWebBridge

bridge = FreeCodeWebBridge(
    cli_path="/Users/surfing/tools/free-code/cli",
    cwd="/Users/surfing/tools/free-code",
    extra_args=["--dangerously-skip-permissions"],
)

def chat(session_id: str, message: str):
    events = bridge.ask(
        session_id=session_id,
        text=message,
        timeout=180,
    )
    return events
```

这里的关键点：

- `session_id` 用网页业务自己的会话 ID 即可
- bridge 内部会自动映射成 CLI 需要的 UUID
- 同一个 `session_id` 会复用同一个 CLI 子进程，从而保留上下文

### 5.2 FastAPI 示例

下面是一份建议写法：

```python
from fastapi import FastAPI, HTTPException
from python.web_bridge import FreeCodeWebBridge

app = FastAPI()

bridge = FreeCodeWebBridge(
    cli_path="/Users/surfing/tools/free-code/cli",
    cwd="/Users/surfing/tools/free-code",
    extra_args=["--dangerously-skip-permissions"],
)

@app.post("/chat/{session_id}")
def chat(session_id: str, payload: dict):
    message = payload.get("message", "").strip()
    if not message:
        raise HTTPException(status_code=400, detail="message is empty")

    events = bridge.ask(
        session_id=session_id,
        text=message,
        timeout=180,
    )

    return {
        "session_id": session_id,
        "events": events,
    }
```

### 5.3 如果你想要流式输出

网页聊天通常更适合流式返回。

当前已经在 [api_server.py](file:///Users/surfing/tools/free-code/python/api_server.py) 里提供了一个 SSE 版本接口：

- `POST /chat/{session_id}/stream`

它会持续返回：

```text
data: {json event}

data: {json event}
```

直到收到 CLI 的 `result` 事件为止。

---

## 6. 前端接法

前端分两种常见方式。

### 6.1 同步请求

适合先快速打通。

```javascript
async function sendMessage(sessionId, message) {
  const resp = await fetch(`/chat/${sessionId}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message, timeout: 180 }),
  });

  if (!resp.ok) {
    throw new Error(await resp.text());
  }

  return await resp.json();
}
```

返回内容里会有：

- `events`
- `result`
- `assistant_text`，如果你走的是内置 API server

### 6.2 流式请求

如果你要网页端边生成边显示，建议走 SSE。

示例思路：

```javascript
async function streamMessage(sessionId, message) {
  const resp = await fetch(`/chat/${sessionId}/stream`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message, timeout: 180 }),
  });

  const reader = resp.body.getReader();
  const decoder = new TextDecoder("utf-8");
  let buffer = "";

  while (true) {
    const { value, done } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const parts = buffer.split("\n\n");
    buffer = parts.pop() || "";

    for (const chunk of parts) {
      if (!chunk.startsWith("data: ")) continue;
      const event = JSON.parse(chunk.slice(6));
      console.log("event", event);

      if (event.type === "assistant") {
        // 更新聊天消息
      }

      if (event.type === "result") {
        // 一轮结束
      }
    }
  }
}
```

---

## 7. 会话管理怎么做

这是网页接入里最重要的部分。

建议规则：

1. 一个网页聊天会话，对应一个业务 `session_id`
2. Python 后端用这个 `session_id` 去调用 `bridge.ask()`
3. bridge 内部会为这个业务会话维持一个 CLI 进程
4. 用户下一轮消息继续使用同一个 `session_id`
5. 当用户关闭会话或超时后，调用 `close_session(session_id)`

推荐你在后端维护：

```text
user_id + conversation_id -> session_id
```

或者直接：

```text
conversation_id -> session_id
```

这样可以保证上下文连续。

---

## 8. 网页后端与 CLI 的职责边界

建议按下面分工：

### 网页前端负责

- 展示聊天 UI
- 输入框与发送按钮
- 流式渲染文本
- 展示工具执行中的状态
- 展示错误提示

### Python Web 后端负责

- 用户鉴权
- 会话管理
- 接入 `FreeCodeWebBridge`
- 把 CLI 事件转换成前端可消费的格式
- 控制会话生命周期

### CLI 负责

- 大模型调用
- 工具调用
- 上下文和历史会话
- 本地文件/代码能力
- 结果汇总

---

## 9. 事件协议怎么理解

网页应用一般只需要关心这些事件类型：

### `system`

常见用途：

- 初始化
- 状态变更
- 任务通知

### `assistant`

正式助手消息。

前端通常应该把它渲染为一条完整 assistant 回复。

### `stream_event`

更细粒度的过程事件。

如果你的前端只需要普通聊天体验，可以先不强依赖这个类型。

### `control_request`

这是 CLI 向网页后端发起的控制请求。

最常见的是：

- `can_use_tool`

也就是“是否允许执行某个工具”。

### `control_response`

后端对 `control_request` 的响应。

### `result`

一轮对话结束标志。

网页前端通常应该把它当作“本轮回答完成”。

---

## 10. 权限怎么处理

你现在有两种模式。

### 模式 A：开发联调阶段

最简单：

```bash
--dangerously-skip-permissions
```

优点：

- 联调最快

缺点：

- 不适合正式环境

### 模式 B：网页来决定权限

推荐正式环境这样做：

1. CLI 发出 `control_request`
2. Python 后端收到后转成网页弹窗或审批逻辑
3. 用户点允许/拒绝
4. 后端再回 `control_response`

如果你未来要做“网页确认执行命令、网页确认改文件”，就是走这条路径。

---

## 11. 当前这边需要如何做

如果你问的是“这个仓库这边还需要怎么配”，当前最少需要这些步骤：

### 第一步：构建 CLI

```bash
cd /Users/surfing/tools/free-code
bun run build
```

产物：

```text
/Users/surfing/tools/free-code/cli
```

### 第二步：准备 Python 环境

如果你只用 bridge，不跑 FastAPI，可以只用 Python 标准库。

如果你要跑 HTTP 服务：

```bash
pip install fastapi uvicorn
```

### 第三步：先用测试脚本确认链路

CLI 直连测试：

```bash
python3 python/test_cli_client.py \
  --cli ./cli \
  --cwd /Users/surfing/tools/free-code \
  --message "请只回复 Python bridge OK" \
  --cli-arg=--dangerously-skip-permissions
```

HTTP API 测试：

先启动服务：

```bash
python3 python/run_api_server.py \
  --cli ./cli \
  --cwd /Users/surfing/tools/free-code \
  --cli-arg=--dangerously-skip-permissions
```

再执行：

```bash
python3 python/test_api_server.py \
  --base-url http://127.0.0.1:8000 \
  --session-id web-test-session \
  --message "请只回复 API bridge OK"
```

---

## 12. 推荐上线方式

如果是正式网页项目，建议按下面做：

1. 保留 `FreeCodeWebBridge` 作为后端内部能力
2. 不直接暴露底层 CLI 事件给浏览器，先做一层后端协议转换
3. 对 `session_id` 做你自己的业务映射
4. 增加会话超时回收机制
5. 对权限请求做网页确认
6. 记录 CLI stderr 和关键事件日志

建议再补这些能力：

- 会话过期回收
- 多用户隔离
- 失败重试
- 统一错误码
- SSE/WS 心跳
- 权限审批 UI

---

## 13. 推荐的落地顺序

建议你按这个顺序推进：

1. 先跑通 `test_cli_client.py`
2. 再跑通 `run_api_server.py` + `test_api_server.py`
3. 网页前端先接同步 `/chat/{session_id}`
4. 再升级为流式 `/chat/{session_id}/stream`
5. 最后再补权限确认和生产级会话管理

---

## 14. 一句话总结

你网页应用的正确接法不是“网页直接调用 CLI”，而是：

```text
网页前端 -> Python Web 后端 -> Python bridge -> free-code CLI
```

这边仓库已经把 bridge、API server、测试脚本都补好了，你网页应用只需要接后端接口即可。
