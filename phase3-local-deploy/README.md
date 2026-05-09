# Phase 3：本地部署 — 在你自己电脑上跑模型

📌 **前置要求:** Phase 2（理解 Transformer 计算过程）

🎯 **学完你能回答:**
- 如何在 Windows 上安装 Ollama 并运行本地模型？
- 量化是什么？Q4_K_M 的"4"和"K"和"M"分别代表什么？
- KV Cache 为什么让长对话变慢？
- llama.cpp 和 Ollama 是什么关系？

🗺️ **路线图:**
1. **Track A: 本地模型部署** — 装 Ollama，拉模型，跑起来
   - 读 `windows-setup.md`
2. **Track B: 推理引擎入门** — 编译 llama.cpp，理解底层
   - 读 `getting-started.md`
3. **Track C: 理解 KV Cache** — 推理性能的核心概念
   - 读 `kv-cache.md`
   - 跑 `kv_cache_viz.py` 看 KV Cache 增长曲线
4. **Track D: 动手实验** — 6 组对照实验，填结果表
   - 读 `experiments.md`
   - 跑 `experiments/` 下的脚本

🏃 **动手环节:**

```powershell
# Track A: 安装 Ollama（去 ollama.com 下载）
ollama pull qwen2.5:7b
ollama run qwen2.5:7b

# Track B: （可选）编译 llama.cpp
git clone https://github.com/ggerganov/llama.cpp
cd llama.cpp && mkdir build && cd build
cmake .. && cmake --build . --config Release

# Track C: 观察 KV Cache
python kv_cache_viz.py

# Track D: 跑实验
cd experiments
python 01-cpu-vs-gpu.py
python 02-context-length.py
python 03-quantization.py
```

✅ **验收题:**
- [ ] 能用 Ollama 成功运行一个本地模型并对话
- [ ] 能用数据回答：GPU 加速对首 token 延迟帮助多大？
- [ ] 能画出 KV Cache 大小和上下文长度的关系曲线

🔗 **下一步:** Phase 4 — 构建 LLM 应用（RAG + Agent）
