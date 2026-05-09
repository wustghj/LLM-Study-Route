# LLM 学习路径优化 — 设计文档

> 日期：2026-05-09
> 状态：待审核

## 1. 目标

将现有 6 Phase LLM 学习项目重构为 7 层自顶向下路径，同时服务两类读者：

- **纯小白（零编程基础）**：早期 Phase 友好引导，重用比喻和图示
- **有编程基础但不熟悉 AI 的人**：后端类比加深理解，后期 Phase 深入工程细节

每层都建立在前一层之上，没有跳跃。

---

## 2. 新项目结构

```
llm-learning-path/
├── README.md                     # 项目入口 + 5 分钟快速开始
├── CLAUDE.md                     # Claude Code 配置（更新）
├── .gitignore                    # ★ 新增
├── .github/workflows/            # ★ 新增
│   └── check.yml                 #   语法检查 + smoke test
│
├── docs/                         # 📚 所有阅读内容
│   ├── start-here.md             #   30 分钟叙事指南（从 START-HERE.md 移入）
│   ├── learning-path.md          #   完整 7 Phase 课程表（从 LEARNING-PATH.md 移入）
│   ├── faq.md                    #   常见问题（从 FAQ.md 移入）
│   ├── concepts/                 #   概念深度解析
│   │   ├── llm-architecture.md
│   │   ├── tokenization.md
│   │   ├── embedding.md
│   │   └── training.md
│   ├── guides/                   #   实用技巧
│   │   └── prompt-engineering.md
│   └── appendix/                 # ★ 新增
│       ├── glossary.md           #   术语速查表
│       ├── troubleshooting.md   #   故障排查
│       └── resources.md          #   推荐阅读/视频链接
│
├── phase0-fundamentals/          # Phase 0：基础认知（纯阅读，有 README 引用 docs/）
│   └── README.md
│
├── phase1-api/                   # Phase 1：API 精通
│   ├── README.md                 # ★ 新增
│   ├── exercises/                # ★ 新增（3 个练习）
│   ├── main.py
│   ├── raw_client.py             #   + 详细教学注释
│   ├── benchmark.py
│   ├── config.example.toml
│   └── requirements.txt
│
├── phase2-transformer/           # Phase 2：理解模型内部 ★ 全新
│   ├── README.md                 # ★ 新增
│   ├── exercises/                # ★ 新增
│   ├── transformer_annotated.py  #   ★ 教学版（每步打印 shape）
│   ├── transformer.py            #   精简版
│   ├── attention_viz.py          #   ★ Attention 矩阵可视化
│   └── requirements.txt
│
├── phase3-local-deploy/          # Phase 3：本地部署 ★ 重构（原 Phase 2）
│   ├── README.md                 # ★ 新增
│   ├── exercises/                # ★ 新增
│   ├── experiments/              #   ★ 目录：6 个自动化实验脚本
│   │   ├── 01-cpu-vs-gpu.py
│   │   ├── 02-context-length.py
│   │   ├── 03-quantization.py
│   │   └── ...
│   ├── kv_cache_viz.py           #   ★ KV Cache 增长可视化
│   ├── getting-started.md        #   llama.cpp 编译指南
│   ├── kv-cache.md               #   KV Cache 概念
│   └── experiments.md            #   实验手册
│
├── phase4-apps/                  # Phase 4：应用构建
│   ├── rag/
│   │   ├── README.md
│   │   ├── exercises/
│   │   ├── rag.py
│   │   └── requirements.txt
│   └── agent/
│       ├── README.md
│       ├── exercises/
│       ├── agent.py
│       └── requirements.txt
│
├── phase5-customize/             # Phase 5：模型定制
│   ├── finetune/
│   │   ├── README.md
│   │   ├── exercises/
│   │   ├── prepare_data.py
│   │   ├── train.py
│   │   ├── inference.py
│   │   └── requirements.txt
│   └── prompt-engineering.md     #   引用 docs/guides/prompt-engineering.md
│
├── phase6-production/            # Phase 6：生产上线
│   ├── README.md
│   ├── exercises/
│   ├── docker-compose.yml        # ★ 新增
│   ├── logger.py
│   ├── cost.py
│   ├── loadtest.py
│   ├── gateway.py
│   └── requirements.txt
│
├── phase7-source/                # Phase 7：源码深水区 ★ 可选
│   ├── README.md
│   ├── llama-cpp-guide.md
│   └── reading-notes-template.md # ★ 新增
│
├── projects/                     # ★ 新增：跨 Phase 综合实战
│   ├── 01-personal-knowledge-base/
│   │   └── README.md             #   目标 + 参考方向（综合 Phase 1 + 4）
│   └── 02-code-review-bot/
│       └── README.md             #   （综合 Phase 1 + 4 + 5 + 6）
│
└── tools/                        # ★ 新增
    └── check_env.py              #   Python/依赖/显存 环境检查
```

