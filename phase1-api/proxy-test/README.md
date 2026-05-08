# Proxy 测试 — 纯小白版

> 理解"请求在到达模型之前经过了什么"

---

## 0. 什么是 Proxy（代理）

你已经知道两种使用模型的方式：

```
方式 1（云 API）：  你的电脑 → 互联网 → DeepSeek 服务器 → 模型
方式 2（本地模型）： 你的电脑 → Ollama → 本地模型
```

还有一种**方式 3（Proxy）**：

```
方式 3（代理）：    你的电脑 → 本地 Proxy → 互联网 → DeepSeek 服务器 → 模型
```

Proxy 坐你电脑上，它不跑模型——它只是把请求**转发**给上游，然后把回答**转发**回来。就像快递中转站：不生产包裹，只负责转运。

**为什么需要 Proxy？** 几个常见原因：
- 统一管理 API Key（所有人用 Proxy，不用各自配 Key）
- 模型名改写（把 `my-model` 映射到 `deepseek-chat`）
- 加日志、限流、审计
- 请求/响应改写（截断长上下文、过滤敏感词）

> 这个目录下的脚本用来验证：Proxy 是不是正常工作。Ollama 不需要 Proxy——Ollama 自己就是推理服务。

---

## 1. 启动 Proxy

首先确保你要测试的 Proxy 已经在本机跑起来了。以 `cursor-deepseek-v4-proxy` 为例：

```powershell
# 去 GitHub 克隆项目，按它的 README 配置并启动
# 通常监听在 http://localhost:3000
```

验证 Proxy 活着：

```powershell
curl.exe http://localhost:3000
# 有响应就说明它在跑
```

---

## 2. 测试普通请求（非流式）

```powershell
cd phase1-api/proxy-test

# 先设环境变量（告诉测试脚本 Proxy 在哪）
$env:PROXY_BASE_URL = "http://localhost:3000/v1"
$env:PROXY_API_KEY = "test-key"
$env:PROXY_MODEL = "deepseek-chat"

# 跑测试
python test_chat.py
```

**你会看到：**
1. 完整的 HTTP 响应 JSON（所有字段一览无余）
2. 最下面一行是模型的实际回答

**如果成功：** 说明 Proxy 的 `/v1/chat/completions` 接口正常工作——接收了你的请求，转发给了上游模型，拿到了回答，原样返回给了你。

---

## 3. 测试流式请求

```powershell
python test_stream.py
```

**你会看到：**
- 回答一个字一个字出现（这就是流式——SSE 协议）
- 最后输出 `first_token_ms` 和 `total_ms`

**如果卡住不动：** Proxy 可能在 SSE 透传上有问题——比如没有正确转发 `data:` 行，或者提前关闭了连接。

---

## 4. 请求到底经过了什么

```
test_chat.py / test_stream.py
  │
  │  POST http://localhost:3000/v1/chat/completions
  │  请求体：{"model": "deepseek-chat", "messages": [...], "stream": true}
  │
  ▼
本地 Proxy (localhost:3000)
  │
  │  1. 验证调用方的 API Key（你设的 PROXY_API_KEY）
  │  2. 可能改写 model 名称
  │  3. 把请求转发给上游
  │
  │  POST https://api.deepseek.com/v1/chat/completions
  │  请求头：Authorization: Bearer <上游的真实 API Key>
  │
  ▼
DeepSeek 云服务器
  │
  │  模型推理 → 生成回答
  │
  ▼
返回 SSE 流（或 JSON）
  │
  │  Proxy 透传给客户端
  │
  ▼
test_chat.py / test_stream.py 收到回答
```

---

## 5. 接入你的 CLI 客户端

Proxy 测试通过后，把它加到你的客户端配置里：

```toml
# config.toml
api_key = "$PROXY_API_KEY"            # Proxy 要求的 key（不是上游的 key！）
base_url = "http://localhost:3000/v1"
model = "deepseek-chat"               # 或者 Proxy 支持的任意模型名
```

```powershell
cd ../cli-chat
python main.py --config config.toml
```

现在你有三种后端可以随时切换了：

| Provider | base_url | 做什么 |
|----------|----------|--------|
| DeepSeek 云 | `https://api.deepseek.com` | 直接调云 API |
| Ollama 本地 | `http://localhost:11434/v1` | 本地推理 |
| Proxy | `http://localhost:3000/v1` | 中转代理 |

---

## 6. 常见问题

| 现象 | 可能原因 | 试试 |
|------|---------|------|
| `Connection refused` | Proxy 没启动 | 确认 Proxy 在跑，端口号没错 |
| `HTTP 401` | Proxy 的 API Key 不对 | 检查 `$env:PROXY_API_KEY` 是否正确 |
| `HTTP 502` | Proxy 连不上上游 | 检查上游 API 的 Key 和 URL 在 Proxy 那边配好没有 |
| 流式测试卡住不输出 | SSE 透传有问题 | 用 `test_chat.py` 先确认非流式正常，再排查流式 |
| 回答内容和直接调 DeepSeek 不一样 | Proxy 改了 system prompt 或参数 | 正常——Proxy 可能在中间层修改了请求 |
| 流式输出中间断了一截 | SSE 跨 TCP 分包时丢数据 | `test_stream.py` 的 `iter_sse_lines()` 用 `readlines()` 已解决了这个问题 |

---

## 附录：后端工程师的工程视角（可选）

如果你有后端经验，可以把 Proxy 理解成一个**反向代理 / API 网关**：

| Proxy 的职责 | 后端类比 |
|-------------|---------|
| 路由 `/v1/chat/completions` → 上游 | Nginx `proxy_pass` |
| 鉴权（调用方 Key vs 上游 Key） | API Gateway 的认证层 |
| 模型名改写 | 请求重写（rewrite） |
| SSE 流式透传 | `proxy_buffering off` + chunked response |
| 错误透传（上游 401/429/5xx） | `proxy_pass` 的 error_page 传递 |
| 超时与重试 | 连接池超时 + retry policy |
| 日志 | access log 记录每次请求的入口、上游、耗时 |

> 和 Ollama 的定位完全不同：Ollama = 数据库（真正干活），Proxy = 反向代理（只转发）。
