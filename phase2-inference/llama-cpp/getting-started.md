# llama.cpp 入门指南 — 纯小白版

> 前置条件：已完成 Phase 1（会用 API、部署过 Ollama、跑过 proxy 测试）
> 目标：绕过 Ollama，直接操作推理引擎，看看模型到底是怎么"跑"起来的

---

## 0. 你在做什么，为什么

到目前为止，你一直在用 Ollama 跑本地模型。Ollama 很好用，但它把底层细节全藏起来了——就像一个自动挡汽车，你踩油门就走，但不知道发动机怎么转的。

llama.cpp 是 Ollama 的"发动机"——纯 C/C++ 写的推理引擎。这次你要打开引擎盖，直接操作发动机：

```
之前:  你 → Ollama（黑盒）→ llama.cpp → GPU/CPU
现在:  你 → llama.cpp → GPU/CPU

Ollama 帮你在中间做了：
  - 下载和管理模型文件
  - 启动 HTTP 服务
  - 提供 REST API
  - 管理模型版本

这些事你自己也能做。而且直接操作 llama.cpp，你能看到：
  - 模型是怎么加载到内存的（为什么启动要等那么久）
  - KV Cache 到底占了多少显存（任务管理器里亲眼看到）
  - 调一个参数，速度立刻变化（-ngl 从 0 改成 99 的差距）
  - 不同量化等级的实际效果（不只是文件大小，还有回答质量）
```

---

## 1. 编译 llama.cpp

### 1.1 什么是"编译"

llama.cpp 是用 C/C++ 写的源代码。你需要把它变成能在你电脑上运行的 `.exe` 程序——这个过程叫**编译**。

**你需要装的东西：**

