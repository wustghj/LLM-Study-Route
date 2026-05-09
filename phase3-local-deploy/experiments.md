# llama.cpp 对照实验 — 纯小白版

> 用数据代替感觉。每个实验只改变一个变量，观察它对速度和资源的影响。

---

## 实验前必读

### 你需要什么

- 已编译好的 llama.cpp（参考 `getting-started.md`）
- 至少一个 GGUF 模型文件（推荐 qwen2.5-7b-instruct-q4_k_m.gguf）
- 本项目的 CLI 客户端（`cli-chat/benchmark.py`）

### 实验原则（最重要！）

```
每次只改一个变量，其他条件保持不变。
```

- 改 GPU 层数时，上下文长度、模型文件都不能变
- 改上下文长度时，GPU 层数、模型文件都不能变
- 每个实验跑至少 3 次取平均，排除网络/系统波动

### 没有 GPU 怎么办？

如果你没有 NVIDIA 显卡，实验 1（GPU 层数）和实验 4（Ollama vs llama.cpp）仍然可以做——你观察到的会是"纯 CPU 推理有多慢"，这本身就是一个重要的数据点。

实验 2（上下文长度）和实验 3（量化等级）在 CPU 上同样有效。

---

## 实验 0：建立基线

**为什么先做这个：** 你得有个"参照物"，才知道后面的改动是变好了还是变差了。

**做什么：** 用 Ollama 跑一次 benchmark，记录数据作为对比基准。

```powershell
# 确认 Ollama 在运行，且 qwen2.5:7b 已下载
ollama list

# 确保 config.toml 指向 Ollama
# base_url = "http://localhost:11434/v1"
# model = "qwen2.5:7b"
# api_key = "ollama"

cd ../../phase1-api/cli-chat
python benchmark.py --prompt medium --runs 3
```

**观察什么：**
- 首 token 延迟（first_token_ms）：多久开始输出第一个字
- 总耗时（total_ms）：完整回答花多长时间
- token/s：每秒生成多少个字

> 把这三个数字记下来，这就是你的**基线**。后面所有实验都跟它比。

---

## 实验 1：GPU 加速到底有多大用？

**核心问题：** 把模型的计算从 CPU 搬到 GPU，能快多少？

**你需要理解的参数：**

| 参数 | 含义 | 例子 |
|------|------|------|
| `-ngl 0` | 全部用 CPU 算（最慢） | 就像用人脑算 1000 道乘法 |
| `-ngl 20` | 20 层给 GPU，其余 CPU | 一半用计算器，一半人脑 |
| `-ngl 99` | 全部给 GPU（最快） | 全部用计算器 |

> `-ngl` = number of GPU layers。模型有很多"层"（Qwen2.5-7B 约 28 层），每层都可以选择在 CPU 还是 GPU 上计算。

**动手：**

```powershell
# 场景 A：纯 CPU
./bin/llama-server -m model.gguf -ngl 0 -c 4096 --port 8080
# 等服务器启动后：
python benchmark.py --prompt medium --runs 3

# 场景 B：部分 GPU（如果你的显卡支持）
# 关掉上一个 server（Ctrl+C），再启动新的：
./bin/llama-server -m model.gguf -ngl 20 -c 4096 --port 8080
python benchmark.py --prompt medium --runs 3

# 场景 C：全部 GPU（-ngl 设一个很大的数，llama.cpp 自动取最大值）
./bin/llama-server -m model.gguf -ngl 99 -c 4096 --port 8080
python benchmark.py --prompt medium --runs 3
```

**预期会看到什么：**
- CPU 模式：首 token 延迟可能 > 10 秒，token/s 很低
- GPU 模式：首 token 延迟可能降到 1-3 秒，token/s 高几十倍
- 纯 CPU 推理非常慢——这让你理解为什么大家都抢 GPU

---

## 实验 2：上下文越长越慢吗？

**核心问题：** 把上下文窗口从 2048 扩到 8192，速度和显存怎么变？

**背景：** 这就是在验证你刚读的 KV Cache 原理——上下文越大，KV Cache 越大，显存占用越多，速度可能越慢。

```powershell
# 场景 A：短上下文
./bin/llama-server -m model.gguf -c 2048 -ngl 35 --port 8080
python benchmark.py --prompt long --runs 3

# 场景 B：长上下文（注意：显存不够会直接启动失败！）
./bin/llama-server -m model.gguf -c 8192 -ngl 35 --port 8080
python benchmark.py --prompt long --runs 3
```

**观察重点：**
- 打开任务管理器 → 性能 → GPU → 专用 GPU 内存
  - `-c 2048` 时显存占用 ≈ ？
  - `-c 8192` 时显存占用 ≈ ？
  - 差值是不是接近 KV Cache 公式算出来的？
- token/s 有没有下降？（理论上 decode 阶段会更慢）

> 如果你的显存不够启动 `-c 8192`，恭喜——你亲身体验了"上下文长度由硬件决定"。

---

## 实验 3：量化——用质量换空间，值吗？

**核心问题：** Q2、Q4、Q8 三种量化等级，文件大小差多少？回答质量差多少？速度差多少？

**背景：** 量化就像"图片压缩"——JPEG 压缩越狠，文件越小，但画质越差。模型量化同理。

