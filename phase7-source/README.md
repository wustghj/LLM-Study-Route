# Phase 7：源码深水区 — 读懂 llama.cpp

📌 **前置要求:** Phase 3（了解 llama.cpp 的编译和使用）、C++ 基础

🎯 **学完你能回答:**
- GGUF 文件是怎么加载到内存的？
- llama_decode() 的实现流程是什么？
- KV Cache 在 C++ 里长什么样？
- Q4_K_M 量化块的结构是什么？

🗺️ **路线图:**

读 `llama-cpp-guide.md`，按 5 站路线阅读：

| 站 | 文件/函数 | 核心问题 | 时间 |
|----|----------|---------|------|
| 1 | `llama-model.cpp:llama_model_load()` | GGUF 文件怎么加载？ | 30min |
| 2 | `llama.cpp:llama_decode()` | 一次推理的完整流程 | 1h |
| 3 | KV Cache 结构体 | Phase 3 学的 KV Cache 在代码里长什么样？ | 45min |
| 4 | `ggml-quants.c` | Q4_K_M 权重怎么反量化？ | 30min |
| 5 | `ggml.h / ggml.c` | llama.cpp 的"深度学习框架"怎么造的？ | 1h |

📖 **做笔记:** 用 `reading-notes-template.md` 记录你的源码阅读笔记。

> 🧠 这是整个学习路径的终极挑战——作为 C++ 后端工程师，
> 读懂 llama.cpp 意味着你能自己优化推理引擎、接入新的硬件后端。

✅ **验收题:**
- [ ] 能在 llama.cpp 源码中找到 llama_decode() 和 KV Cache 结构体
- [ ] 能解释 GGUF 文件加载时为什么用 mmap 而不是 malloc
- [ ] 能说出 Prefill 和 Decode 在代码路径上的区别