| 工具 | 作用 | 怎么装 |
|------|------|--------|
| **Git** | 从 GitHub 下载源代码 | [git-scm.com](https://git-scm.com) 下载安装 |
| **CMake** | 生成编译配置文件 | [cmake.org](https://cmake.org) 下载安装 |
| **C++ 编译器（Visual Studio）** | 把代码变成 exe | 安装 Visual Studio 2022 Community（免费），勾选"使用 C++ 的桌面开发" |

> 如果你已经有 Visual Studio 和 CMake（作为 C++ 后端工程师大概率已经有了），跳过安装直接开始编译。

### 1.2 编译步骤

```powershell
# 1. 下载 llama.cpp 源代码
git clone https://github.com/ggerganov/llama.cpp
cd llama.cpp

# 2. 创建编译目录（保持源代码干净）
mkdir build
cd build

# 3. 生成编译配置
#    有 NVIDIA 显卡 → 加 -DLLAMA_CUBLAS=ON（启用 CUDA 加速）
#    有 AMD 显卡     → 加 -DLLAMA_HIPBLAS=ON
#    纯 CPU          → 不加任何 flag
cmake .. -DLLAMA_CUBLAS=ON

# 4. 开始编译（这一步比较慢，等 5-15 分钟）
cmake --build . --config Release

# 5. 验证编译成功
./bin/Release/llama-server --help
# 或者
./bin/llama-cli --help
```

**每个命令在做什么：**

| 命令 | 做了什么 |
|------|---------|
| `git clone` | 把 GitHub 上的代码下载到你电脑 |
| `mkdir build && cd build` | 创建一个单独的编译目录（不污染源码） |
| `cmake ..` | 检测你的编译器、GPU、系统，生成编译指令 |
| `cmake --build .` | 实际编译——把 .cpp 文件变成 .exe |
| `--config Release` | 编译优化版（跑得快），不是调试版（跑得慢） |

### 1.3 编译失败了怎么办

| 报错 | 原因 | 解决 |
|------|------|------|
| `cmake: command not found` | CMake 没装或没加到 PATH | 重装 CMake，安装时勾选"Add to PATH" |
| `No CMAKE_CXX_COMPILER found` | 没装 C++ 编译器 | 装 Visual Studio 2022 Community，勾选 C++ 工作负载 |
| `CUDA not found` | 加了 `-DLLAMA_CUBLAS=ON` 但没装 CUDA | 去掉这个 flag（纯 CPU 编译），或装 CUDA Toolkit |
| `error: unknown type name` | 编译器版本太老 | 更新 Visual Studio 到最新版 |
| 编译到一半内存不足 | 并行编译开太多 | 加 `-j 2` 限制并行数：`cmake --build . -j 2 --config Release` |

---

## 2. 获取模型文件

编译完你有了"引擎"，但还需要"燃料"——模型文件。

llama.cpp 用 **GGUF** 格式的模型文件。这是一个打包好的单个文件，包含模型的所有权重数据。Ollama 下载的模型底层也是 GGUF，但 Ollama 把它拆成了多个文件存。

**去哪下载：** [Hugging Face](https://huggingface.co) 上搜 `Qwen2.5-7B-Instruct-GGUF`

推荐用命令行下载（比浏览器下载快且稳定）：

```powershell
# 安装下载工具
pip install huggingface-hub

# 下载 qwen2.5 7B 的 Q4_K_M 版本（推荐新手用这个）
huggingface-cli download Qwen/Qwen2.5-7B-Instruct-GGUF `
    qwen2.5-7b-instruct-q4_k_m.gguf `
    --local-dir ./models
```

**该下载哪个版本？**

| 如果你 | 推荐 |
|--------|------|
| 显存 ≤ 4GB | Q2_K 或更小的模型（如 Qwen2.5-1.5B） |
| 显存 6-8GB | Q4_K_M（甜点，质量和速度兼顾） |
| 显存 ≥ 12GB | Q8_0 或 Q6_K |
| 纯 CPU、内存 16GB | Q4_K_M，上下文别超过 4096 |

> 不知道显存多少？任务管理器 → 性能 → GPU → "专用 GPU 内存" 就是。

---

## 3. 启动你的第一个推理服务

```powershell
# 在 llama.cpp 目录下
./build/bin/Release/llama-server `
    -m ./models/qwen2.5-7b-instruct-q4_k_m.gguf `
    -c 4096 `
    --port 8080 `
    -ngl 35
```

看到类似这样的输出就成功了：
```
main: server is listening on http://127.0.0.1:8080
```

### 参数速查表

| 参数 | 作用 | 不设会怎样 | 怎么选 |
|------|------|-----------|--------|
| `-m` | 模型文件路径 | **必填**，不设启动不了 | 填你下载的 .gguf 文件路径 |
| `-c` | 上下文窗口大小（token） | 默认 512，聊两句就超了 | 设 4096（够用）或 8192（需要更多显存） |
| `-ngl` | 放到 GPU 的层数 | 默认 0，纯 CPU，慢 | 你的显卡显存 / 每层约 0.2GB。6GB 显存约能放 30 层 |
| `-t` | CPU 线程数 | 默认用全部核心 | 纯 CPU 推理时才需要调，有 GPU 不用管 |
| `--port` | HTTP 服务端口 | 默认 8080 | 被占用就换一个，如 `--port 8081` |
| `--temp` | Temperature（随机性） | 默认 0.8 | 不需要在启动时设，API 调用时可以覆盖 |
| `--mlock` | 锁住内存防止被系统换出 | 不锁 | 内存充足就加上，避免推理时卡顿 |

---

## 4. 用你的 CLI 客户端连接

现在 llama.cpp 在 `http://localhost:8080` 上提供了一个 **OpenAI-Compatible API**——和你一直用的 DeepSeek API、Ollama API 是同一套接口。

所以你不需要写新代码，只需要改配置文件：

```toml
# config.toml
api_key = "not-needed"          # llama.cpp 默认不验证 API Key
base_url = "http://localhost:8080/v1"
model = "qwen2.5-7b-instruct-q4_k_m"
system_prompt = "你是一个简洁、可靠的编程助手。"
temperature = 0.7
max_tokens = 2048
```

```powershell
cd ../../phase1-api/cli-chat
python main.py --config config.toml
```

> 不出意外的话，你应该能正常对话。如果连不上，检查：server 是不是还活着？端口号对不对？防火墙有没有拦？

---

## 5. 现在你有三个本地后端了

```
┌─────────────────────────────────────────────────────┐
│                  你的 CLI 客户端                      │
│           (只改 config.toml，不改代码)                │
└───────┬──────────────┬──────────────┬───────────────┘
        │              │              │
        ▼              ▼              ▼
┌──────────────┐ ┌──────────┐ ┌──────────────┐
│ DeepSeek 云   │ │  Ollama  │ │ llama.cpp    │
│ (最快最省心)  │ │ (最方便)  │ │ (最可控)     │
│ 付费          │ │ 免费      │ │ 免费         │
│ 有网就能用    │ │ 需 GPU   │ │ 需自己编译   │
└──────────────┘ └──────────┘ └──────────────┘
```

跑一遍 benchmark，三组数据放一起看：

```powershell
python benchmark.py --prompt medium --runs 3
```

你大概率会看到：
- **DeepSeek 云**：首 token 最快（别人的高端 GPU），但每次调用都花钱
- **Ollama**：比 llama.cpp 慢几十到几百毫秒（多一层封装），但用起来方便
- **llama.cpp**：最接近硬件，参数全可控

---

## 6. 接下来做什么

你已经打开了推理引擎的黑盒。现在趁热打铁：

1. **跑实验** — 打开 `experiments.md`，按 6 个实验做一遍，把数据填进表格
2. **读懂 KV Cache** — 打开 `kv-cache-deep-dive.md`，理解你刚才在任务管理器里看到的显存变化到底是怎么来的
3. （可选）**部署 vLLM** — Phase 2 的高性能推理框架，对比 Continuous Batching 和 llama.cpp 的单请求推理

---

## 7. 验收题

做完这篇指南，你应该能回答：

- [ ] llama.cpp 和 Ollama 是什么关系？谁在谁的"下面"？
- [ ] GGUF 文件是什么？为什么一个文件就包含整个模型？
- [ ] `-ngl` 参数改成 0 和改成 99，速度差多少？（亲手跑过数据）
- [ ] `-c` 参数从 2048 改成 4096，显存变化了吗？（亲眼在任务管理器里看到）
- [ ] 你的 CLI 客户端连上 llama.cpp 了吗？（亲手改 config.toml 连通过）

---

## 附录：C++ 后端工程师的视角（可选）

如果你有后端背景，这些对应关系会让 llama.cpp 的架构更好理解：

| llama.cpp 概念 | 后端类比 |
|---------------|---------|
| 模型加载（`-m`） | 服务启动时把一个大索引文件 mmap 到内存 |
| GPU 层数（`-ngl`） | 把计算卸载到加速卡——CPU 做调度，GPU 做矩阵乘法 |
| KV Cache | 请求上下文缓存——随会话增长，有最大容量，超了要淘汰 |
| Prefill 阶段 | 第一次 SQL 查询：解析 + 生成计划 + 扫描索引 |
| Decode 阶段 | 逐页返回结果——每页只查增量，不重新扫描 |
| Context Window（`-c`） | 最大请求/响应体大小 |
| GGUF 量化 | 用精度换空间——类似 float32 → int8 压缩，解压时损失精度 |
| `--mlock` | mlock() 系统调用——防止内存页被 swap 出去（避免 page fault 延迟） |
| Continuous Batching | 连接池复用——多个请求共享一次推理，减少空闲时间 |