| 文件 | 量化 | 大约大小 | 直观类比 |
|------|------|---------|---------|
| `qwen2.5-7b-instruct-q2_k.gguf` | Q2_K | ~3 GB | 高度压缩的 JPEG，能看但糊 |
| `qwen2.5-7b-instruct-q4_k_m.gguf` | Q4_K_M | ~4.5 GB | 普通 JPEG，肉眼几乎看不出区别 |
| `qwen2.5-7b-instruct-q8_0.gguf` | Q8_0 | ~7.5 GB | 接近原图，但文件大了很多 |

> 你需要先下载这三个文件（Hugging Face 上搜 `Qwen2.5-7B-Instruct-GGUF`），挑这三个量化等级下载。

**动手：**

```powershell
# 依次用三个模型文件启动 server，跑同样的 benchmark
./bin/llama-server -m models/q2_k.gguf -c 4096 -ngl 35 --port 8080
python benchmark.py --prompt medium --runs 3

./bin/llama-server -m models/q4_k_m.gguf -c 4096 -ngl 35 --port 8080
python benchmark.py --prompt medium --runs 3

./bin/llama-server -m models/q8_0.gguf -c 4096 -ngl 35 --port 8080
python benchmark.py --prompt medium --runs 3
```

**怎么判断"回答质量"？** 不用看 benchmark 的数字——用同样的 prompt 问模型，**肉眼读**回答。比如问"用一句话解释什么是注意力机制"，三个版本的回答哪个更准、更流畅？

**预期会看到什么：**
- Q2_K：文件最小，但回答可能前言不搭后语或有明显错误
- Q4_K_M：文件适中，回答质量不错——这是大多数人的"甜点"
- Q8_0：文件最大，回答质量最好，但和 Q4 的差距可能没有想象中大

---

## 实验 4：Ollama vs 直接用 llama.cpp，差多少？

**核心问题：** Ollama 比原生 llama.cpp 多了一层封装，性能损失有多大？

**背景：** Ollama 底层就是 llama.cpp。但 Ollama 多了进程间通信、模型管理、API 路由等开销。

```powershell
# 用 Ollama 启动同一个模型
ollama run qwen2.5:7b

# 用 llama.cpp 直接启动同一个 GGUF 文件
./bin/llama-server -m model.gguf -c 4096 -ngl 35 --port 8080

# 分别跑 benchmark，对比
python benchmark.py --prompt medium --runs 5
```

**预期会看到什么：**
- 首 token 延迟：llama.cpp 可能略快（少一层进程间通信，几十到几百毫秒）
- token/s：非常接近（底层是同一个引擎）
- 结论：Ollama 的便利性（自动下载模型、管理版本、一键启动）远大于它的性能损失

---

## 结果记录表

把数据填进这张表，你会拥有一份自己的"推理性能档案"：

| 实验 | 条件 | 首 token(ms) | 总耗时(ms) | token/s | 显存(GB) | 备注 |
|------|------|-------------|-----------|---------|----------|------|
| 0 | Ollama 基线 | | | | | 参照物 |
| 1 | ngl=0（纯 CPU） | | | | | 慢到怀疑人生？ |
| 1 | ngl=20 | | | | | |
| 1 | ngl=99（全 GPU） | | | | | 最快能多快？ |
| 2 | ctx=2048 | | | | | |
| 2 | ctx=8192 | | | | | 显存涨了多少？ |
| 3 | Q2_K | | | — | | 回答质量怎样？ |
| 3 | Q4_K_M | | | — | | "甜点"级别 |
| 3 | Q8_0 | | | — | | 质量提升值 3GB 吗？ |
| 4 | Ollama | | | | | |
| 4 | llama.cpp | | | | | 差距可忽略？ |

---

## 做完所有实验后，回答这 5 个问题

1. **你的机器最适合什么配置？**（GPU 层数 + 上下文长度 + 量化等级的组合）
2. **量化从 Q4 到 Q8，文件大了 3GB，但你的肉眼能看出回答质量的提升吗？** 你觉得值吗？
3. **GPU 加速（-ngl）主要提升的是首 token 延迟，还是 token/s？** 为什么？（提示：回想 Prefill vs Decode）
4. **你的显卡最多能撑住多大的上下文？**（一直加 -c 直到启动失败，那个临界值就是答案）
5. **Ollama 比原生 llama.cpp 慢了多少？** 这个差距在你的场景里可接受吗？

---

## 如果卡住了

| 问题 | 可能原因 | 试试这个 |
|------|---------|---------|
| server 启动后 benchmark 连不上 | 端口被占用或 server 还没准备好 | 等 5 秒再跑，或者换 `--port 8081` |
| `-ngl 35` 报错 | 显卡不支持那么多层 | 降到 20 或 10 |
| `-c 8192` 启动失败 | 显存不够 | 降低到 4096 或 2048 |
| 不同实验的 token/s 差不多 | 正常！token/s 瓶颈通常在 GPU 计算能力，跟上下文关系不大 | 重点关注首 token 延迟和显存的变化 |
| 不知道在哪下载不同量化版本 | 去 Hugging Face 搜模型名+GGUF | 比如搜索 `Qwen2.5-7B-Instruct-GGUF` |