### 需要删除的项

| 路径 | 原因 |
|------|------|
| `api调用实战/` | 空目录残留 |
| `howto/` | 未使用 |
| `meta-original-prompt.md` | 内部规划文件，非学习内容 |
| `meta-plan-artifact.md` | 内部规划文件，非学习内容 |
| `meta-short-video-draft.md` | 内部规划文件，非学习内容 |
| 根目录 `concepts/` | 移到 `docs/concepts/` |
| 根目录 `guides/` | 移到 `docs/guides/` |
| `START-HERE.md` | 内容移到 `docs/start-here.md`，根目录只放 README |
| `LEARNING-PATH.md` | 内容移到 `docs/learning-path.md` |
| `FAQ.md` | 内容移到 `docs/faq.md` |
| `phase1-api/cli-chat/conversations/` | .gitignore 排除 |
| `phase5-production/logs/` | .gitignore 排除 |
| `phase1-api/cli-chat/config.toml` | .gitignore 排除（但保留 config.example.toml） |

---

## 3. 7 层学习路径

```
Phase 0  基础认知      30 分钟纯阅读，建立心智模型
   ↓
Phase 1  API 精通      调 SDK、手写 HTTP、多 provider benchmark
   ↓
Phase 2  模型内部      纯 numpy 手写 Transformer 前向传播 ★ 新位置
   ↓
Phase 3  本地部署      Ollama、llama.cpp 编译、KV Cache、量化实验
   ↓
Phase 4  应用构建      RAG 检索增强 + Agent 智能体
   ↓
Phase 5  模型定制      Prompt Engineering + LoRA 微调
   ↓
Phase 6  生产上线      日志、成本、压测、网关
   ↓
Phase 7  源码深水区    llama.cpp C++ 源码阅读（可选，面向工程师）
```

### 为什么重新排序

原来的 Phase 2（编译 llama.cpp、理解 KV Cache）对小白是断崖——需要 C++ 编译器、需要理解推理引擎的概念。新路径的 Phase 2 用纯 numpy 实现 Transformer 前向传播，只需要 Python + numpy，小白可以安全探索"模型内部到底在算什么"。有了数学直觉后，Phase 3 再学 KV Cache 和量化就不再是天书。

### 各 Phase 详细内容

#### Phase 0 — 基础认知

- 内容：`docs/start-here.md`、`docs/faq.md`、`docs/concepts/` 四篇
- 改动：只做文件移动，内容不动
- 验收：能用自己的话解释 LLM 是什么；知道 token、temperature、幻觉 的含义

#### Phase 1 — API 精通

- 三个 Track：SDK 调用 → 手写 HTTP → benchmark 对比
- 改动：
  - 加 README 引导三 track 学习顺序
  - `raw_client.py` 加逐行中文注释当教学材料
  - 加 3 个 exercises：Temperature 对比实验、批量问答脚本、双 provider 延迟对比
- 验收：能用同一个客户端切换 DeepSeek/Ollama/Proxy 三种后端；能写出 SSE 数据流格式

#### Phase 2 — 模型内部 ★ 全新位置

- 两个版本：
  - `transformer_annotated.py`：纯注释教学版，每一步打印输入/输出 shape
  - `transformer.py`：精简版，辅助函数隐藏到 utils
- `attention_viz.py`：跑一次推理，输出 Attention 矩阵热力图
- README：逐层图解 Embedding → 位置编码 → 多头 Attention → FFN → 残差 → Logits
- exercises：手填 Attention 矩阵、改 num_heads 观察 shape 变化
- 验收：能画出 Attention QKV 流程并解释每个步骤的作用

#### Phase 3 — 本地部署

- 保留原来的 llama.cpp 编译指南、KV Cache 概念文档、实验手册
- 新增：`experiments/` 下 6 个 Python 脚本，自动调用 Ollama API 跑实验、输出表格结果
- 新增：`kv_cache_viz.py` 用 matplotlib 画出 KV Cache 随上下文长度的增长曲线
- README：引导三个环节（装 Ollama → 跑实验 → 理解 KV Cache）
- 验收：能用数据回答 GPU 加速对推理的帮助；能看到 KV Cache 大小和上下文长度的线性关系

