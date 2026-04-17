# Python 对接说明

这里提供了一套基于 `stream-json` 的 Python 封装，用来把网页后端直接接到 CLI。

如果你要看“网页应用如何接入”的完整说明，请直接看：

- [WEB_APP_INTEGRATION.md](file:///Users/surfing/tools/free-code/python/WEB_APP_INTEGRATION.md)

## 文件说明

- `free_code_cli_client.py`
  - 底层进程封装
  - 负责启动 `free-code`/`cli`
  - 通过 stdin 发送 NDJSON
  - 通过 stdout 持续接收 NDJSON 事件

- `web_bridge.py`
  - 面向 Web 会话的封装
  - 一个 `session_id` 对应一个 CLI 子进程
  - 适合 Flask/FastAPI/Django 这类后端

- `test_cli_client.py`
  - 最小联调脚本
  - 用来验证 Python 和 CLI 的通信链路是否正常

- `api_server.py`
  - 可选的 FastAPI 封装
  - 暴露 HTTP 接口，方便网页后端直接接入

- `run_api_server.py`
  - 启动 API 服务

- `test_api_server.py`
  - HTTP 测试脚本
  - 用来验证 API 服务能否正常调用 CLI

## CLI 运行模式

Python 封装使用的是 CLI 现有协议，不是自定义私有接口：

```bash
./cli \
  --print \
  --verbose \
  --input-format stream-json \
  --output-format stream-json
```

注意：

- `stream-json` 模式下必须带 `--verbose`
- 输入输出都是一行一个 JSON
- 一轮结束以 `type="result"` 作为完成标记

## 先构建 CLI

如果仓库根目录还没有 `./cli`，先执行：

```bash
bun run build
```

## 测试脚本

最小验证：

```bash
python3 python/test_cli_client.py \
  --cli ./cli \
  --cwd /Users/surfing/tools/free-code \
  --message "请只回复 Python bridge OK" \
  --cli-arg=--dangerously-skip-permissions
```

如果需要自动放行工具权限：

```bash
python3 python/test_cli_client.py \
  --cli ./cli \
  --auto-approve-tools \
  --cli-arg=--dangerously-skip-permissions
```

## Web 后端接法

### 1. 创建一个全局 bridge

```python
from python.web_bridge import FreeCodeWebBridge

bridge = FreeCodeWebBridge(
    cli_path="/Users/surfing/tools/free-code/cli",
    cwd="/Users/surfing/tools/free-code",
    extra_args=["--dangerously-skip-permissions"],
)
```

### 2. 为网页会话创建 CLI 会话

```python
session = bridge.create_session("web-user-001")
print(session.session_id)
```

### 3. 用户发消息

```python
events = bridge.ask(
    "web-user-001",
    "请帮我总结当前项目",
    timeout=180,
)
```

### 4. 处理返回事件

`events` 中通常会看到这些类型：

- `system`
  - 初始化信息、状态信息
- `assistant`
  - 助手正式消息
- `stream_event`
  - 更细粒度的流式事件
- `control_request`
  - 权限请求，例如 `can_use_tool`
- `control_response`
  - 对控制请求的响应
- `result`
  - 本轮结束标记

网页通常可以这样做：

- `assistant` 实时追加到前端消息流
- `control_request` 转成网页确认弹窗
- `result` 作为一次回答结束信号

## FastAPI 风格示例

```python
from fastapi import FastAPI
from python.web_bridge import FreeCodeWebBridge

app = FastAPI()

bridge = FreeCodeWebBridge(
    cli_path="/Users/surfing/tools/free-code/cli",
    cwd="/Users/surfing/tools/free-code",
    extra_args=["--dangerously-skip-permissions"],
)

@app.post("/chat/{session_id}")
def chat(session_id: str, payload: dict):
    events = bridge.ask(session_id, payload["message"], timeout=180)
    return {"session_id": session_id, "events": events}
```

如果你的前端要流式输出，可以把 `on_event` 回调接到 SSE 或 WebSocket 推送。

## 直接启动 HTTP API

如果你希望先用一个独立的 Python 服务把 CLI 包起来，再让网页调用这个服务，可以直接使用这里的 FastAPI 封装。

先安装依赖：

```bash
pip install fastapi uvicorn
```

启动服务：

```bash
python3 python/run_api_server.py \
  --cli /Users/surfing/tools/free-code/cli \
  --cwd /Users/surfing/tools/free-code \
  --cli-arg=--dangerously-skip-permissions
```

默认监听：

```text
http://127.0.0.1:8000
```

### 提供的接口

- `GET /health`
  - 健康检查

- `POST /sessions`
  - 创建一个 CLI 会话
  - 这里的 `session_id` 可以是你的业务 ID；封装层会自动映射到内部 CLI UUID
  - body 示例：

```json
{
  "session_id": "web-user-001"
}
```

- `POST /chat/{session_id}`
  - 同步请求，直到收到 `result`
  - body 示例：

```json
{
  "message": "请帮我总结当前项目",
  "timeout": 180
}
```

- `POST /chat/{session_id}/stream`
  - SSE 流式输出
  - 每条 `data:` 都是一条 CLI 事件 JSON

- `DELETE /sessions/{session_id}`
  - 关闭 CLI 会话

## HTTP 测试脚本

服务启动后，可以直接这样测试：

```bash
python3 python/test_api_server.py \
  --base-url http://127.0.0.1:8000 \
  --session-id web-test-session \
  --message "请只回复 API bridge OK"
```

## 权限处理

如果你不想加 `--dangerously-skip-permissions`，可以启用自动权限处理：

```python
def auto_permission_handler(event: dict):
    request = event.get("request", {})
    if request.get("subtype") == "can_use_tool":
        return {
            "behavior": "allow",
            "updatedInput": request.get("input", {}),
        }
    return None
```

然后：

```python
bridge = FreeCodeWebBridge(
    cli_path="/Users/surfing/tools/free-code/cli",
    cwd="/Users/surfing/tools/free-code",
    auto_permission_handler=auto_permission_handler,
)
```

## 建议

- 网页后端自己维护 `session_id -> CLI 子进程`
- 每个用户会话复用同一个 CLI 进程，保留上下文
- 生产环境不要默认开启 `--dangerously-skip-permissions`
- 如果前端要更好的流式体验，优先用 WebSocket 或 SSE
