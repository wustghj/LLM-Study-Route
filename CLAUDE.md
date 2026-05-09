# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A hands-on LLM learning project for beginners. Core philosophy: **run first, understand later**. Every phase has working code, every interaction outputs measurable metrics (first_token_ms, total_ms). The same OpenAI-Compatible client connects to cloud APIs, local Ollama, and a local proxy — switch by changing config only.

## Project Structure

```
├── README.md                    # Entry point
├── START-HERE.md                # (moved to docs/start-here.md)
├── LEARNING-PATH.md             # (moved to docs/learning-path.md)
├── FAQ.md                       # (moved to docs/faq.md)
├── CLAUDE.md                    # This file
├── .gitignore
│
├── docs/                        # All reading materials
│   ├── start-here.md            #   30-min narrative guide
│   ├── learning-path.md         #   7-phase curriculum
│   ├── faq.md                   #   20 most common questions
│   ├── concepts/                #   Concept deep-dives (4 files)
│   ├── guides/                  #   Prompt engineering handbook
│   └── appendix/                #   Glossary, troubleshooting, resources
│
├── phase0-fundamentals/         # Phase 0: Foundation (reading only)
├── phase1-api/                  # Phase 1: API mastery
│   ├── proxy-test/              #   Proxy verification scripts
│   ├── exercises/               #   Hands-on exercises
│   ├── main.py                  #   SDK-based chat client
│   ├── raw_client.py            #   Raw HTTP chat client
│   └── benchmark.py             #   Multi-provider performance benchmark
│
├── phase2-transformer/          # Phase 2: Transformer internals
│   ├── exercises/               #   Hands-on exercises
│   ├── transformer_annotated.py #   Teaching version (prints shapes)
│   ├── transformer.py           #   Clean version
│   └── attention_viz.py         #   Attention weight visualization
│
├── phase3-local-deploy/         # Phase 3: Local deployment
│   ├── experiments/             #   Automated experiment scripts
│   ├── exercises/               #   Hands-on exercises
│   ├── getting-started.md       #   llama.cpp build guide
│   ├── kv-cache.md              #   KV Cache deep-dive
│   └── experiments.md           #   6 experiments manual
│
├── phase4-apps/                 # Phase 4: Application frameworks
│   ├── rag/                     #   RAG system
│   └── agent/                   #   Function Calling agent
│
├── phase5-customize/            # Phase 5: Model customization
│   └── finetune/                #   QLoRA training pipeline
│
├── phase6-production/           # Phase 6: Production engineering
│   ├── logger.py                #   Structured JSON logging
│   ├── cost.py                  #   Multi-provider cost tracker
│   ├── loadtest.py              #   Concurrent load testing
│   └── gateway.py               #   Minimal LLM API gateway
│
├── phase7-source/               # Phase 7: Advanced — source reading
│   └── llama-cpp-guide.md       #   llama.cpp C++ source reading guide
│
├── projects/                    # Capstone projects
│   ├── 01-personal-knowledge-base/
│   └── 02-code-review-bot/
│
└── tools/                       # Utility scripts
    └── check_env.py             #   Environment checker
```

## Learning Path Overview

The complete learning roadmap is in `docs/learning-path.md` (9 layers, Pre-Phase -> Phase 7):

| Layer | Focus | Status | Key Files |
|-------|-------|--------|-----------|
| Pre-Phase | 5-min quickstart | Ready | `phase1-api/main.py` |
| 0 | Foundation — what is LLM, terminology | Ready | `docs/start-here.md` |
| 1 | Application — API, local model, proxy, benchmarks | Ready | `phase1-api/` |
| 2 | Transformer — numpy forward pass, Attention viz | Ready | `phase2-transformer/` |
| 3 | Local deploy — Ollama, llama.cpp, KV Cache, experiments | Ready | `phase3-local-deploy/` |
| 4 | Frameworks — RAG, Agent, Function Calling | Ready | `phase4-apps/` |
| 5 | Customization — Prompt Engineering, LoRA | Ready | `phase5-customize/finetune/` |
| 6 | Production — logging, cost, load testing, gateway | Ready | `phase6-production/` |
| 7 | Advanced — llama.cpp source reading | Ready | `phase7-source/` |

## Key Architecture

### CLI Chat Client (`phase1-api/main.py`)

Single-file client: TOML config with `$ENV_VAR` interpolation, multi-turn conversation with JSON persistence, OpenAI SDK streaming with `first_token_ms` and `total_ms` metrics, typed error handling (auth/rate-limit/timeout/connection).

Supporting files:
- `raw_client.py` — Same features using raw `urllib` (no OpenAI SDK)
- `benchmark.py` — Multi-provider performance comparison -> CSV

### RAG Demo (`phase4-apps/rag/rag.py`)

Documents -> chunks -> vectorize (sentence-transformers) -> similarity search -> feed context to LLM. `--compare` mode shows with/without RAG.

### Agent Demo (`phase4-apps/agent/agent.py`)

Function Calling agent: LLM decides answer or tool call -> execute tool -> feedback loop. Tools: calculator, current time, directory listing.

### Fine-tuning Demo (`phase5-customize/finetune/`)

Three-stage QLoRA pipeline: `prepare_data.py` (200 records) -> `train.py` (4-bit, ~4GB VRAM) -> `inference.py` (before/after comparison).

## Running

```powershell
# Phase 1 — CLI Chat
$env:DEEPSEEK_API_KEY = "sk-..."
cd phase1-api
python main.py --config config.example.toml
python raw_client.py --config config.example.toml
python benchmark.py --prompt medium --runs 3

# Phase 1 — Proxy tests (stdlib only)
cd phase1-api/proxy-test
$env:PROXY_BASE_URL = "http://localhost:3000/v1"
$env:PROXY_API_KEY = "test-key"
python test_chat.py
python test_stream.py

# Phase 2 — Transformer
cd phase2-transformer
pip install numpy
python transformer_annotated.py
python transformer.py
python attention_viz.py

# Phase 3 — Local deployment
ollama pull qwen2.5:7b
cd phase3-local-deploy
python kv_cache_viz.py

# Phase 4 — RAG
cd phase4-apps/rag
pip install sentence-transformers numpy openai tomli
python rag.py --query "what is KV Cache?" --compare

# Phase 4 — Agent
cd phase4-apps/agent
python agent.py

# Phase 5 — Fine-tuning
cd phase5-customize/finetune
python prepare_data.py
python train.py --model-name Qwen/Qwen2.5-1.5B-Instruct
python inference.py

# Phase 6 — Production tools
cd phase6-production
python logger.py    # stdlib only
python cost.py      # stdlib only
# loadtest.py needs: pip install aiohttp
# gateway.py needs: pip install fastapi uvicorn aiohttp

# Phase 7 — Source reading
# Read phase7-source/llama-cpp-guide.md
```

## Design Principles

- **Provider-agnostic**: `base_url`, `api_key`, `model` are config-only
- **Minimal dependencies**: proxy tests use stdlib only; CLI client only needs `openai` and `tomli`
- **Measurable learning**: `first_token_ms` and `total_ms` printed on every response
- **Progressive complexity**: Phase 0 needs only a browser; Phase 2 needs a C++ compiler
