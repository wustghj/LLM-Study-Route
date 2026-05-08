# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A hands-on LLM learning project designed for pure beginners (and backend engineers). The core philosophy: **run first, understand later**. Every phase has working code, every interaction outputs measurable metrics (first_token_ms, total_ms). The same OpenAI-Compatible client connects to cloud APIs, local Ollama, and a local proxy — switch by changing config only.

## Project Structure

```
G:\AI学习路径\
│
├── README.md                           # Project entry point
├── LLM学习路径_完整版.md                 # Complete 6-phase learning roadmap
├── CLAUDE.md                           # This file
├── .gitignore
│
└── api调用实战/
    │
    ├── cli-chat/                       # Phase 1 core: API client
    │   ├── main.py                     #   SDK version (start here)
    │   ├── raw_client.py               #   Raw HTTP version (learn the protocol)
    │   ├── benchmark.py                #   Multi-provider perf comparison → CSV
    │   ├── config.toml / config.example.toml
    │   ├── requirements.txt
    │   └── conversations/
    │
    ├── proxy-test/                     # Phase 1: Proxy verification
    │   ├── test_chat.py                #   Single POST
    │   ├── test_stream.py              #   SSE streaming
    │   └── README.md
    │
    ├── ollama-notes/                   # Phase 1: Local deployment notes
    │   ├── windows-setup.md
    │   └── model-benchmark.md
    │
    ├── llama-cpp-notes/                # Phase 2: Inference engine notes
    │   ├── getting-started.md          #   Build/run/connect CLI
    │   ├── kv-cache-deep-dive.md       #   KV Cache deep dive
    │   └── experiments.md              #   6 controlled experiments
    │
    ├── rag-demo/                       # Phase 3: RAG
    │   ├── rag.py                      #   Complete RAG implementation
    │   ├── README.md
    │   └── requirements.txt
    │
    ├── agent-demo/                     # Phase 3: Agent
    │   ├── agent.py                    #   Function Calling agent
    │   ├── README.md
    │   └── requirements.txt
    │
    ├── finetune-demo/                  # Phase 4: Fine-tuning
    │   ├── prepare_data.py             #   Generate training data
    │   ├── train.py                    #   QLoRA training script
    │   ├── inference.py                #   Before/after comparison
    │   ├── README.md
    │   └── requirements.txt
    │
    ├── production-demo/                # Phase 5: Production
    │   ├── logger.py                   #   Structured JSON logging
    │   ├── cost.py                     #   Multi-provider cost tracker
    │   ├── loadtest.py                 #   Concurrent load testing
    │   ├── gateway.py                  #   Minimal LLM API gateway
    │   ├── README.md
    │   └── requirements.txt
    │
    ├── advanced-notes/                 # Phase 6: Advanced
    │   ├── minimal_transformer.py      #   Numpy Transformer forward pass
    │   └── llama-cpp-source-guide.md   #   llama.cpp source reading guide
    │
    ├── 大模型自顶向下图解.md              # LLM architecture diagram
    └── 短视频文案-普通工程师学大模型.md
```

## Learning Path Overview

The complete learning roadmap is in `LLM学习路径_完整版.md` (7 layers, Pre-Phase → Phase 6):

| Layer | Focus | Status | Key Files |
|-------|-------|--------|-----------|
| Pre-Phase | 5-min quickstart — talk to an LLM | ✅ Ready | `cli-chat/main.py` |
| 0 | Foundation — what is LLM, terminology, full request chain | ✅ Ready | `大模型自顶向下图解.md` |
| 1 | Application — API client, local model, proxy, benchmarks | ✅ Complete | `cli-chat/`, `proxy-test/`, `ollama-notes/` |
| 2 | Inference — llama.cpp, KV Cache, experiments | ✅ Complete | `llama-cpp-notes/` (3 files) |
| 3 | Frameworks — RAG, Agent, Function Calling | ✅ Complete | `rag-demo/rag.py`, `agent-demo/agent.py` |
| 4 | Customization — Prompt Engineering, LoRA | ✅ Complete | `finetune-demo/` (3 files) |
| 5 | Production Engineering — logging, cost, load testing, gateway | ✅ Complete | `production-demo/` (4 files) |
| 6 | Advanced — Transformer, training, llama.cpp source | ✅ Planned | `advanced-notes/` (2 files) |

