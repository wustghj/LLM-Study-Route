# LLM 学习项目 — 从零开始掌握大模型

> 一份为纯小白设计的 AI 大模型实战学习路径
> 不啃论文，不背公式——先跑起来，再理解原理

## 5 分钟快速开始

```powershell
# 1. 设置 API Key（去 platform.deepseek.com 免费注册获取）
$env:DEEPSEEK_API_KEY = "sk-你的key"

# 2. 安装依赖
cd api调用实战/cli-chat
pip install openai tomli

# 3. 开始你的第一次 AI 对话
python main.py --config config.example.toml
```

输入一个问题，看屏幕上逐字出现回答，完成你的第一次 LLM API 调用。

## 这个项目是什么

这是一个**动手实践导向**的 LLM（大语言模型）学习项目。它的核心思路是：

```
先跑通 → 建立体感 → 测量数据 → 理解原理 → 深入优化
```

每个阶段都有可运行的代码，每个操作都有可测量的指标（首 token 延迟、总耗时、token/s）。

## 学习路径（7 层，从零到进阶）

| 阶段 | 内容 | 适合谁 | 状态 |
|------|------|--------|------|
| **Pre-Phase** | 5 分钟快速体验 | 还没用过 API 的人 | ✅ |
| **Phase 0** | LLM 是什么、能做什么、不能做什么 | 零基础 | ✅ |
| **Phase 1** | API 调用 → 本地模型 → Proxy → Benchmark | 会用终端 | ✅ 已完成 |
| **Phase 2** | llama.cpp → KV Cache → 对照实验 | 想看黑盒内部 | ✅ 已完成 |
| **Phase 3** | RAG 检索增强 → Agent 智能体 | 想构建应用 | ✅ 已完成 |
| **Phase 4** | Prompt 工程 → LoRA 微调 | 想让模型听话 | ✅ 已完成 |
| **Phase 5** | 日志 / 成本 / 压测 / 网关 | 想上线服务 | ✅ 已完成 |
| **Phase 6** | Transformer → 训练 → 多模态 | 想深入原理 | 🔭 远期 |

**完整路线图：** 打开 `LLM学习路径_完整版.md`

## 项目结构

```
api调用实战/
│
├── cli-chat/                         # Phase 1 核心：API 调用客户端
│   ├── main.py                       #   SDK 版（推荐新手用这个）
│   ├── raw_client.py                 #   纯 HTTP 版（看协议细节）
│   ├── benchmark.py                  #   多 provider 性能对比 → CSV
│   ├── config.toml / config.example.toml
│   └── conversations/                #   对话存档
│
├── proxy-test/                       # Phase 1：代理测试脚本
│   ├── test_chat.py / test_stream.py
│
├── ollama-notes/                     # Phase 1：本地模型部署笔记
│
├── llama-cpp-notes/                  # Phase 2：推理引擎笔记
│   ├── getting-started.md
│   ├── kv-cache-deep-dive.md
│   └── experiments.md
│
├── rag-demo/                         # Phase 3：RAG 系统
│   └── rag.py                        #   可运行，含对比模式
│
├── agent-demo/                       # Phase 3：Agent 系统
│   └── agent.py                      #   可运行，含工具调用
│
├── finetune-demo/                    # Phase 4：微调流水线
│   ├── prepare_data.py               #   生成训练数据
│   ├── train.py                      #   QLoRA 训练
│   └── inference.py                  #   微调前后对比
│
├── production-demo/                  # Phase 5：生产化工具
│   ├── logger.py                     #   结构化 JSON 日志
│   ├── cost.py                       #   成本计算器
│   ├── loadtest.py                   #   并发负载测试
│   ├── gateway.py                    #   最小 API 网关
│   └── README.md
│
├── LLM学习路径_完整版.md              #   完整学习路线图（从这里开始）
└── README.md                         #   你正在看的文件
```

## 核心理念

1. **先动手，再动脑** — 先跑通，建立体感，再补原理
2. **同一个客户端，多个后端** — 一个客户端连接 DeepSeek / Ollama / Proxy，只改配置
3. **可测量的学习** — 每次回答都输出 `first_token_ms` 和 `total_ms`
4. **渐进式复杂度** — Phase 0 只需要浏览器和记事本，Phase 2 才需要编译 C++

## 如何学习这个项目

```
1. 打开 LLM学习路径_完整版.md，找到你当前的阶段
2. 按顺序往下走，完成每个阶段的"验收标准"
3. 遇到术语忘记 → 翻到附录 A 术语速查表
4. 出问题了 → 翻到附录 B 常见问题排查
5. 搞懂了再进入下一阶段
```
