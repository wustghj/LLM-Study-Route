# llama.cpp 源码阅读指南 — C++ 后端工程师版

> Phase 6 进阶：用你的 C++ 功底，读懂业界最流行的推理引擎源码

---

## 为什么要读 llama.cpp 源码

- 它是目前最流行的本地推理引擎（Ollama 的底层、众多落地项目的基础）
- 纯 C/C++ 写成，没有 Python 胶水层——对后端工程师来说读起来很舒服
- 代码质量高，架构清晰，是学习"推理引擎怎么写"的最佳教材
- 你已经在 Phase 2 编译和用过它了，现在打开引擎盖看里面

---

## 阅读路线图

不要从头到尾硬读——4 万行 C++ 代码会淹死你。按下面的顺序，每次聚焦一个问题。

### 第 1 站：模型文件加载（30 分钟）

**你要回答：GGUF 文件是怎么被读进内存的？**

```
入口文件：llama-model.cpp
关键函数：llama_model_load()

阅读路径：
  1. gguf_init_from_file()     — 打开 GGUF 文件，解析元数据（层数、头数、维度...）
  2. llm_load_vocab()          — 加载 tokenizer 词汇表
  3. llm_load_tensors()        — 把权重数据 mmap 到内存
  4. llama_model_load() 的返回  — 一个 llama_model 结构体

观察：
  - 权重不是"读"进来的，是 mmap 进来的（零拷贝）
  - 量化权重在加载时反量化，还是推理时反量化？→ 看 ggml 的量化算子
```

### 第 2 站：一次推理的全流程（1 小时）

**你要回答：`llama_decode()` 到底做了什么？**

```
入口文件：llama.cpp
关键函数：llama_decode()

阅读路径：
  1. llama_decode()                     — 入口，接收 token IDs
  2. llm_build_context() 或类似函数     — 构建计算图
  3. ggml_graph_compute()               — 执行计算图
  4. 回到 llama_decode()，取 logits     — 拿到每个位置对词汇表的预测分数

观察：
  - Prefill 和 Decode 在代码里怎么区分？→ 看 seq_len：>1 = Prefill, =1 = Decode
  - KV Cache 在代码里怎么存储？→ 看 llama_kv_cache 结构体
  - 计算图（ggml graph）是什么？→ 类似 TensorFlow 的静态图，先构建再执行
```

### 第 3 站：KV Cache 的实现（45 分钟）

**你要回答：Phase 2 学到的 KV Cache，在 C++ 里到底长什么样？**

```
关键结构体：llama_kv_cache（在 llama.h 或 llama.cpp 里）

阅读路径：
  1. 找到 llama_kv_cache 的定义
     - 观察：cells 数组怎么组织的？每个 cell 存了什么？
     - 观察：has_shift 是什么？→ 滑动窗口的实现
  2. llama_kv_cache_find_slot()    — 怎么给新 token 分配 cache 位置？
  3. 在 llama_decode() 中搜索 "cache" → 看 K/V 怎么写入和读出

观察：
  - Cache 是预分配的（启动时根据 -c 参数分配一整块显存）
  - PagedAttention 没在 llama.cpp 里（那是 vLLM 的优化）→ 这是简化版
  - 超出上下文时怎么处理？→ 看 cache 满时的分支（丢弃最旧的 / 报错）
```

### 第 4 站：量化推理（30 分钟）

**你要回答：Q4_K_M 的权重在推理时怎么用？**

```
关键文件：ggml-quants.c, ggml-quants.h

阅读路径：
  1. block_q4_K 结构体          — Q4_K 的一个量化块长什么样？
     - d（缩放因子）+ 最小值 + 4bit 值的数组
  2. ggml_dequantize_block_q4_K()  — 反量化：4bit → float32
  3. 在 llama_decode() 中，权重的量化类型怎么影响计算路径？

观察：
  - 推理时每次都要反量化吗？→ 看 ggml 的量化矩阵乘法实现
  - 量化主要省的是显存（权重变小了），不是计算（反量化也有开销）
```

### 第 5 站：ggml 张量库（1 小时）

**你要回答：llama.cpp 的"深度学习框架"是怎么造的？**

```
关键文件：ggml.h, ggml.c

这是 llama.cpp 最核心的部分——一个 ~15000 行的 C 张量计算库。
类似 PyTorch 的 C++ 子集，但极简、无依赖。

阅读路径：
  1. ggml_tensor 结构体          — 张量怎么表示？
  2. ggml_graph_compute()        — 计算图怎么执行？
  3. ggml_compute_forward_*()    — 各种算子的前向实现
  4. 关注一个具体算子如 ggml_compute_forward_mul_mat() — 矩阵乘法怎么做的？

观察：
  - 为什么 ggml 不用 CUDA 也有不错的性能？→ 内存布局优化 + 多线程
  - CUDA 后端怎么接进来的？→ 看 ggml-cuda.cu
```

---

## 阅读技巧

### 不要做的事

- 不要从头到尾读每个文件——你会疯
- 不要试图理解每一行代码——先抓骨架，再填血肉
- 不要在没跑过的情况下读——编译、跑通、加日志、再读

### 推荐做的事

1. **加 printf 调试：** 在 `llama_decode()` 入口打印 `n_tokens`，在 KV Cache 写入处打印 `cache_pos`——看真实的推理过程
2. **用 gdb/lldb 单步：** 启动一个 server，attach 上去，发一个请求，在 `llama_decode` 设断点
3. **画调用图：** 每理解一个环节，画一张调用关系图（不需要 UML，手绘即可）
4. **改一个小功能：** 比如在每次 decode 后打印 KV Cache 的利用率——改动是最深刻的理解

---

## 验收题

读完这 5 站，你应该能回答：

- [ ] GGUF 文件加载时，权重的内存布局是怎样的？（mmap 还是 malloc？）
- [ ] Prefill 和 Decode 在代码路径上有什么区别？
- [ ] KV Cache 的 cells 数组是根据什么索引的？（seq_id？pos？）
- [ ] 一个 Q4_K 量化块占用多少字节？反量化时做了什么操作？
- [ ] ggml 的计算图和 TensorFlow 的静态图有什么异同？
