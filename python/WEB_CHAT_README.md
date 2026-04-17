# 简单网页对话程序

这里提供了一个最小网页程序，打开浏览器后就可以直接和 `free-code` 对话。

相关文件：

- [web_chat_app.py](file:///Users/surfing/tools/free-code/python/web_chat_app.py)
- [run_web_chat.py](file:///Users/surfing/tools/free-code/python/run_web_chat.py)

## 启动方式

先确保已经构建 CLI：

```bash
cd /Users/surfing/tools/free-code
bun run build
```

再启动网页程序：

```bash
python3 python/run_web_chat.py \
  --cli /Users/surfing/tools/free-code/cli \
  --cwd /Users/surfing/tools/free-code \
  --cli-arg=--dangerously-skip-permissions
```

默认地址：

```text
http://127.0.0.1:18001
```

## 页面功能

- 输入消息并发送
- 通过流式接口实时显示 assistant 回复
- 浏览器本地保存 `session_id`
- 支持手动切换会话
- 支持新会话和清空页面消息

## 适用场景

- 本地快速联调
- 给网页侧先看交互效果
- 验证 Python bridge 和网页链路

## 注意

- 这个页面是最小演示版，不是正式生产 UI
- 默认建议只用于本地或内网环境
- 正式上线时建议把前端页面并入你自己的网页项目中
