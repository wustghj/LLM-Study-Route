# Windows 下 Ollama + Open WebUI 部署 — 纯小白版

> 目标：在你自己的电脑上跑一个不需要联网的 AI 模型

---

## 0. 你在做什么

目前为止你用的是 DeepSeek 云 API——你的问题通过网络飞到 DeepSeek 的服务器，他们的 GPU 算完，结果飞回来。

这次不一样。你要在自己的电脑上跑一个模型，**数据不出你的电脑，不需要网络，不按 token 付费**。

跑通之后的架构长这样：

```
你的浏览器/终端
    │
    ├─→ Open WebUI（漂亮的聊天界面）    ← 可选，有它更舒服
    │     └─→ http://localhost:3000
    │
    └─→ 你的 CLI 客户端（main.py）       ← 你已经会用了
          │
          └─→ Ollama（本地推理服务）
                └─→ http://localhost:11434
                      │
                      └─→ 加载模型文件 → GPU/CPU 计算 → 生成回答
```

**关键认知：** Ollama 不是模型本身。Ollama 是一个"模型管理器"——它帮你下载模型、加载模型、提供 HTTP API。真正的计算在更底层（llama.cpp 推理引擎）。

---

## 1. 硬件检查

先搞清楚你的电脑能不能跑本地模型：

| 你的配置 | 能跑什么 | 体验 |
|---------|---------|------|
| 16GB 内存 + NVIDIA 6GB+ 显存 | 7B 量化模型 | 流畅，秒级响应 |
| 16GB 内存 + 无独显 | 7B 量化模型（CPU 推理） | 能用，但慢（几秒一个字） |
| 8GB 内存 + 无独显 | 1.5B-3B 小模型 | 勉强，建议换更大的机器或用云 API |

> 怎么看显存？任务管理器 → 性能 → GPU → "专用 GPU 内存"
> 怎么看内存？任务管理器 → 性能 → 内存 → 右上角的数字

---

## 2. 安装 Ollama