## Key Architecture

### CLI Chat Client (`cli-chat/main.py`)

Single-file client with these responsibilities:
- Config loading: TOML-based, supports `$ENV_VAR` interpolation for API keys
- Multi-turn conversation: System prompt + user/assistant history persisted as JSON
- Streaming: Uses OpenAI SDK `stream=True`, prints tokens as they arrive, reports `first_token_ms` and `total_ms`
- Typed error handling: Distinguishes auth failure, rate limit, timeout, and connection errors with actionable messages
- Provider switching: Change `base_url`, `api_key`, `model` in config.toml to target DeepSeek, OpenAI, Ollama, or a local proxy — no code changes needed

Supporting files:
- `raw_client.py` — Same features, but uses raw `urllib` (no OpenAI SDK). Teaches the HTTP/SSE protocol layer
- `benchmark.py` — Automated multi-provider performance comparison, outputs CSV

Provider flow:
```
CLI Chat → DeepSeek/OpenAI Cloud API
CLI Chat → Ollama (OpenAI-Compatible API, localhost:11434)
CLI Chat → cursor-deepseek-v4-proxy (OpenAI-Compatible API, localhost:3000)
```

### Proxy Tests (`proxy-test/`)

Two minimal stdlib-only scripts (no external dependencies):
- `test_chat.py` — Single POST, prints full JSON response
- `test_stream.py` — SSE stream with `iter_sse_lines()` helper, measures first-token latency

### RAG Demo (`rag-demo/rag.py`)

Retrieval-Augmented Generation system:
- Documents → chunks → vectorize (sentence-transformers) → similarity search
- For each query: retrieves relevant chunks → feeds into LLM with context
- `--compare` mode shows the difference with/without RAG

### Agent Demo (`agent-demo/agent.py`)

Function Calling agent with think-act-observe loop:
- LLM decides: answer directly or call a tool
- Tools: calculator, current time, directory listing
- Demonstrates: JSON Schema tool definitions, tool execution, result feedback loop

### Fine-tuning Demo (`finetune-demo/`)

Three-stage QLoRA pipeline:
- `prepare_data.py` — generates 200 conversation records
- `train.py` — QLoRA (4-bit) fine-tuning via transformers + peft, ~4GB VRAM for 1.5B model
- `inference.py` — side-by-side base vs fine-tuned comparison

## Running

```powershell
# CLI Chat (SDK version)
$env:DEEPSEEK_API_KEY = "sk-..."
cd api调用实战/cli-chat
python main.py --config config.toml

# Raw HTTP version (see the protocol)
python raw_client.py --config config.toml

# Benchmark (compare all providers)
python benchmark.py --prompt medium --runs 3

# Proxy tests (stdlib only, no deps)
cd api调用实战/proxy-test
$env:PROXY_BASE_URL = "http://localhost:3000/v1"
$env:PROXY_API_KEY = "test-key"
python test_chat.py
python test_stream.py

# Ollama (local model)
ollama pull qwen2.5:7b
# Set config.toml: base_url=http://localhost:11434/v1, model=qwen2.5:7b, api_key=ollama

# RAG demo
cd api调用实战/rag-demo
pip install sentence-transformers numpy openai tomli
python rag.py --query "什么是 KV Cache？" --compare

# Agent demo
cd api调用实战/agent-demo
python agent.py

# Fine-tuning
cd api调用实战/finetune-demo
python prepare_data.py
python train.py --model-name Qwen/Qwen2.5-1.5B-Instruct
python inference.py
```

## Design Principles

- Provider-agnostic: `base_url`, `api_key`, `model` are config-only
- Minimal dependencies: proxy tests use stdlib only; CLI client only needs `openai` and `tomli`
- Measurable learning: `first_token_ms` and `total_ms` printed on every response
- Progressive complexity: Phase 0 needs only a browser; Phase 2 needs a C++ compiler
