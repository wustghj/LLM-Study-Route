# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A hands-on LLM learning project for beginners. Core philosophy: **run first, understand later**. Every phase has working code, every interaction outputs measurable metrics (first_token_ms, total_ms). The same OpenAI-Compatible client connects to cloud APIs, local Ollama, and a local proxy — switch by changing config only.

## Project Structure

```
├── README.md                    # Entry point
├── START-HERE.md                # 30-min narrative guide for absolute beginners
├── LEARNING-PATH.md             # Complete 6-phase curriculum
├── FAQ.md                       # 20 most common beginner questions
├── CLAUDE.md                    # This file
├── .gitignore
│
├── concepts/                    # Concept deep-dives
│   ├── llm-architecture.md      #   Full LLM architecture diagram
│   ├── tokenization.md          #   Why Chinese costs more tokens than English
│   ├── embedding.md             #   How words become vectors
│   └── training.md              #   3-stage training: pretrain -> SFT -> RLHF
│
├── guides/                      # Practical guides
│   └── prompt-engineering.md    #   10 prompt techniques with before/after
│
├── phase1-api/                  # Phase 1: API & local deployment
│   ├── cli-chat/                #   Chat client (SDK + raw HTTP)
│   ├── proxy-test/              #   Proxy verification scripts
│   └── ollama/                  #   Local model deployment notes
│
├── phase2-inference/            # Phase 2: Inference engine
│   └── llama-cpp/               #   Build, KV Cache, experiments
│
├── phase3-frameworks/           # Phase 3: Application frameworks
│   ├── rag/                     #   RAG system
│   └── agent/                   #   Function Calling agent
│
├── phase4-finetuning/           # Phase 4: Model customization
│   └── finetune/                #   QLoRA training pipeline
│
├── phase5-production/           # Phase 5: Production engineering
│   ├── logger.py                #   Structured JSON logging
│   ├── cost.py                  #   Multi-provider cost tracker
│   ├── loadtest.py              #   Concurrent load testing
│   ├── gateway.py               #   Minimal LLM API gateway
│   ├── README.md
│   └── requirements.txt
│
└── phase6-advanced/             # Phase 6: Advanced study
    ├── transformer.py           #   Pure numpy Transformer forward pass
    └── llama-cpp-guide.md       #   llama.cpp C++ source reading guide
```

## Learning Path Overview

The complete learning roadmap is in `LEARNING-PATH.md` (7 layers, Pre-Phase -> Phase 6):

| Layer | Focus | Status | Key Files |
|-------|-------|--------|-----------|
| Pre-Phase | 5-min quickstart | Ready | `phase1-api/cli-chat/main.py` |
| 0 | Foundation — what is LLM, terminology | Ready | `concepts/llm-architecture.md` |
| 1 | Application — API, local model, proxy, benchmarks | Complete | `phase1-api/` |
| 2 | Inference — llama.cpp, KV Cache, experiments | Complete | `phase2-inference/llama-cpp/` |
| 3 | Frameworks — RAG, Agent, Function Calling | Complete | `phase3-frameworks/` |
| 4 | Customization — Prompt Engineering, LoRA | Complete | `phase4-finetuning/finetune/` |
| 5 | Production — logging, cost, load testing, gateway | Complete | `phase5-production/` |
| 6 | Advanced — Transformer, training, llama.cpp source | Planned | `phase6-advanced/` |

## Key Architecture

### CLI Chat Client (`phase1-api/cli-chat/main.py`)

Single-file client: TOML config with `$ENV_VAR` interpolation, multi-turn conversation with JSON persistence, OpenAI SDK streaming with `first_token_ms` and `total_ms` metrics, typed error handling (auth/rate-limit/timeout/connection).

Supporting files:
- `raw_client.py` — Same features using raw `urllib` (no OpenAI SDK)
- `benchmark.py` — Multi-provider performance comparison -> CSV

### RAG Demo (`phase3-frameworks/rag/rag.py`)

Documents -> chunks -> vectorize (sentence-transformers) -> similarity search -> feed context to LLM. `--compare` mode shows with/without RAG.

### Agent Demo (`phase3-frameworks/agent/agent.py`)

Function Calling agent: LLM decides answer or tool call -> execute tool -> feedback loop. Tools: calculator, current time, directory listing.

### Fine-tuning Demo (`phase4-finetuning/finetune/`)

Three-stage QLoRA pipeline: `prepare_data.py` (200 records) -> `train.py` (4-bit, ~4GB VRAM) -> `inference.py` (before/after comparison).

## Running

```powershell
# Phase 1 — CLI Chat
$env:DEEPSEEK_API_KEY = "sk-..."
cd phase1-api/cli-chat
python main.py --config config.toml
python raw_client.py --config config.toml
python benchmark.py --prompt medium --runs 3

# Phase 1 — Proxy tests (stdlib only)
cd phase1-api/proxy-test
$env:PROXY_BASE_URL = "http://localhost:3000/v1"
$env:PROXY_API_KEY = "test-key"
python test_chat.py
python test_stream.py

# Phase 3 — RAG
cd phase3-frameworks/rag
pip install sentence-transformers numpy openai tomli
python rag.py --query "what is KV Cache?" --compare

# Phase 3 — Agent
cd phase3-frameworks/agent
python agent.py

# Phase 4 — Fine-tuning
cd phase4-finetuning/finetune
python prepare_data.py
python train.py --model-name Qwen/Qwen2.5-1.5B-Instruct
python inference.py

# Phase 5 — Production tools
cd phase5-production
python logger.py    # stdlib only
python cost.py      # stdlib only
# loadtest.py needs: pip install aiohttp
# gateway.py needs: pip install fastapi uvicorn aiohttp

# Phase 6 — Advanced
cd phase6-advanced
python transformer.py   # needs: pip install numpy
```

## Design Principles

- **Provider-agnostic**: `base_url`, `api_key`, `model` are config-only
- **Minimal dependencies**: proxy tests use stdlib only; CLI client only needs `openai` and `tomli`
- **Measurable learning**: `first_token_ms` and `total_ms` printed on every response
- **Progressive complexity**: Phase 0 needs only a browser; Phase 2 needs a C++ compiler