1. 打开 [ollama.com/download/windows](https://ollama.com/download/windows)，下载 Windows 安装包
2. 双击安装，一路下一步
3. 装完后打开 PowerShell，验证：

```powershell
ollama --version
# 输出版本号就说明装好了。如果提示"找不到命令"，重启 PowerShell 再试。
```

> Ollama 安装后会在后台自动启动一个服务（任务栏右下角有 Ollama 图标）。这个服务一直在跑，等着接收请求。

---

## 3. 下载并运行你的第一个本地模型

```powershell
# 下载模型（约 4.5 GB，等几分钟）
ollama pull qwen2.5:7b

# 运行模型（直接对话）
ollama run qwen2.5:7b
```

看到 `>>> ` 提示符就可以直接聊天了。输入 `/bye` 退出。

**下载太慢？** 国内网络访问 Ollama 的模型仓库可能很慢。试试：
- 换个时间段（深夜/早上）
- 或者先下载更小的模型：`ollama pull qwen2.5:1.5b`（只有约 1GB）

**常用命令：**

| 命令 | 做什么 |
|------|--------|
| `ollama list` | 看我下载了哪些模型 |
| `ollama ps` | 看当前有哪些模型在运行 |
| `ollama show qwen2.5:7b` | 看模型的详细信息（大小、参数等） |
| `ollama rm qwen2.5:7b` | 删除一个模型（释放磁盘空间） |

---

## 4. 验证：Ollama 提供了 HTTP API

Ollama 在后台默默监听着 `http://localhost:11434`。你可以用浏览器或命令行验证：

**方法 1：浏览器验证（最简单）**

打开浏览器，访问：
```
http://localhost:11434
```
看到 `Ollama is running` 就说明服务正常。

**方法 2：用 curl 测试（看原始数据）**

```powershell
# 非流式请求——一次返回完整结果
curl.exe -X POST http://localhost:11434/api/chat `
  -H "Content-Type: application/json" `
  -d '{"model": "qwen2.5:7b", "messages": [{"role": "user", "content": "你好，用一句话介绍你自己"}], "stream": false}'
```

如果返回了一段 JSON，里面有 `"message":{"content":"你好！我是..."}`，恭喜——你已经成功调用了本地模型的 HTTP API。

**Ollama 提供了两套 API：**

| API 路径 | 风格 | 谁能用 |
|---------|------|--------|
| `http://localhost:11434/api/chat` | Ollama 原生格式 | 只有专门为 Ollama 写的客户端能用 |
| `http://localhost:11434/v1/chat/completions` | OpenAI-Compatible 格式 | 你的 CLI 客户端（main.py）就能直接用！ |

---

## 5. 把你的 CLI 客户端接上 Ollama

修改 `phase1-api/cli-chat/config.toml`（只需要改 3 行）：

```toml
api_key = "ollama"                          # Ollama 不需要真的 API Key
base_url = "http://localhost:11434/v1"      # 指向本地 Ollama
model = "qwen2.5:7b"                        # 你下载的模型名
```

然后运行：

```powershell
cd phase1-api/cli-chat
python main.py --config config.toml
```

输入问题，观察 `first_token_ms` 和 `total_ms`。你会注意到：

- **首 token 延迟**比云 API 长很多（本地 GPU 不如云端的 A100/H100 快）
- **token/s** 可能只有云 API 的 1/10 甚至更低
- 但好处是：**免费、隐私、没有网络也能用**

---

## 6.（可选）安装 Open WebUI——给 Ollama 加个漂亮的界面

如果你觉得命令行聊天太硬核，可以装 Open WebUI——一个类似 ChatGPT 的网页界面，底层调用你的本地 Ollama。

**前提：** 装了 Docker Desktop（去 [docker.com](https://docker.com) 下载安装）

```powershell
docker run -d `
  --name open-webui `
  -p 3000:8080 `
  -e OLLAMA_BASE_URL=http://host.docker.internal:11434 `
  -v open-webui:/app/backend/data `
  --restart always `
  ghcr.io/open-webui/open-webui:main
```

然后浏览器打开 `http://localhost:3000`，注册一个本地账号（数据全在你电脑上），选择模型 `qwen2.5:7b`，开始聊天。

> **不用 Docker 也能装**，但依赖更复杂。第一阶段用 Docker 最省心。

---

## 7. 各组件到底是什么关系

新手最容易搞混的就是"谁是模型本身"。记住这个：

```
┌─────────────────────────────────────────────────────────┐
│                                                         │
│  Open WebUI          ← 就是个网页界面，不负责推理         │
│  http://localhost:3000                                   │
│       │                                                 │
│       ▼                                                 │
│  Ollama               ← 模型管理器+HTTP服务，不负责推理    │
│  http://localhost:11434                                  │
│       │                                                 │
│       ▼                                                 │
│  llama.cpp            ← 真正的推理引擎（C++写的）         │
│  (Ollama 内置)         负责加载模型、矩阵计算、生成 token   │
│       │                                                 │
│       ▼                                                 │
│  模型文件(.gguf)       ← 训练好的权重数据，不能自己运行     │
│       │                                                 │
│       ▼                                                 │
│  GPU / CPU             ← 实际干活的硬件                   │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

**一句话版：**
- Open WebUI = 界面
- Ollama = 服务管家
- llama.cpp = 真正干活的引擎
- 模型文件 = 菜谱（不是厨师）
- GPU/CPU = 灶台

---

## 8. 常见问题排查

| 现象 | 可能原因 | 试试这个 |
|------|---------|---------|
| `ollama: command not found` | 没装或没加到 PATH | 重装 Ollama，或重启 PowerShell |
| `connection refused` (连不上 11434) | Ollama 服务没启动 | 从开始菜单启动 Ollama，或运行 `ollama serve` |
| 下载模型卡住不动 | 国内网络慢 | 换时间段，或换更小的模型 `qwen2.5:1.5b` |
| 第一个回答等了很久 | 模型冷启动，首次加载到内存 | 正常，第二次就快了（模型已在内存中） |
| 回答一个字一个字往外蹦 | CPU 推理（没 GPU 加速） | 正常现象。检查 `ollama ps` 看是不是用的 CPU |
| 聊了几轮后越来越慢 | 上下文变长，KV Cache 膨胀 | 输入 `/bye` 重新开始，或减少上下文长度 |
| 内存/显存满了 | 模型太大 | 换更小的模型，或用更低的量化版本 |
| Open WebUI 连不上 Ollama | Docker 访问宿主机地址不对 | 确保环境变量是 `host.docker.internal`（不是 localhost） |
| `Invoke-RestMethod` 报错 | PowerShell 版本太老 | 改用 `curl.exe`（Windows 10 自带） |
| 输出质量不稳定/答非所问 | temperature 太高 | 在 config.toml 里把 temperature 降到 0.3-0.5 |

---

## 9. 云 API vs 本地模型——选哪个？

| 场景 | 用云 API | 用本地 Ollama |
|------|---------|-------------|
| 图快、图省心 | ✅ 首 token 几百毫秒 | ❌ 可能要等几秒 |
| 处理敏感数据 | ❌ 数据发给供应商 | ✅ 数据不出电脑 |
| 没网的时候用 | ❌ 必须有网 | ✅ 断网也能用 |
| 高频大量调用 | ❌ 按 token 付费 | ✅ 电费忽略不计 |
| 想要最强模型 | ✅ 顶级模型随便用 | ❌ 受限于硬件 |

> 实际项目里通常是"混着用"——敏感数据走本地，普通任务走云 API。

---

## 附录：后端工程师的观察视角（可选）

如果你有后端经验，可以从这些角度理解 Ollama：

| 概念 | 后端类比 |
|------|---------|
| Ollama 服务启动 | 服务进程启动 + 加载大索引文件到内存 |
| 冷启动（首次推理慢） | 类似第一次查询需要把索引 load 进 page cache |
| 首 token 延迟 | 请求进入后第一次可写响应的时间 |
| token/s | 吞吐指标，类似 QPS 但衡量的是 token 生成速率 |
| KV Cache 随对话增长 | 请求上下文缓存，占用随上下文线性增长 |
| 流式输出（SSE） | Chunked Transfer Encoding / Server-Sent Events |
| 量化模型 | 用精度换空间——float32 → int8 压缩，类似有损压缩 |