#### Phase 4 — 应用构建

- 内容不变，结构优化：
  - RAG 和 Agent 各加 exercises/
  - RAG 练习：换文档库跑对比
  - Agent 练习：加一个新工具的指南
- 验收：能画出 RAG 流程图；能解释 Agent 的 Think→Act→Observe 循环

#### Phase 5 — 模型定制

- Prompt Engineering 内容引用 `docs/guides/prompt-engineering.md`
- LoRA 微调：补充 README 详解关键参数（rank、alpha、target_modules）的含义
- exercises：设计 system prompt，10 轮对话验证输出风格稳定性
- 验收：能解释 prompt engineering 和微调的区别

#### Phase 6 — 生产上线

- 加 `docker-compose.yml` 一键启动 gateway
- 加 exercises：自己跑 loadtest 找到并发瓶颈
- 验收：能回答"服务在多大并发下开始明显变慢？瓶颈在哪？"

#### Phase 7 — 源码深水区

- 内容不变（llama-cpp-guide.md）
- 新增：`reading-notes-template.md` 帮助读者做源码阅读笔记
- 标注为可选——不需要所有人都进到这一层

---

## 4. 质量标准

### 4.1 写作标准

每个 Phase 的 README 统一结构：

```
# Phase X：标题

📌 前置要求
🎯 学完你能回答
🗺️ 路线图（Track 1 → 2 → 3）
📖 核心内容
🏃 动手环节
✅ 验收题
🔗 下一步
```

两类读者的差异化处理：
- **正文面向小白**：比喻优先、避免术语堆砌、每步解释"为什么"
- **边栏/注释面向工程师**：`> 🧠 后端视角：xxx 相当于 yyy`

### 4.2 代码标准

- 每个 Phase 独立可运行（不跨 Phase 依赖代码文件）
- `requirements.txt` 锁定依赖版本
- `.py` 文件顶部一行注释说明用途
- 配置使用 `.example.toml` 提交，真实 `.toml` 被 gitignore 排除

### 4.3 CI

`.github/workflows/check.yml`：
- 触发：push 到 main，PR 到 main
- 每个 Phase：编译检查（`python -m py_compile`）
- 有依赖的 Phase：`pip install -r requirements.txt` 后运行 smoke test
- smoke test 成功标准：脚本以 exit 0 结束（无网络调用的最小验证）

### 4.4 .gitignore

```
*.toml
!*.example.toml
conversations/
logs/
*.jsonl
__pycache__/
*.pyc
.venv/
.DS_Store
*.gguf
*.bin
*.safetensors
```

---

## 5. 迁移计划

### 阶段 1：基础设施（不改内容）
1. 创建新目录结构
2. 编写 `.gitignore`
3. 编写 CI 配置
4. 编写 `tools/check_env.py`

### 阶段 2：文件迁移（不改内容）
5. 移动 docs/ 内容（concepts/、guides/、*.md）
6. 移动 Phase 代码到新位置
7. 重命名目录匹配新 Phase 编号
8. 删除残留目录和文件

### 阶段 3：内容新增（优先级最高）
9. Phase 2 全新内容（transformer_annotated.py、attention_viz.py、README、exercises）
10. Phase 3 实验脚本（experiments/ 下 6 个 script）
11. Phase 3 kv_cache_viz.py

### 阶段 4：内容补充
12. 各 Phase exercises/
13. 各 Phase README
14. projects/ 综合实战大纲
15. docs/appendix/ 整理

### 阶段 5：质量收尾
16. 全项目 README 更新
17. CLAUDE.md 更新
18. CI 验证通过
19. 小白测试：找一个人从头跑到 Phase 3，记录卡点并修复

---

## 6. 不在本次范围内

- 视频内容录制
- 在线平台部署
- 多语言翻译
- 自动评分系统

---

## 7. 风险

| 风险 | 缓解 |
|------|------|
| 目录重命名导致 git blame 丢失 | 用 `git mv` 保留文件历史 |
| Phase 2 新内容工作量被低估 | transformer.py 已有基础版，只需加注释 + 可视化 + README |
| 旧链接断裂（外部引用原文件路径） | 根目录 README 只保留入口链接；内部交叉引用用相对路径逐个修正 |
