# CLI Chat — 命令行 AI 聊天客户端

> 这个目录是本项目的核心。一个客户端，连接所有后端。

---

## 你在这里能学到什么

```
                    同一个客户端（main.py）
                    只改 config.toml，代码不动
                              │
        ┌─────────────────────┼─────────────────────┐
        ▼                     ▼                     ▼
  DeepSeek 云 API        Ollama 本地            本地 Proxy
  (最快最省心)           (免费，隐私)           (中转代理)
```

---

## 文件说明

| 文件 | 用途 | 适合谁 |
|------|------|--------|
| `main.py` | 日常聊天使用，用 OpenAI SDK | 新手从这里开始 |
| `raw_client.py` | 学习 HTTP 协议——手写请求、解析 SSE | 想看"SDK 背后是什么"的时候用 |
| `benchmark.py` | 自动测试多个 provider 的性能 → CSV | 想用数据对比的时候用 |
| `config.toml` | 你的配置文件（API Key、模型、参数） | 每次切换后端改这个就行 |
| `config.example.toml` | 配置模板（不含真实 Key，可以提交 git） | 给别人看、或自己重置配置时用 |
| `conversations/` | 聊天记录存档（JSON 格式） | 回头看之前聊了什么 |

---

## 快速开始

```powershell
# 1. 装依赖（只需要两个包）
cd phase1-api/cli-chat
pip install openai tomli

# 2. 设置 API Key
$env:DEEPSEEK_API_KEY = "sk-你的key"

# 3. 复制一份配置
Copy-Item config.example.toml config.toml

# 4. 开始聊天
python main.py --config config.toml
```

输入问题，看屏幕上逐字出现回答，最后一行显示 `[metrics] first_token_ms=xxx, total_ms=xxx`。

---

## 切换后端（只改配置！）

### 用 DeepSeek 云 API

```toml
api_key = "$DEEPSEEK_API_KEY"
base_url = "https://api.deepseek.com"
model = "deepseek-chat"
```

### 用 Ollama 本地模型

```toml
api_key = "ollama"
base_url = "http://localhost:11434/v1"
model = "qwen2.5:7b"
```

### 用本地 Proxy

```toml
api_key = "$PROXY_API_KEY"
base_url = "http://localhost:3000/v1"
model = "deepseek-chat"
```

---

## 聊天命令

在对话中输入这些命令（不是终端）：

| 输入 | 效果 |
|------|------|
| `/exit` | 保存对话并退出 |
| `/save` | 手动保存当前对话 |
| `/new` | 开始新对话（清空上下文） |

---

## 三个 Python 文件怎么选

| 如果你想 | 用这个 |
|---------|--------|
| 日常聊天 | `main.py` |
| 学习 HTTP 协议——看请求体和响应体的原始格式 | `raw_client.py` |
| 比较 DeepSeek vs Ollama vs Proxy 谁快 | `benchmark.py` |

`raw_client.py` 的功能和 `main.py` 一模一样——区别是它不用 OpenAI SDK，所有 HTTP 请求都是手写的。**对比着看这两个文件，你就能理解 SDK 到底帮你做了什么。**

---

## 常见问题

### "认证失败" / "API Key 无效"

```powershell
# 确认环境变量设了
$env:DEEPSEEK_API_KEY
# 如果输出为空，重新设置
$env:DEEPSEEK_API_KEY = "sk-你的key"
```

### "网络连接失败"

- DeepSeek API 在国内能直连，不用代理
- 如果用 Ollama/Proxy，确认它们正在运行：浏览器访问 `http://localhost:11434` 或 `http://localhost:3000`
- 检查 `config.toml` 里的 `base_url` 有没有打错

### "请求超时"

- 本地模型第一次加载比较慢（冷启动），等几秒就好
- DeepSeek 免费用户有每分钟请求次数限制，太频繁会被限流

### benchmark 没反应

- 确认 `config.toml` 里有一个有效的 provider 配置
- benchmark 会按 `config.toml` 当前的 base_url 跑测试

---

## 每次回答的指标怎么看

```
[metrics] first_token_ms=320, total_ms=4200
```

| 指标 | 什么意思 | 好的标准 |
|------|---------|---------|
| `first_token_ms` | 从发送请求到屏幕上出现第一个字的时间 | 云 API < 500ms 算快，本地 < 5000ms 算正常 |
| `total_ms` | 整个回答花的总时间 | 取决于回答长度，10-30 秒都正常 |

> 每次聊天都看这两个数字——慢慢地你就会对不同 provider 的延迟有直觉。
