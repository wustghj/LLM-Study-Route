# LLM 从零到精通 — 动手实战学习路径

> 零基础、不啃论文、不背公式。先跑起来，再理解原理。
> 30 分钟建立完整认知 → 6 个 Phase 逐步深入 → 成为 LLM 工程专家。

---

## 快速开始

```powershell
# 0. 确保装了 Python 3.10+（python.org 下载，勾选 Add to PATH）
python --version

# 1. 获取 API Key（platform.deepseek.com 免费注册）
$env:DEEPSEEK_API_KEY = "sk-你的key"

# 2. 装依赖 + 跑第一次对话
cd phase1-api/cli-chat
pip install openai tomli
python main.py --config config.example.toml
```

输入问题，看屏幕上逐字出现回答。你刚完成了一次 LLM API 调用。

---

## 两条阅读路线

| 你想要 | 读这个 | 时间 |
|--------|--------|------|
| **先搞懂 LLM 到底是什么** | [`START-HERE.md`](START-HERE.md) | 30 分钟 |
| **直接开始系统学习** | [`LEARNING-PATH.md`](LEARNING-PATH.md) | 6 Phase 课程表 |
| **遇到困惑查一下** | [`FAQ.md`](FAQ.md) | 随时 |

---

## 项目结构

```
├── START-HERE.md          ← 纯小白入口：30 分钟搞懂 LLM
├── LEARNING-PATH.md       ← 完整 6 Phase 课程表
├── FAQ.md                 ← 20 个最常见问题
├── README.md              ← 你在这里
│
├── concepts/              ← 概念深度解析
│   ├── llm-architecture.md    LLM 架构全景图
│   ├── tokenization.md        Token 完全解释
│   ├── embedding.md           Embedding 完全解释
│   └── training.md            训练三阶段故事
│
├── guides/                ← 实用技巧
│   └── prompt-engineering.md  10 个 Prompt 技巧
│
├── phase1-api/            ← Phase 1：API 调用 + 本地部署
│   ├── cli-chat/              聊天客户端（SDK + 纯 HTTP）
│   ├── proxy-test/            代理测试
│   └── ollama/                本地模型部署
│
├── phase2-inference/      ← Phase 2：推理引擎
│   └── llama-cpp/             编译、KV Cache、6 个实验
│
├── phase3-frameworks/     ← Phase 3：应用框架
│   ├── rag/                   RAG 检索增强生成
│   └── agent/                 Agent 智能体
│
├── phase4-finetuning/     ← Phase 4：模型微调
│   └── finetune/              QLoRA 训练流水线
│
├── phase5-production/     ← Phase 5：生产化
│   ├── logger.py              结构化日志
│   ├── cost.py                成本计算器
│   ├── loadtest.py            并发压测
│   └── gateway.py             API 网关
│
└── phase6-advanced/       ← Phase 6：进阶深造
    ├── transformer.py         手写 Transformer
    └── llama-cpp-guide.md     C++ 推理引擎源码阅读
```

---

## 学习路线

```
START-HERE.md（30 分钟）
      ↓
Phase 1   →  Phase 2   →  Phase 3   →  Phase 4   →  Phase 5   →  Phase 6
调 API        推理引擎      RAG+Agent     LoRA 微调     生产化        进阶
1-2 周        2-4 周       2-4 周       2-4 周       2-3 周       长期
```

每个 Phase 都有可运行的代码、明确的验收标准和可测量的指标。
