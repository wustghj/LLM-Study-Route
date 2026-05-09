# LLM 学习路径优化 — 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将 6 Phase LLM 学习项目重构为 7 层路径，重组目录结构，补充缺失代码，统一质量标准。

**Architecture:** 5 个阶段顺序执行——基础设施 → 文件迁移 → 内容新增 → 内容补充 → 质量收尾。每个阶段完成后项目保持可用。所有文件移动用 `git mv` 保留历史。

**Tech Stack:** Python 3.10+, numpy, matplotlib, openai, tomli, fastapi, Git

---

## 文件结构总览

最终结构对照 spec 第二节。关键变动：

| 旧路径 | 新路径 |
|--------|--------|
| `START-HERE.md` | `docs/start-here.md` |
| `LEARNING-PATH.md` | `docs/learning-path.md` |
| `FAQ.md` | `docs/faq.md` |
| `concepts/` | `docs/concepts/` |
| `guides/` | `docs/guides/` |
| `phase1-api/cli-chat/` | `phase1-api/` (扁平化) |
| `phase1-api/ollama/` | `phase3-local-deploy/` (合并) |
| `phase1-api/proxy-test/` | `phase1-api/proxy-test/` (保留) |
| `phase2-inference/llama-cpp/` | `phase3-local-deploy/` (合并) |
| `phase3-frameworks/rag/` | `phase4-apps/rag/` |
| `phase3-frameworks/agent/` | `phase4-apps/agent/` |
| `phase4-finetuning/finetune/` | `phase5-customize/finetune/` |
| `phase5-production/` | `phase6-production/` |
| `phase6-advanced/transformer.py` | `phase2-transformer/transformer.py` |
| `phase6-advanced/llama-cpp-guide.md` | `phase7-source/llama-cpp-guide.md` |

---

## 阶段 1：基础设施

### Task 1.1: 创建新目录结构

**Files:**
- Create: `docs/concepts/` (dir)
- Create: `docs/guides/` (dir)
- Create: `docs/appendix/` (dir)
- Create: `phase0-fundamentals/` (dir)
- Create: `phase2-transformer/` (dir)
- Create: `phase2-transformer/exercises/` (dir)
- Create: `phase3-local-deploy/experiments/` (dir)
- Create: `phase3-local-deploy/exercises/` (dir)
- Create: `phase4-apps/rag/exercises/` (dir)
- Create: `phase4-apps/agent/exercises/` (dir)
- Create: `phase5-customize/finetune/exercises/` (dir)
- Create: `phase6-production/exercises/` (dir)
- Create: `phase7-source/` (dir)
- Create: `projects/01-personal-knowledge-base/` (dir)
- Create: `projects/02-code-review-bot/` (dir)
- Create: `tools/` (dir)
- Create: `.github/workflows/` (dir)

- [ ] **Step 1: 创建所有新目录**

```powershell
New-Item -ItemType Directory -Force -Path "G:\AI学习路径\docs\concepts"
New-Item -ItemType Directory -Force -Path "G:\AI学习路径\docs\guides"
New-Item -ItemType Directory -Force -Path "G:\AI学习路径\docs\appendix"
New-Item -ItemType Directory -Force -Path "G:\AI学习路径\phase0-fundamentals"
New-Item -ItemType Directory -Force -Path "G:\AI学习路径\phase2-transformer\exercises"
New-Item -ItemType Directory -Force -Path "G:\AI学习路径\phase3-local-deploy\experiments"
New-Item -ItemType Directory -Force -Path "G:\AI学习路径\phase3-local-deploy\exercises"
New-Item -ItemType Directory -Force -Path "G:\AI学习路径\phase4-apps\rag\exercises"
New-Item -ItemType Directory -Force -Path "G:\AI学习路径\phase4-apps\agent\exercises"
New-Item -ItemType Directory -Force -Path "G:\AI学习路径\phase5-customize\finetune\exercises"
New-Item -ItemType Directory -Force -Path "G:\AI学习路径\phase6-production\exercises"
New-Item -ItemType Directory -Force -Path "G:\AI学习路径\phase7-source"
New-Item -ItemType Directory -Force -Path "G:\AI学习路径\projects\01-personal-knowledge-base"
New-Item -ItemType Directory -Force -Path "G:\AI学习路径\projects\02-code-review-bot"
New-Item -ItemType Directory -Force -Path "G:\AI学习路径\tools"
New-Item -ItemType Directory -Force -Path "G:\AI学习路径\.github\workflows"
```

- [ ] **Step 2: 验证目录创建**

```powershell
Get-ChildItem -Path "G:\AI学习路径" -Directory | Select-Object Name
```

- [ ] **Step 3: Commit**

```bash
git add -A
git commit -m "feat: create new directory structure for 7-phase reorganization"
```

---

### Task 1.2: 编写 .gitignore

**Files:**
- Create: `.gitignore`

- [ ] **Step 1: 编写 .gitignore 文件**

```
# 配置文件（含密钥）
*.toml
!*.example.toml

# 运行时数据
conversations/
logs/
*.jsonl

# Python
__pycache__/
*.pyc
*.pyo
.venv/
venv/
*.egg-info/
dist/

# 模型文件（太大）
*.gguf
*.bin
*.safetensors
*.pth
*.ckpt

# 系统文件
.DS_Store
Thumbs.db

# IDE
.vscode/
.idea/

# 临时文件
*.tmp
*.swp

# 训练输出
checkpoints/
output/
wandb/
```

- [ ] **Step 2: 验证 .gitignore 生效**

```powershell
git status --short
# 确认 conversations/ 和 logs/ 目录不再显示为 untracked
```

- [ ] **Step 3: Commit**

```bash
git add .gitignore
git commit -m "feat: add .gitignore for secrets, runtime data, and artifacts"
```

---

### Task 1.3: 编写 CI 配置

**Files:**
- Create: `.github/workflows/check.yml`

- [ ] **Step 1: 编写 CI workflow**

```yaml
name: Check

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  compile-check:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        phase:
          - phase1-api
          - phase2-transformer
          - phase4-apps/rag
          - phase4-apps/agent
          - phase5-customize/finetune
          - phase6-production
          - phase7-source
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Compile check ${{ matrix.phase }}
        run: |
          find ${{ matrix.phase }} -name "*.py" -exec python -m py_compile {} +

  smoke-test:
    runs-on: ubuntu-latest
    needs: compile-check
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Phase 2 smoke test
        working-directory: phase2-transformer
        run: |
          pip install numpy
          python transformer.py

      - name: Phase 6 production smoke tests
        working-directory: phase6-production
        run: |
          python -m py_compile logger.py
          python -m py_compile cost.py
          python cost.py  # cost.py has self-test when run directly
```

- [ ] **Step 2: Commit**

```bash
git add .github/workflows/check.yml
git commit -m "feat: add CI workflow for compile checks and smoke tests"
```

---

### Task 1.4: 编写环境检查工具

**Files:**
- Create: `tools/check_env.py`

- [ ] **Step 1: 编写 check_env.py**

```python
"""检查学习环境是否就绪。"""

import subprocess
import sys
import os


def check_python() -> bool:
    v = sys.version_info
    ok = v.major == 3 and v.minor >= 10
    print(f"  Python {v.major}.{v.minor}.{v.micro}: {'OK' if ok else '需要 3.10+'} "
          f"({sys.executable})")
    return ok


def check_pip_package(name: str, display: str = None) -> bool:
    try:
        __import__(name)
        print(f"  {display or name}: OK")
        return True
    except ImportError:
        print(f"  {display or name}: 未安装 (pip install {name})")
        return False


def check_gpu() -> str:
    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader"],
            capture_output=True, text=True, timeout=10,
        )
        if result.returncode == 0:
            info = result.stdout.strip()
            print(f"  GPU: {info}")
            return info
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    print("  GPU: 未检测到 NVIDIA GPU（纯 CPU 推理会很慢）")
    return ""


def check_ram() -> str:
    try:
        import psutil
        total = psutil.virtual_memory().total / (1024 ** 3)
        print(f"  RAM: {total:.1f} GB")
        return f"{total:.1f} GB"
    except ImportError:
        print("  RAM: 无法检测（pip install psutil 可以看详细内存信息）")
        return ""


def main():
    print("=" * 50)
    print("LLM 学习路径 — 环境检查")
    print("=" * 50)

    print("\n[Python]")
    py_ok = check_python()

    print("\n[核心依赖]")
    deps = [
        ("openai", "openai"),
        ("numpy", "numpy"),
        ("tomllib", "tomli/tomllib"),
    ]
    dep_ok = all(check_pip_package(name, display) for name, display in deps)

    print("\n[硬件]")
    check_gpu()
    check_ram()

    print("\n[网络]")
    try:
        import urllib.request
        urllib.request.urlopen("https://api.deepseek.com", timeout=5)
        print("  DeepSeek API: 可达")
    except Exception:
        print("  DeepSeek API: 不可达（可能需要 VPN/代理）")

    print("\n[API Key]")
    for var in ["DEEPSEEK_API_KEY", "OPENAI_API_KEY", "PROXY_API_KEY"]:
        val = os.getenv(var, "")
        if val:
            masked = val[:7] + "***" + val[-4:] if len(val) > 11 else "***"
            print(f"  {var}: {masked}")
        else:
            print(f"  {var}: 未设置")

    print("\n" + "=" * 50)
    if py_ok and dep_ok:
        print("环境就绪，可以开始学习！")
    else:
        print("请先解决上述问题再继续。")
    print("=" * 50)


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: 验证脚本可运行**

```powershell
python tools/check_env.py
```

- [ ] **Step 3: Commit**

```bash
git add tools/check_env.py
git commit -m "feat: add environment checker tool"
```

---

## 阶段 2：文件迁移

### Task 2.1: 移动文档到 docs/

- [ ] **Step 1: 移动概念和指南目录**

```powershell
git mv concepts/llm-architecture.md docs/concepts/llm-architecture.md
git mv concepts/tokenization.md docs/concepts/tokenization.md
git mv concepts/embedding.md docs/concepts/embedding.md
git mv concepts/training.md docs/concepts/training.md
git mv guides/prompt-engineering.md docs/guides/prompt-engineering.md
```

- [ ] **Step 2: 移动根文档**

```powershell
git mv START-HERE.md docs/start-here.md
git mv LEARNING-PATH.md docs/learning-path.md
git mv FAQ.md docs/faq.md
```

- [ ] **Step 3: 清理空目录**

```powershell
Remove-Item -Force -Recurse "G:\AI学习路径\concepts" -ErrorAction SilentlyContinue
Remove-Item -Force -Recurse "G:\AI学习路径\guides" -ErrorAction SilentlyContinue
```

- [ ] **Step 4: Commit**

```bash
git add -A
git commit -m "refactor: move docs and concepts to docs/ directory"
```

---

### Task 2.2: 重组 Phase 目录（Phase 1 → Phase 1）

- [ ] **Step 1: 扁平化 phase1-api/cli-chat → phase1-api**

```powershell
# 先创建新目录结构
git mv phase1-api/cli-chat/main.py phase1-api/main.py
git mv phase1-api/cli-chat/raw_client.py phase1-api/raw_client.py
git mv phase1-api/cli-chat/benchmark.py phase1-api/benchmark.py
git mv phase1-api/cli-chat/config.example.toml phase1-api/config.example.toml
git mv phase1-api/cli-chat/requirements.txt phase1-api/requirements.txt
git mv phase1-api/cli-chat/README.md phase1-api/README.md
```

- [ ] **Step 2: 移动 proxy-test 保留在 phase1-api 下**

```powershell
# proxy-test 已经在 phase1-api/ 下，不需要动
# 验证: Get-ChildItem phase1-api/proxy-test/
```

- [ ] **Step 3: 移动 conversations 目录到 phase1-api/**

```powershell
git mv phase1-api/cli-chat/conversations/ phase1-api/conversations/
```

- [ ] **Step 4: 清理旧 cli-chat 目录**

```powershell
Remove-Item -Force -Recurse "G:\AI学习路径\phase1-api\cli-chat" -ErrorAction SilentlyContinue
```

- [ ] **Step 5: Commit**

```bash
git add -A
git commit -m "refactor: flatten phase1-api structure"
```

---

### Task 2.3: 重组 Phase 目录（Phase 1 → Phase 3）

- [ ] **Step 1: 移动 ollama 笔记到 phase3-local-deploy**

```powershell
git mv phase1-api/ollama/model-benchmark.md phase3-local-deploy/model-benchmark.md
git mv phase1-api/ollama/windows-setup.md phase3-local-deploy/windows-setup.md
Remove-Item -Force -Recurse "G:\AI学习路径\phase1-api\ollama" -ErrorAction SilentlyContinue
```

- [ ] **Step 2: 移动 Phase 2 (inference) 内容到 phase3-local-deploy**

```powershell
git mv phase2-inference/llama-cpp/getting-started.md phase3-local-deploy/getting-started.md
git mv phase2-inference/llama-cpp/kv-cache.md phase3-local-deploy/kv-cache.md
git mv phase2-inference/llama-cpp/experiments.md phase3-local-deploy/experiments.md
Remove-Item -Force -Recurse "G:\AI学习路径\phase2-inference" -ErrorAction SilentlyContinue
```

- [ ] **Step 3: Commit**

```bash
git add -A
git commit -m "refactor: consolidate local deploy content into phase3-local-deploy"
```

---

### Task 2.4: 重组剩余 Phase 目录

- [ ] **Step 1: 移动 Phase 3 frameworks → Phase 4 apps**

```powershell
git mv phase3-frameworks/rag/rag.py phase4-apps/rag/rag.py
git mv phase3-frameworks/rag/README.md phase4-apps/rag/README.md
git mv phase3-frameworks/rag/requirements.txt phase4-apps/rag/requirements.txt
git mv phase3-frameworks/agent/agent.py phase4-apps/agent/agent.py
git mv phase3-frameworks/agent/README.md phase4-apps/agent/README.md
git mv phase3-frameworks/agent/requirements.txt phase4-apps/agent/requirements.txt
Remove-Item -Force -Recurse "G:\AI学习路径\phase3-frameworks" -ErrorAction SilentlyContinue
```

- [ ] **Step 2: 移动 Phase 4 finetuning → Phase 5 customize**

```powershell
git mv phase4-finetuning/finetune/prepare_data.py phase5-customize/finetune/prepare_data.py
git mv phase4-finetuning/finetune/train.py phase5-customize/finetune/train.py
git mv phase4-finetuning/finetune/inference.py phase5-customize/finetune/inference.py
git mv phase4-finetuning/finetune/README.md phase5-customize/finetune/README.md
git mv phase4-finetuning/finetune/requirements.txt phase5-customize/finetune/requirements.txt
Remove-Item -Force -Recurse "G:\AI学习路径\phase4-finetuning" -ErrorAction SilentlyContinue
```

- [ ] **Step 3: 移动 Phase 5 production → Phase 6 production**

```powershell
git mv phase5-production/logger.py phase6-production/logger.py
git mv phase5-production/cost.py phase6-production/cost.py
git mv phase5-production/loadtest.py phase6-production/loadtest.py
git mv phase5-production/gateway.py phase6-production/gateway.py
git mv phase5-production/README.md phase6-production/README.md
git mv phase5-production/requirements.txt phase6-production/requirements.txt
# logs 已被 .gitignore 排除，不需要移动
Remove-Item -Force -Recurse "G:\AI学习路径\phase5-production" -ErrorAction SilentlyContinue
```

- [ ] **Step 4: 移动 Phase 6 advanced → Phase 2 transformer + Phase 7 source**

```powershell
git mv phase6-advanced/transformer.py phase2-transformer/transformer.py
git mv phase6-advanced/llama-cpp-guide.md phase7-source/llama-cpp-guide.md
Remove-Item -Force -Recurse "G:\AI学习路径\phase6-advanced" -ErrorAction SilentlyContinue
```

- [ ] **Step 5: Commit**

```bash
git add -A
git commit -m "refactor: renumber all phases to new 7-layer structure"
```

---

### Task 2.5: 删除残留文件和目录

- [ ] **Step 1: 删除所有残留**

```powershell
Remove-Item -Force -Recurse "G:\AI学习路径\api调用实战" -ErrorAction SilentlyContinue
Remove-Item -Force -Recurse "G:\AI学习路径\howto" -ErrorAction SilentlyContinue
Remove-Item -Force "G:\AI学习路径\meta-original-prompt.md" -ErrorAction SilentlyContinue
Remove-Item -Force "G:\AI学习路径\meta-plan-artifact.md" -ErrorAction SilentlyContinue
Remove-Item -Force "G:\AI学习路径\meta-short-video-draft.md" -ErrorAction SilentlyContinue
```

- [ ] **Step 2: Commit**

```bash
git add -A
git commit -m "chore: remove residual empty directories and meta files"
```

---

### Task 2.6: 修复内部路径引用

**Files:**
- Modify: `phase4-apps/rag/rag.py`
- Modify: `phase4-apps/agent/agent.py`
- Modify: `phase1-api/main.py:25` (security fix — hardcoded API key)

- [ ] **Step 1: 修复 rag.py 中的 config 路径**

在 `phase4-apps/rag/rag.py` 中，将 `load_llm_config()` 函数中对旧路径的引用改为读取同目录或 phase1-api 的配置：

```python
def load_llm_config() -> dict[str, str]:
    """从 phase1-api 的 config.toml 读取 LLM 配置"""
    config_path = Path(__file__).parent.parent.parent / "phase1-api" / "config.toml"
    if not config_path.exists():
        return DEFAULT_CONFIG
    with config_path.open("rb") as f:
        cfg = tomllib.load(f)
    result = DEFAULT_CONFIG.copy()
    result.update(cfg)
    return {k: resolve_env(v) for k, v in result.items()}
```

- [ ] **Step 2: 修复 agent.py 中的 config 路径**

在 `phase4-apps/agent/agent.py` 中，同样修改 `load_config()`：

```python
def load_config() -> dict[str, str]:
    path = Path(__file__).parent.parent.parent / "phase1-api" / "config.toml"
    if not path.exists():
        return DEFAULT_CONFIG
    with path.open("rb") as f:
        cfg = tomllib.load(f)
    result = DEFAULT_CONFIG.copy()
    result.update(cfg)
    return {k: resolve_env(v) for k, v in result.items()}
```

- [ ] **Step 3: 修复 main.py 中硬编码的 API Key（安全修复）**

将 `phase1-api/main.py` 第 25 行的硬编码 Key：
```python
"api_key": "sk-你的key",
```
改为：
```python
"api_key": "$DEEPSEEK_API_KEY",
```

- [ ] **Step 4: 验证所有 .py 文件语法正确**

```powershell
Get-ChildItem -Path "G:\AI学习路径" -Recurse -Filter "*.py" | ForEach-Object {
    python -m py_compile $_.FullName
    if ($?) { Write-Host "OK: $($_.Name)" } else { Write-Host "FAIL: $($_.Name)" }
}
```

- [ ] **Step 5: Commit**

```bash
git add -A
git commit -m "fix: update internal paths and remove hardcoded API key"
```

---

## 阶段 3：内容新增

### Task 3.1: 编写 Phase 2 — transformer_annotated.py

**Files:**
- Create: `phase2-transformer/transformer_annotated.py`

`transformer.py` 已经存在且质量很高。`transformer_annotated.py` 在其基础上强化每步的 shape 打印和学习引导。

- [ ] **Step 1: 编写 annotated 版**

```python
"""
transformer_annotated.py — Phase 2 教学版：手写 Transformer 前向传播

和 transformer.py 功能完全一样，但每一步打印输入输出的 shape 和含义。
适合第一次运行——跟着 shape 的变化理解数据流。
跑通后再去看 transformer.py 的精简版。

用法：
    pip install numpy
    python transformer_annotated.py
"""

import numpy as np


def section(title: str):
    """打印章节标题"""
    print(f"\n{'=' * 70}")
    print(f"  {title}")
    print(f"{'=' * 70}")


def show(name: str, arr: np.ndarray):
    """打印数组的名称和形状"""
    print(f"  {name:30s}  shape={str(arr.shape):20s}  dtype={arr.dtype}")


def explain(text: str):
    """打印解释文字"""
    print(f"    💡 {text}")


# =========================================================================
# 1. Embedding：把 token ID 变成向量
# =========================================================================

def token_embedding(token_ids: np.ndarray, embedding_matrix: np.ndarray) -> np.ndarray:
    result = embedding_matrix[token_ids]
    show("token_ids", token_ids)
    show("embedding_matrix (词汇表)", embedding_matrix)
    show("→ 查表结果", result)
    explain(f"每个 token ID 在 embedding_matrix 里找到对应的行")
    explain(f"一个整数 → 一个 {result.shape[-1]} 维的稠密向量")
    return result


# =========================================================================
# 2. 位置编码：注入顺序信息
# =========================================================================

def sinusoidal_positional_encoding(seq_len: int, d_model: int) -> np.ndarray:
    pos = np.arange(seq_len)[:, np.newaxis]
    i = np.arange(d_model)[np.newaxis, :]
    angle = pos / np.power(10000, (2 * (i // 2)) / d_model)

    pe = np.zeros((seq_len, d_model))
    pe[:, 0::2] = np.sin(angle[:, 0::2])
    pe[:, 1::2] = np.cos(angle[:, 1::2])

    show("位置编码矩阵", pe)
    explain(f"({seq_len}, {d_model}) — 每行是一个位置的"指纹"")
    explain("偶数列用 sin，奇数列用 cos——这是论文里的标准做法")
    return pe


# =========================================================================
# 3. 自注意力：核心机制
# =========================================================================

def scaled_dot_product_attention(
    Q: np.ndarray, K: np.ndarray, V: np.ndarray,
    mask: np.ndarray | None = None,
) -> np.ndarray:
    d_k = Q.shape[-1]
    show("Q (查询)", Q)
    show("K (键)", K)
    show("V (值)", V)
    explain("Q=我要找什么, K=每个位置有什么, V=每个位置的实际内容")

    # Step 1: 计算分数
    scores = Q @ K.transpose(0, 1, 3, 2)
    show("Q @ K^T (注意力分数)", scores)
    explain(f"形状 ({scores.shape[-2]}, {scores.shape[-1]}) — 每个 token 对每个 token 的相关性")

    # Step 2: 缩放
    scores = scores / np.sqrt(d_k)
    explain(f"÷ sqrt(d_k={d_k}) = ÷ {np.sqrt(d_k):.1f}  — 防止点积太大，softmax 饱和")

    # Step 3: Mask
    if mask is not None:
        scores = scores + mask
        explain("加上因果 mask：让位置 i 只能看到 0~i")

    # Step 4: Softmax
    scores = scores - scores.max(axis=-1, keepdims=True)
    exp_scores = np.exp(scores)
    attention_weights = exp_scores / exp_scores.sum(axis=-1, keepdims=True)
    show("Softmax 后 (注意力权重)", attention_weights)
    explain("每行的和 = 1.0 — 像一个概率分布")

    # Step 5: 加权求和
    output = attention_weights @ V
    show("注意力输出 (权重×V)", output)
    explain("用注意力权重对 V 做加权平均——关注度越高，贡献越大")

    return output


def multi_head_attention(
    x: np.ndarray,
    W_Q: np.ndarray, W_K: np.ndarray, W_V: np.ndarray, W_O: np.ndarray,
    n_heads: int,
    mask: np.ndarray | None = None,
) -> np.ndarray:
    batch, seq_len, d_model = x.shape
    d_k = d_model // n_heads

    show("多头注意力输入 x", x)

    Q = x @ W_Q
    K = x @ W_K
    V = x @ W_V
    show("  投影后 Q", Q)
    show("  投影后 K", K)
    show("  投影后 V", V)
    explain(f"线性投影：把 d_model={d_model} 映射为 Q/K/V 空间")

    Q = Q.reshape(batch, seq_len, n_heads, d_k).transpose(0, 2, 1, 3)
    K = K.reshape(batch, seq_len, n_heads, d_k).transpose(0, 2, 1, 3)
    V = V.reshape(batch, seq_len, n_heads, d_k).transpose(0, 2, 1, 3)
    show("  切分后 Q (多头)", Q)
    explain(f"切成 {n_heads} 个头，每个头维度 d_k={d_k}")
    explain("每个头独立做 Attention，关注不同类型的关系")

    print(f"\n  --- 对 {n_heads} 个头分别做 Attention ---")
    attn_output = scaled_dot_product_attention(Q, K, V, mask)

    attn_output = attn_output.transpose(0, 2, 1, 3).reshape(batch, seq_len, d_model)
    show("  拼回头", attn_output)
    explain(f"把 {n_heads} 个头拼回 d_model={d_model} 维")

    output = attn_output @ W_O
    show("  输出投影后", output)
    explain("W_O 把多头信息融合成一个统一的表示")

    return output


# =========================================================================
# 4. 前馈网络
# =========================================================================

def feed_forward(x: np.ndarray, W1: np.ndarray, W2: np.ndarray) -> np.ndarray:
    show("FFN 输入", x)
    hidden = x @ W1
    show("  W1 升维后", hidden)
    explain(f"d_model → d_ff ({W1.shape[-1]})，通常升 4 倍——给足够的容量")

    hidden = np.maximum(0, hidden)
    explain("ReLU 激活：max(0, x)——引入非线性")

    output = hidden @ W2
    show("  W2 降维后 (FFN 输出)", output)
    explain(f"d_ff → d_model，恢复原始维度")

    return output


# =========================================================================
# 5. 层归一化
# =========================================================================

def layer_norm(x: np.ndarray, gamma: np.ndarray, beta: np.ndarray, eps: float = 1e-6) -> np.ndarray:
    mean = x.mean(axis=-1, keepdims=True)
    var = x.var(axis=-1, keepdims=True)
    show("LN 输入", x)
    normed = (x - mean) / np.sqrt(var + eps)
    result = gamma * normed + beta
    show("LN 输出", result)
    explain(f"均值={mean[0,0,0]:.3f}, 方差={var[0,0,0]:.3f}  → 归一化到均值0方差1")
    return result


# =========================================================================
# 6. Transformer 层
# =========================================================================

def transformer_layer(
    x: np.ndarray,
    attn_params: dict,
    ffn_params: dict,
    ln_params: dict,
    n_heads: int,
    layer_idx: int,
    mask: np.ndarray | None = None,
) -> np.ndarray:
    print(f"\n  {'─' * 60}")
    print(f"  Layer {layer_idx + 1}")
    print(f"  {'─' * 60}")

    # 子层 1: Attention + 残差
    attn_in = layer_norm(x, **ln_params["attn_ln"])
    attn_out = multi_head_attention(attn_in, **attn_params, n_heads=n_heads, mask=mask)
    x = x + attn_out
    show("Attention + 残差后", x)
    explain("残差连接：x + Attention(x)——即使 Attention 学到的是 0，输入也能原样传过去")

    # 子层 2: FFN + 残差
    ffn_in = layer_norm(x, **ln_params["ffn_ln"])
    ffn_out = feed_forward(ffn_in, **ffn_params)
    x = x + ffn_out
    show("FFN + 残差后", x)
    explain("残差连接：x + FFN(x)")

    return x


# =========================================================================
# 7. 完整前向传播
# =========================================================================

def transformer_forward(
    token_ids: np.ndarray,
    embedding: np.ndarray,
    positional_encoding: np.ndarray,
    layers: list[dict],
    lm_head: np.ndarray,
    n_heads: int,
    mask: np.ndarray | None = None,
) -> np.ndarray:
    section("Step 1: Embedding 查表")
    x = token_embedding(token_ids, embedding)

    section("Step 2: 加位置编码")
    x = x + positional_encoding[:token_ids.shape[1], :]
    show("Embedding + 位置编码", x)
    explain("位置编码和 embedding 直接相加——简单的做法，但效果很好")

    section("Step 3: 通过 Transformer 层")
    for i, layer in enumerate(layers):
        x = transformer_layer(x, **layer, n_heads=n_heads, layer_idx=i, mask=mask)

    section("Step 4: 最终投影 (LM Head)")
    logits = x @ lm_head.T
    show("输出 logits", logits)
    explain(f"({logits.shape[-2]} 个位置) × ({logits.shape[-1]} 个候选词)")
    explain("每个位置对词汇表中每个词的"倾向"——分数越高越可能是下一个 token")

    return logits


# =========================================================================
# Demo
# =========================================================================

def demo():
    print("=" * 70)
    print("  迷你 Transformer — 带 shape 注解的完整前向传播")
    print("  零数学，只看数据形状变化")
    print("=" * 70)

    vocab_size = 1000
    d_model = 64
    n_heads = 4
    d_ff = 256
    n_layers = 2
    seq_len = 6

    np.random.seed(42)

    token_ids = np.array([[15, 234, 89, 567, 2, 0]])

    section("超参数")
    print(f"  vocab_size={vocab_size}  (词汇表大小)")
    print(f"  d_model={d_model}        (向量维度，GPT-3 是 12288)")
    print(f"  n_heads={n_heads}         (注意力头数)")
    print(f"  d_ff={d_ff}          (FFN 隐藏层维度 = d_model×4)")
    print(f"  n_layers={n_layers}        (Transformer 层数)")
    print(f"  seq_len={seq_len}         (输入序列长度)")
    print(f"  输入 token IDs: {token_ids[0].tolist()}")

    embedding = np.random.randn(vocab_size, d_model).astype(np.float32)
    pe = sinusoidal_positional_encoding(seq_len, d_model)
    causal_mask = np.triu(np.ones((seq_len, seq_len)) * -1e9, k=1)

    d_k = d_model // n_heads
    layers = []
    for i in range(n_layers):
        layers.append({
            "attn_params": {
                "W_Q": np.random.randn(d_model, d_model).astype(np.float32) * 0.02,
                "W_K": np.random.randn(d_model, d_model).astype(np.float32) * 0.02,
                "W_V": np.random.randn(d_model, d_model).astype(np.float32) * 0.02,
                "W_O": np.random.randn(d_model, d_model).astype(np.float32) * 0.02,
            },
            "ffn_params": {
                "W1": np.random.randn(d_model, d_ff).astype(np.float32) * 0.02,
                "W2": np.random.randn(d_ff, d_model).astype(np.float32) * 0.02,
            },
            "ln_params": {
                "attn_ln": {"gamma": np.ones(d_model), "beta": np.zeros(d_model)},
                "ffn_ln": {"gamma": np.ones(d_model), "beta": np.zeros(d_model)},
            },
        })

    lm_head = np.random.randn(vocab_size, d_model).astype(np.float32) * 0.02

    logits = transformer_forward(
        token_ids, embedding, pe, layers, lm_head, n_heads, causal_mask,
    )

    last_logits = logits[0, -1, :]
    predicted_token = int(np.argmax(last_logits))

    section("总结")
    print(f"""
  一条 token ID 的数据旅程：

  整数 [{', '.join(str(t) for t in token_ids[0])}]
    → Embedding 查表：每个 ID 变成 {d_model} 维向量
    → + 位置编码：注入"第几个位置"的信息
    → 通过 {n_layers} 个 Transformer 层：
        每层 = LayerNorm → 多头 Attention → + 残差
             → LayerNorm → FFN (升维→ReLU→降维) → + 残差
    → LM Head 投影到 {vocab_size} 维
    → argmax 取最大值 → 预测下一个 token = {predicted_token}

  真正的 GPT 模型只是把数字放大：
    d_model=768~12288, n_layers=12~96, vocab_size=50000~100000
  核心计算完全一样。
  """)

    # 展示 Attention 权重
    section("附加：看看 Attention 权重矩阵")
    print("  输入 token: 我(15) 喜欢(234) 学习(89) 大模型(567) [EOS](2) [PAD](0)")
    print()

    x_demo = token_embedding(token_ids, embedding) + pe[:seq_len, :]
    Q_d = x_demo @ layers[0]["attn_params"]["W_Q"]
    K_d = x_demo @ layers[0]["attn_params"]["W_K"]
    Q_d = Q_d.reshape(1, seq_len, n_heads, d_k).transpose(0, 2, 1, 3)
    K_d = K_d.reshape(1, seq_len, n_heads, d_k).transpose(0, 2, 1, 3)
    scores_d = Q_d @ K_d.transpose(0, 1, 3, 2) / np.sqrt(d_k)
    scores_d = scores_d + causal_mask
    scores_d = scores_d - scores_d.max(axis=-1, keepdims=True)
    weights_d = np.exp(scores_d) / np.exp(scores_d).sum(axis=-1, keepdims=True)

    token_labels = ["我(15)", "喜欢(234)", "学习(89)", "大模型(567)", "[EOS](2)", "[PAD](0)"]

    for h in range(min(n_heads, 2)):
        print(f"  Head {h + 1} 的注意力矩阵（行=查询者, 列=被关注者, 因果mask导致上三角为0）：")
        print(f"    {'':12s}", end="")
        for label in token_labels:
            print(f"{label:>10s}", end="")
        print()
        for i, from_label in enumerate(token_labels):
            print(f"    {from_label:12s}", end="")
            for j in range(seq_len):
                w = weights_d[0, h, i, j]
                if w > 0.01:
                    print(f"{w:10.3f}", end="")
                else:
                    print(f"{'0':>10s}", end="")
            print()
        print()

    print("  观察：")
    print("  - 每行的和 = 1.0（概率分布）")
    print("  - 上三角全是 0（因果mask——不能让当前位置看到未来）")
    print("  - 每个头可能关注不同的模式")
    print("  - 因为权重是随机的，这里的分布没有实际意义——真正的模型训练后会学到有意义的模式")


if __name__ == "__main__":
    demo()
```

- [ ] **Step 2: 验证运行**

```powershell
cd phase2-transformer
pip install numpy
python transformer_annotated.py
```

- [ ] **Step 3: Commit**

```bash
git add phase2-transformer/transformer_annotated.py
git commit -m "feat(phase2): add annotated transformer for step-by-step learning"
```

---

### Task 3.2: 编写 Phase 2 — attention_viz.py

**Files:**
- Create: `phase2-transformer/attention_viz.py`

- [ ] **Step 1: 编写 attention 可视化脚本**

```python
"""Visualize attention weights from the transformer demo."""

import numpy as np
from transformer import (
    token_embedding,
    sinusoidal_positional_encoding,
    multi_head_attention,
)

def main():
    vocab_size = 1000
    d_model = 64
    n_heads = 4
    seq_len = 6
    d_k = d_model // n_heads

    np.random.seed(42)
    token_ids = np.array([[15, 234, 89, 567, 2, 0]])
    token_labels = ["我", "喜欢", "学习", "大模型", "[EOS]", "[PAD]"]

    embedding = np.random.randn(vocab_size, d_model).astype(np.float32)
    pe = sinusoidal_positional_encoding(seq_len, d_model)
    x = token_embedding(token_ids, embedding) + pe[:seq_len, :]

    W_Q = np.random.randn(d_model, d_model).astype(np.float32) * 0.02
    W_K = np.random.randn(d_model, d_model).astype(np.float32) * 0.02
    W_V = np.random.randn(d_model, d_model).astype(np.float32) * 0.02

    Q = x @ W_Q
    K = x @ W_K
    Q = Q.reshape(1, seq_len, n_heads, d_k).transpose(0, 2, 1, 3)
    K = K.reshape(1, seq_len, n_heads, d_k).transpose(0, 2, 1, 3)

    scores = Q @ K.transpose(0, 1, 3, 2) / np.sqrt(d_k)
    causal_mask = np.triu(np.ones((seq_len, seq_len)) * -1e9, k=1)
    scores = scores + causal_mask
    scores = scores - scores.max(axis=-1, keepdims=True)
    weights = np.exp(scores) / np.exp(scores).sum(axis=-1, keepdims=True)

    # ASCII heatmap
    print("Attention Weights Heatmap (Head 1)")
    print("Rows = query position, Cols = key position")
    print()
    print(f"{'':12s}", end="")
    for label in token_labels:
        print(f"{label:>8s}", end="")
    print()

    for i, label_i in enumerate(token_labels):
        print(f"{label_i:12s}", end="")
        for j in range(seq_len):
            w = weights[0, 0, i, j]
            blocks = min(int(w * 40), 40)
            bar = "█" * blocks
            print(f" {bar:<8s}", end="") if blocks > 0 else print(f" {'·':<8s}", end="")
        print()

    print()
    print("█ = higher attention    · = masked (can't see future)")

    # Statistics
    print(f"\nPer-head attention entropy (higher = more spread out):")
    for h in range(n_heads):
        entropy = -np.sum(weights[0, h] * np.log(weights[0, h] + 1e-9)) / seq_len
        print(f"  Head {h+1}: {entropy:.3f}")

    # Note: with random weights, the pattern is meaningless
    print("\nNote: These weights are from random initialization — no meaningful pattern yet.")
    print("In a trained model, you'd see patterns like:")
    print("  - Next-token positions paying attention to previous tokens")
    print("  - Syntactic heads attending to nearby words")
    print("  - Semantic heads attending to related concepts across the sentence")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: 验证运行**

```powershell
cd phase2-transformer
python attention_viz.py
```

- [ ] **Step 3: Commit**

```bash
git add phase2-transformer/attention_viz.py
git commit -m "feat(phase2): add attention weights visualization"
```

---

### Task 3.3: 编写 Phase 2 — README

**Files:**
- Create: `phase2-transformer/README.md`
- Create: `phase2-transformer/requirements.txt`

- [ ] **Step 1: 编写 requirements.txt**

```
numpy>=1.24.0
```

- [ ] **Step 2: 编写 README**

```markdown
# Phase 2：模型如何"思考" — 手写 Transformer 前向传播

📌 **前置要求:** Phase 1（会用 API 调模型）

🎯 **学完你能回答:**
- Attention 机制的本质是什么？Q、K、V 分别做什么？
- 一个 token 从输入到输出经历了哪些步骤？
- 为什么 Transformer 能并行处理所有 token？
- 多头注意力（Multi-Head Attention）中每个"头"在做什么？

🗺️ **路线图:**
1. 跑 `transformer_annotated.py` — 看数据流的 shape 变化
2. 跑 `transformer.py` — 理解精简版的代码结构
3. 跑 `attention_viz.py` — 可视化 Attention 权重矩阵

📖 **核心内容:**

### Token 的旅程

```
"我爱学习" → Tokenizer → [15, 234, 89, 2]
  → Embedding 查表 → 每个 ID 变 64 维向量
  → + 位置编码 → 告诉模型"这是第几个字"
  → N 个 Transformer 层 → 每层 = Attention + FFN
  → LM Head → 预测下一个 token
```

### Attention: 一切的核心

```
Q (查询): "我想找什么？"
K (键):   "我有什么？"
V (值):   "我的实际内容"

Attention = softmax(Q·K^T / √d_k) · V

直觉：你在人群中找"谁懂 C++"
  Q = 你的需求 "找懂 C++ 的人"
  K = 每个人身上的标签
  V = 每个人能提供的实际帮助
  Attention = 找到标签最匹配的人，获取他的帮助
```

> 🧠 后端视角：Attention ≈ 数据库查询优化器的"索引查找"——Q 是查询条件，
> K 是索引键，V 是行数据。softmax(Q·K^T) 是"这个索引键和查询条件的匹配度"。

### 为什么 Transformer 能并行

RNN 必须按顺序处理：读完"我"→ 读"爱"→ 读"学"。
Transformer 一次性看全部 token，Attention 让每个位置直接"沟通"。
这就是它能训练得这么快、这么大的原因。

🏃 **动手环节:**

```powershell
pip install numpy
python transformer_annotated.py   # 教学版：看每一步的 shape
python transformer.py             # 精简版：看整体结构
python attention_viz.py           # 可视化 Attention 矩阵
```

### 实验：改参数看变化

1. 把 `n_heads` 从 4 改成 8，观察 shape 变化
2. 把 `n_layers` 从 2 改成 4，思考为什么输出 shape 不变
3. 把 `seq_len` 从 6 改成 10，观察 Attention 矩阵变大

✅ **验收题:**
- [ ] 能画出 Attention(Q, K, V) 的数据流图
- [ ] 能解释 Q、K、V 各自的角色
- [ ] 能运行 transformer_annotated.py 并说出每一步在做什么
- [ ] 知道"残差连接"解决了什么问题

🔗 **下一步:** Phase 3 — 本地部署：在你自己电脑上跑真正的模型
```

- [ ] **Step 3: Commit**

```bash
git add phase2-transformer/README.md phase2-transformer/requirements.txt
git commit -m "feat(phase2): add README and requirements"
```

---

### Task 3.4: 编写 Phase 2 — exercises

**Files:**
- Create: `phase2-transformer/exercises/01-attention-matrix.py`
- Create: `phase2-transformer/exercises/02-change-heads.py`
- Create: `phase2-transformer/exercises/03-trace-a-token.py`

- [ ] **Step 1: 编写练习 1 — 手填 Attention 矩阵**

```python
"""
练习 1：手算一个 Attention 矩阵

给定简化的 Q、K、V 值，手动计算 Attention 的输出。
跑完脚本后对比你的手算结果和程序输出。

提示：用纸笔一步步算。
  1. Q @ K^T
  2. ÷ sqrt(d_k)
  3. softmax (每行)
  4. @ V
"""

import numpy as np

# 简化设置：d_k=2, seq_len=3
Q = np.array([[[[1.0, 0.0],
                [0.0, 1.0],
                [1.0, 1.0]]]])  # (1, 1, 3, 2)

K = np.array([[[[1.0, 0.0],
                [0.0, 1.0],
                [1.0, 1.0]]]])  # (1, 1, 3, 2)

V = np.array([[[[1.0, 2.0],
                [3.0, 4.0],
                [5.0, 6.0]]]])  # (1, 1, 3, 2)

d_k = 2

print("Q =")
print(Q[0, 0])
print("\nK =")
print(K[0, 0])
print("\nV =")
print(V[0, 0])

print("\n" + "=" * 40)
print("第 1 步：Q @ K^T (注意力分数)")
scores = Q @ K.transpose(0, 1, 3, 2)
print(scores[0, 0])

print("\n第 2 步：÷ sqrt(d_k) = ÷", np.sqrt(d_k))
scores = scores / np.sqrt(d_k)
print(scores[0, 0])

print("\n第 3 步：Softmax (每行)")
scores = scores - scores.max(axis=-1, keepdims=True)
exp_scores = np.exp(scores)
attn_weights = exp_scores / exp_scores.sum(axis=-1, keepdims=True)
print(attn_weights[0, 0])
print("(验证：每行和应该 = 1)")
print("行和：", attn_weights[0, 0].sum(axis=-1))

print("\n第 4 步：加权求和 (× V)")
output = attn_weights @ V
print(output[0, 0])

print("\n✅ 对比你的手算结果，是否一致？")
print("  如果一致 → 你理解了 Attention 的计算过程")
print("  如果不一致 → 检查每一步，特别是在 softmax 之前有没有减去最大值")
```

- [ ] **Step 2: 编写练习 2 — 改头数观察变化**

```python
"""
练习 2：修改 n_heads，观察 shape 变化

运行 transformer_annotated.py，分别设 n_heads=2, 4, 8。
观察：d_k 怎么变？每个头的"视野"怎么变？
"""

import numpy as np

d_model = 64

for n_heads in [2, 4, 8]:
    d_k = d_model // n_heads
    print(f"n_heads={n_heads:2d}  →  d_k={d_k:2d}  "
          f"→ 每个头处理 {d_k}/{d_model} = {d_k/d_model:.0%} 的维度")
    print(f"         每个头的 Attention 矩阵: (seq_len, seq_len) 不变")
    print(f"         每个头的 Q/K/V 形状: (batch, seq_len, {d_k})")
    print()

print("思考题：")
print("1. 头数越多越好吗？为什么？")
print("2. d_k 太小会有什么问题？")
print("3. GPT-3 的 d_model=12288, n_heads=96, 每个 d_k=128。")
print("   为什么选这个组合？")
```

- [ ] **Step 3: 编写练习 3 — 跟踪一个 token**

```python
"""
练习 3：跟踪一个 token 的数据流

在 transformer_annotated.py 的输出中，找到 token ID=234 ("喜欢")
在每一层的 shape 变化，画出它的旅程。
"""

print("""
Token "喜欢" (ID=234) 的旅程：

  [输入]
  token_id = 234                                ← 一个整数
      │
  [Embedding]
  embedding[234] → shape=(64,)                   ← 稠密向量
      │
  [+ 位置编码]
  pe[1]         → shape=(64,)                   ← 加上"第2个位置"
  x[0, 1, :]    → shape=(64,)                   ← 输入序列的第2个token的表示
      │
  [Layer 1: LayerNorm → Multi-Head Attention]
  Q[0, :, 1, :] → shape=(n_heads, d_k)          ← 4个头各自的查询向量
  和所有 K 算相似度 → attention[0, :, 1, :]     ← 对每个位置的关注度
  加权取 V        → attn_out[0, 1, :]            ← shape=(64,)
  x[0, 1, :] + attn_out[0, 1, :]                ← 残差连接
      │
  [Layer 1: LayerNorm → FFN]
  ffn_out[0, 1, :] → shape=(64,)
  x[0, 1, :] + ffn_out[0, 1, :]                 ← 残差连接
      │
  [Layer 2: 同上流程]
      │
  [LM Head]
  logits[0, 1, :] → shape=(1000,)               ← 第2个位置对词汇表的预测
  argmax → 预测下一个 token ID

  真正生成时，我们只关心最后一个位置的预测。
  最后一个位置预测的下一个 token → 拼到序列末尾 → 再来一轮。
  这就是"逐字生成"。
""")
```

- [ ] **Step 4: Commit**

```bash
git add phase2-transformer/exercises/
git commit -m "feat(phase2): add exercises for attention and transformer"
```

---

### Task 3.5: 编写 Phase 3 — 实验脚本

**Files:**
- Create: `phase3-local-deploy/experiments/01-cpu-vs-gpu.py`
- Create: `phase3-local-deploy/experiments/02-context-length.py`
- Create: `phase3-local-deploy/experiments/03-quantization.py`
- Create: `phase3-local-deploy/experiments/common.py`

- [ ] **Step 1: 编写实验公共模块 common.py**

```python
"""
实验公共模块 — 调用 Ollama API 测量性能指标。
"""

import time
import sys
import json
import urllib.request
import urllib.error


def measure_ollama(base_url: str, model: str, prompt: str,
                   max_tokens: int = 256) -> dict:
    """测量一次 Ollama 推理的性能指标。"""
    t0 = time.perf_counter()
    first_token_at = None
    output_tokens = 0

    payload = json.dumps({
        "model": model,
        "messages": [
            {"role": "system", "content": "你是一个简洁的助手。"},
            {"role": "user", "content": prompt},
        ],
        "stream": True,
        "temperature": 0.7,
        "max_tokens": max_tokens,
    }).encode("utf-8")

    url = f"{base_url.rstrip('/')}/chat/completions"
    req = urllib.request.Request(
        url, data=payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": "Bearer ollama",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            for line in resp:
                text = line.decode("utf-8", errors="replace").strip()
                if not text.startswith("data:"):
                    continue
                data_str = text.removeprefix("data:").strip()
                if data_str == "[DONE]":
                    break
                try:
                    chunk = json.loads(data_str)
                except json.JSONDecodeError:
                    continue
                delta = chunk.get("choices", [{}])[0].get("delta", {}).get("content", "")
                if delta:
                    if first_token_at is None:
                        first_token_at = time.perf_counter()
                    output_tokens += 1
    except urllib.error.URLError as exc:
        return {"success": False, "error": str(exc.reason)}
    except Exception as exc:
        return {"success": False, "error": str(exc)}

    done_at = time.perf_counter()
    ft_ms = int((first_token_at - t0) * 1000) if first_token_at else None
    total_ms = int((done_at - t0) * 1000)
    tps = round(output_tokens / (total_ms / 1000), 2) if total_ms > 0 else 0

    return {
        "success": True,
        "first_token_ms": ft_ms,
        "total_ms": total_ms,
        "output_tokens": output_tokens,
        "tokens_per_sec": tps,
    }


TEST_PROMPT = "请用三句话解释什么是 KV Cache，每句不超过 20 个字。"
```

- [ ] **Step 2: 编写实验 1 — CPU vs GPU**

```python
"""
实验 1：GPU 加速到底有多大用？

改变 llama-server 的 -ngl 参数（0 / 20 / 99），
分别测量首 token 延迟和吞吐量。

前提：
  - Ollama 已安装并运行
  - 至少有一个模型（如 qwen2.5:7b）

运行：
  python 01-cpu-vs-gpu.py
"""

from common import measure_ollama, TEST_PROMPT

OLLAMA_URL = "http://localhost:11434/v1"

MODELS = {
    "qwen2.5:7b": "7B 参数模型",
    "qwen2.5:1.5b": "1.5B 参数模型（纯 CPU 也能跑）",
}


def main():
    print("=" * 60)
    print("实验 1：GPU 加速的效果")
    print("=" * 60)
    print("注意：这个实验测量的是 Ollama（底层已启用 GPU）的延迟。")
    print("要测纯 CPU，请修改 Ollama 配置或在另一台无 GPU 的机器上跑。")
    print()

    for model, desc in MODELS.items():
        print(f"\n测试模型：{model} ({desc})")
        print("-" * 40)

        for run in range(3):
            print(f"  第 {run + 1} 次...", end=" ", flush=True)
            result = measure_ollama(OLLAMA_URL, model, TEST_PROMPT)
            if result["success"]:
                print(f"首token={result['first_token_ms']}ms, "
                      f"总耗时={result['total_ms']}ms, "
                      f"{result['tokens_per_sec']} tok/s")
            else:
                print(f"失败: {result['error']}")

    print("\n结论：")
    print("  对于 7B 模型，纯 CPU 推理（-ngl 0）首 token 延迟通常 ≥ 5秒。")
    print("  启用 GPU 加速（-ngl 99）可以把延迟降到 ≤ 1秒。")
    print("  如果你的机器有 NVIDIA 显卡，去任务管理器确认 Ollama 在用 GPU。")


if __name__ == "__main__":
    main()
```

- [ ] **Step 3: 编写实验 2 — 上下文长度**

```python
"""
实验 2：上下文越长越慢吗？

用同一个 prompt，通过填充不同长度的 context 来模拟长对话。
实际场景中，可以观察长时间多轮对话的 total_ms 变化。

运行：
  python 02-context-length.py
"""

from common import measure_ollama

OLLAMA_URL = "http://localhost:11434/v1"
MODEL = "qwen2.5:7b"

PROMPTS = {
    "短": "你好（1 轮对话，约 10 token）",
    "中": "请用 C++ 后端工程师能理解的方式，解释大模型推理中的 KV Cache，并给一个网络服务类比",
    "长": ("请详细解释大模型推理中的以下 5 个概念，每个给一个 C++ 后端工程师能理解的类比："
           "1. KV Cache\n2. Attention 机制\n3. 量化\n4. 流式输出\n5. 上下文窗口"),
}


def main():
    print("=" * 60)
    print("实验 2：上下文长度对性能的影响")
    print("=" * 60)
    print("注意：这个实验通过不同长度的 prompt 来近似模拟。")
    print("真正的长上下文影响需要在多轮对话中观察 total_ms 增长。")
    print()

    for label, prompt in PROMPTS.items():
        print(f"\n{'─' * 40}")
        print(f"Prompt：{label}")
        print(f"内容：{prompt[:60]}...")
        print()

        for run in range(3):
            print(f"  第 {run + 1} 次...", end=" ", flush=True)
            result = measure_ollama(OLLAMA_URL, MODEL, prompt)
            if result["success"]:
                print(f"首token={result['first_token_ms']}ms, "
                      f"总耗时={result['total_ms']}ms")
            else:
                print(f"失败: {result['error']}")

    print("\n预期观察：")
    print("  Prompt 越长 → Prefill 越慢 → 首 token 延迟越大")
    print("  Decode 速度（tok/s）基本不变（瓶颈在 GPU 计算能力）")
    print("  去 Phase 3 的 main.py 里做 15 轮连续对话，")
    print("  观察 total_ms 随对话轮次的增长趋势——那才是 KV Cache 变大的效果。")


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: 编写实验 3 — 量化对比**

```python
"""
实验 3：量化等级对比

用不同量化等级的模型（Q2_K / Q4_K_M / Q8_0），
比较回答质量和延迟差异。

前提：需要有不同量化等级的 GGUF 文件。
如果你用 Ollama，ollama list 可以看到模型的量化信息。

运行：
  python 03-quantization.py
"""

from common import measure_ollama

OLLAMA_URL = "http://localhost:11434/v1"

# Ollama 中常见的模型量化变体
MODELS = [
    ("qwen2.5:1.5b", "1.5B Q4_K_M（默认量化）"),
    ("qwen2.5:7b", "7B Q4_K_M（默认量化）"),
]

QUALITY_PROMPT = "请用三句话解释什么是注意力机制（Attention），每句不超过 20 个字。"


def main():
    print("=" * 60)
    print("实验 3：量化等级对回答质量的影响")
    print("=" * 60)
    print()

    for model, desc in MODELS:
        print(f"\n模型：{desc}")
        print("-" * 40)

        for run in range(2):
            print(f"  第 {run + 1} 次...")
            result = measure_ollama(OLLAMA_URL, model, QUALITY_PROMPT)
            if result["success"]:
                print(f"    首token={result['first_token_ms']}ms, "
                      f"总耗时={result['total_ms']}ms, "
                      f"{result['tokens_per_sec']} tok/s")
            else:
                print(f"    失败: {result['error']}")

    print("\n总结：")
    print("  Q2_K (3GB)  → 文件最小，但回答质量明显下降（可能胡说）")
    print("  Q4_K_M (4.5GB) → 甜点级别：体积和质量的最佳平衡")
    print("  Q8_0 (7.5GB) → 接近原版质量，但文件大了很多")
    print()
    print("  如果 Ollama 只有 Q4_K_M，可以在 Hugging Face 下载不同量化的 GGUF 文件")
    print("  然后用 llama.cpp 直接加载对比。")


if __name__ == "__main__":
    main()
```

- [ ] **Step 5: Commit**

```bash
git add phase3-local-deploy/experiments/
git commit -m "feat(phase3): add automated experiment scripts for local deployment"
```

---

### Task 3.6: 编写 Phase 3 — kv_cache_viz.py

**Files:**
- Create: `phase3-local-deploy/kv_cache_viz.py`

- [ ] **Step 1: 编写 KV Cache 可视化**

```python
"""Visualize KV Cache size growth with context length."""

def main():
    print("KV Cache 大小随上下文长度增长")
    print("=" * 50)
    print()
    print("以 Qwen2.5-7B 为例（28 层, 28 头, d_head=128, FP16=2bytes）：")
    print()
    print("公式：KV ≈ 2 × n_layers × n_heads × d_head × 2bytes × n_tokens")
    print()

    n_layers = 28
    n_heads = 28
    d_head = 128
    bytes_per_element = 2  # FP16

    kv_per_token = 2 * n_layers * n_heads * d_head * bytes_per_element
    kv_per_token_mb = kv_per_token / (1024 * 1024)

    print(f"每个 token 的 KV Cache：{kv_per_token:,} bytes = {kv_per_token_mb:.2f} MB")
    print()
    print(f"{'上下文长度':<15} {'KV Cache 大小':<20} {'累计显存估算':<20}")
    print("-" * 55)

    model_size_gb = 4.5  # Q4_K_M 约 4.5GB

    for ctx in [512, 1024, 2048, 4096, 8192, 16384, 32768]:
        kv_gb = (kv_per_token * ctx) / (1024 ** 3)
        total_gb = model_size_gb + kv_gb
        bar = "█" * int(kv_gb * 10)
        print(f"{ctx:<15} {kv_gb:>6.2f} GB {bar:<20} {total_gb:>6.2f} GB")

    print()
    print("观察：")
    print("  - 上下文翻倍 → KV Cache 翻倍（线性增长）")
    print("  - 7B Q4_K_M 在 8GB 显卡上：上下文最好不要超过 4096")
    print("  - 这就是为什么长上下文模型贵——显存消耗极快")
    print()
    print("显存估算对照：")
    print(f"  RTX 3060 (12GB)：够跑 4096 ctx，8192 可能不够")
    print(f"  RTX 4090 (24GB)：轻松跑 8192 ctx，16384 需要优化")
    print(f"  A100 (80GB)：    可以跑 32768+ ctx")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Commit**

```bash
git add phase3-local-deploy/kv_cache_viz.py
git commit -m "feat(phase3): add KV Cache size visualization"
```

---

## 阶段 4：内容补充

### Task 4.1: 编写各 Phase README

**Files:**
- Create: `phase0-fundamentals/README.md`
- Create: `phase3-local-deploy/README.md`
- Create: `phase4-apps/rag/README.md` (update existing stub)
- Create: `phase4-apps/agent/README.md` (update existing stub)
- Create: `phase5-customize/finetune/README.md` (update existing stub)
- Create: `phase6-production/README.md` (update existing stub)
- Create: `phase7-source/README.md`

- [ ] **Step 1: 编写 phase0-fundamentals/README.md**

```markdown
# Phase 0：基础认知 — 30 分钟建立心智模型

📌 **前置要求:** 无

🎯 **学完你能回答:**
- LLM 是什么？和搜索引擎有什么区别？
- Token、Temperature、上下文窗口、幻觉是什么意思？
- 一次对话在底层发生了什么？

🗺️ **路线图:**
1. 读 `docs/start-here.md` — 30 分钟叙事指南
2. 遇到困惑查 `docs/faq.md` — 20 个常见问题
3. 想深挖读 `docs/concepts/` — 4 篇概念解析

📖 **核心内容:**

见 `docs/start-here.md`。这篇指南覆盖了：
- LLM 的最简定义（预测引擎）
- Tokenizer 怎么把话变成数字
- Embedding 怎么让意思相近的词"位置接近"
- Transformer 怎么"理解"上下文
- 训练的三个阶段（预训练 → SFT → RLHF）
- LLM 做不到的事（幻觉、数学差、知识截止）
- 三种使用方式（网页/API/本地）

✅ **验收题:**
- [ ] 能用自己的话解释 LLM 是什么，不超过 3 句话
- [ ] 知道 token、temperature、上下文窗口、幻觉的含义
- [ ] 准备好了就开始 Phase 1

🔗 **下一步:** Phase 1 — 亲手调 API
```

- [ ] **Step 2: 编写 phase3-local-deploy/README.md**

```markdown
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
```

- [ ] **Step 3: 编写 phase7-source/README.md**

```markdown
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
```

- [ ] **Step 4: Commit**

```bash
git add phase0-fundamentals/README.md phase3-local-deploy/README.md phase7-source/README.md
git commit -m "docs: add README for Phase 0, 3, and 7"
```

---

### Task 4.2: 编写各 Phase exercises

本 task 创建 exercises 目录的 README 和剩余练习文件。

**Files:**
- Create: `phase1-api/exercises/01-temperature-contrast.md`
- Create: `phase1-api/exercises/02-batch-qa.md`
- Create: `phase4-apps/rag/exercises/01-switch-docs.md`
- Create: `phase4-apps/agent/exercises/01-add-tool.md`
- Create: `phase5-customize/finetune/exercises/01-system-prompt.md`
- Create: `phase6-production/exercises/01-find-bottleneck.md`

- [ ] **Step 1: 创建 phase1-api exercises**

`phase1-api/exercises/01-temperature-contrast.md`:
```markdown
# 练习 1：Temperature 对比实验

**目标：** 理解 temperature 对输出风格的影响

**步骤：**
1. 打开 `config.example.toml`，复制为 `config.toml`
2. 分别设 temperature = 0.1, 0.5, 0.9, 1.2
3. 每次用同样的 prompt："请写一首关于程序员的五言绝句"
4. 记录每次的输出差异

**观察：**
- temperature=0.1：输出稳定、保守、每次几乎一样
- temperature=0.5：适中的创造性和确定性平衡
- temperature=0.9：更多样化、可能有意外
- temperature=1.2：可能"放飞"，出现不连贯

**思考：**
- 为什么写代码要用低 temperature？
- 为什么头脑风暴要用高 temperature？
```

`phase1-api/exercises/02-batch-qa.md`:
```markdown
# 练习 2：批量问答脚本

**目标：** 写一个脚本批量处理多个问题

**步骤：**
1. 准备一个问题列表文件 `questions.txt`（每行一个问题）
2. 写一个 Python 脚本 `batch_qa.py`，读取文件，对每个问题调用 API
3. 把回答保存到 `answers/` 目录，文件名 = 问题编号 + 时间戳
4. 打印汇总：总共 X 个问题，总耗时 Y 秒，平均首 token 延迟 Z ms

**提示：**
- 复用 main.py 的 `stream_chat()` 逻辑，去掉交互循环
- 只发单轮请求（messages 只含 system + 一个 user message）
```

- [ ] **Step 2: 创建 phase4-apps exercises**

`phase4-apps/rag/exercises/01-switch-docs.md`:
```markdown
# 练习 1：换一个文档库

**目标：** 理解 RAG 的效果取决于文档内容

**步骤：**
1. 复制 `rag.py` 为 `rag_custom.py`
2. 改 `load_sample_document()` 函数，换成你自己感兴趣的内容
   - 比如你公司的内部文档
   - 或者一本你喜欢的技术书的目录
   - 或者某个开源项目的 README
3. 用 `--compare` 对比 RAG 和无 RAG 的差异

**观察：**
- 当文档包含答案时，RAG 回答准不准？
- 当文档不包含答案时，RAG 会说"不知道"还是硬编？
```

`phase4-apps/agent/exercises/01-add-tool.md`:
```markdown
# 练习 1：给 Agent 加一个新工具

**目标：** 理解 Agent 的 Tool 定义格式

**步骤：**
1. 复制 `agent.py` 为 `agent_custom.py`
2. 按以下模板加一个新工具（比如"读取文件内容"）：

```python
{
    "type": "function",
    "function": {
        "name": "read_file",
        "description": "读取指定文件的内容",
        "parameters": {
            "type": "object",
            "properties": {
                "filepath": {
                    "type": "string",
                    "description": "要读取的文件路径",
                },
            },
            "required": ["filepath"],
        },
    },
}
```

3. 实现 `tool_read_file(filepath: str) -> str` 函数
4. 在 `TOOL_MAP` 里注册新工具
5. 运行 `agent_custom.py`，问"帮我读一下 requirements.txt 的内容"

**观察：**
- LLM 怎么知道什么时候该用 read_file 而不是 calculator？
- 一个 Agent 可以同时有 5 个工具——LLM 会自己选
```

- [ ] **Step 3: 创建 phase5-customize exercises**

`phase5-customize/finetune/exercises/01-system-prompt.md`:
```markdown
# 练习 1：设计并验证一个 System Prompt

**目标：** 让模型稳定输出你想要的风格

**步骤：**
1. 选择一个"角色"：代码审查员 / 技术文档翻译 / API 设计顾问
2. 写一个 system prompt（参考 `docs/guides/prompt-engineering.md`）
3. 准备 10 个测试问题
4. 跑 10 轮对话，不修改 system prompt
5. 检查输出：风格是否一致？有没有偏离角色？

**评分标准：**
- 10/10 保持一致 → system prompt 设计优秀
- 7-9/10 保持一致 → 基本可用，个别情况需要补充约束
- <7/10 保持一致 → 需要加更多约束（格式、角色、不要什么）
```

- [ ] **Step 4: 创建 phase6-production exercises**

`phase6-production/exercises/01-find-bottleneck.md`:
```markdown
# 练习 1：找出并发瓶颈

**目标：** 用 loadtest.py 找到你系统能承受的并发上限

**步骤：**
1. 启动 gateway：
   ```powershell
   $env:DEEPSEEK_API_KEY="sk-..."
   python gateway.py
   ```

2. 在另一个终端跑压测（逐步加大并发）：
   ```powershell
   python loadtest.py --concurrency 1 --requests 5
   python loadtest.py --concurrency 5 --requests 10
   python loadtest.py --concurrency 10 --requests 20
   python loadtest.py --concurrency 20 --requests 20
   ```

3. 记录每次的 P50/P95/P99 延迟和错误率

4. 找出拐点——延迟从哪个并发量开始飙升？

**交付：** 画一张"并发量 vs P95 延迟"的曲线（Excel/手绘都行）
```

- [ ] **Step 5: Commit**

```bash
git add phase1-api/exercises/ phase4-apps/rag/exercises/ phase4-apps/agent/exercises/ phase5-customize/finetune/exercises/ phase6-production/exercises/
git commit -m "feat: add exercises for phases 1, 4, 5, and 6"
```

---

### Task 4.3: 编写 projects/ 综合实战大纲

**Files:**
- Create: `projects/01-personal-knowledge-base/README.md`
- Create: `projects/02-code-review-bot/README.md`

- [ ] **Step 1: 编写 project 1**

```markdown
# 综合实战 1：个人知识库问答系统

**综合 Phase:** 1 (API) + 4 (RAG)

**目标：** 搭建一个能回答你私人问题的 RAG 系统

**要求：**
1. 收集至少 5 篇与你工作/学习相关的文档（Markdown/TXT）
2. 用 Phase 4 的 RAG 代码做文档索引
3. 换更好的 embedding 模型（如 bge-large-zh-v1.5）
4. 设计 10 个测试问题，对比有/无 RAG 的回答差异
5. 优化 chunk_size——找到一个让检索最准的值

**扩展（可选）：**
- 用 Phase 6 的 gateway 对外暴露 HTTP API
- 加 cost.py 追踪每次查询的费用
- 定时更新文档库（自动化索引更新）
```

- [ ] **Step 2: 编写 project 2**

```markdown
# 综合实战 2：AI 代码审查 Bot

**综合 Phase:** 1 (API) + 4 (Agent) + 5 (Prompt) + 6 (Gateway)

**目标：** 搭建一个自动审查 Pull Request 的 Bot

**要求：**
1. 用 Phase 5 的 prompt engineering 设计一个"代码审查员"system prompt
2. 用 Phase 6 的 gateway 对外暴露 `/review` HTTP API
3. 接受一段代码，返回审查意见（安全 → 性能 → 可读性）
4. 用 Phase 6 的 logger.py 记录每次审查请求
5. 可选：用 Agent 模式添加"自动修复建议"功能

**API 设计：**
```
POST /review
Body: {"code": "...", "language": "python"}
Response: {"issues": [...], "suggestions": [...]}
```
```

- [ ] **Step 3: Commit**

```bash
git add projects/
git commit -m "feat: add cross-phase capstone project outlines"
```

---

### Task 4.4: 编写 docs/appendix/ 内容

**Files:**
- Create: `docs/appendix/glossary.md`
- Create: `docs/appendix/troubleshooting.md`
- Create: `docs/appendix/resources.md`

- [ ] **Step 1: 编写 glossary.md**

从 `LEARNING-PATH.md` 的附录 A 中提取术语表，单独成文：

```markdown
# 术语速查表

| 术语 | 一句话解释 |
|------|-----------|
| **API** | 应用程序接口——你发请求，服务器返回结果 |
| **API Key** | 你的身份凭证——证明"是你，你可以用" |
| **Attention** | Transformer 的核心机制——让每个 token 关注其他相关 token |
| **Context Window** | 模型一次能"看到"的最大 token 数 |
| **Decode** | 推理第二阶段：逐 token 生成输出 |
| **Embedding** | 把文字变成一串数字，语义相近的文字数字也相近 |
| **GGUF** | llama.cpp 用的模型文件格式，量化后的模型打包 |
| **Hallucination** | 模型自信地说出错误信息 |
| **JSONL** | JSON Lines——每行一个独立 JSON，适合日志 |
| **KV Cache** | 推理时的"草稿纸"——缓存中间计算结果 |
| **LLM** | Large Language Model，大语言模型 |
| **LoRA** | Low-Rank Adaptation——低成本微调方法 |
| **Ollama** | 让你在个人电脑上轻松运行 LLM 的工具 |
| **OpenAI-Compatible API** | 一套"行业标准"的接口规范 |
| **Prefill** | 推理第一阶段：一次性处理全部输入 |
| **Prompt** | 你发给模型的指令/问题 |
| **Quantization** | 降低权重精度以节省空间——类似图片压缩 |
| **RAG** | Retrieval-Augmented Generation——搜索+生成 |
| **SSE** | Server-Sent Events——服务器推送流式数据 |
| **SDK** | 软件开发工具包——封装好的代码库 |
| **System Prompt** | 给模型设定的"人格" |
| **Temperature** | 控制输出随机性（0=死板，1=放飞） |
| **Token** | 模型的最小处理单元，≈0.75 个中文字 |
| **TOML** | 一种配置文件格式，比 JSON 更适合人类读写 |
| **Transformer** | 现代 LLM 的基础架构（2017 年论文提出） |
```

- [ ] **Step 2: 编写 troubleshooting.md**

从 `LEARNING-PATH.md` 附录 B 提取：

```markdown
# 常见问题排查

| 问题 | 可能原因 | 解决办法 |
|------|---------|---------|
| `认证失败` | API Key 没设置或已过期 | 检查 `$env:DEEPSEEK_API_KEY` |
| `网络连接失败` | 没开代理/VPN，或 base_url 写错 | 检查 config.toml 的 base_url |
| `请求超时` | 网络不稳定或模型响应太慢 | 重试，或换更快的模型 |
| Ollama 下载模型很慢 | 国内网络问题 | 用镜像站，或手动下载 GGUF |
| `CUDA out of memory` | 显存不够 | 减小 -c，或用更小的模型 |
| `ModuleNotFoundError` | 没装依赖 | `pip install -r requirements.txt` |
| llama.cpp 编译失败 | 缺 CMake 或 C++ 编译器 | 参考 phase3-local-deploy/getting-started.md |
| Ollama 模型回答很慢 | 纯 CPU 推理 | 检查有没有 GPU，GPU 有没有被 Ollama 用 |
```

- [ ] **Step 3: 编写 resources.md**

```markdown
# 推荐阅读和资源

## 必读（免费在线）

- [The Illustrated Transformer](https://jalammar.github.io/illustrated-transformer/) — 图解 Transformer，60 张图
- [Andrej Karpathy — Let's build GPT from scratch](https://www.youtube.com/watch?v=kCc8FmEb1nY) — 2h 视频，手写 GPT
- [Hugging Face NLP Course](https://huggingface.co/learn/nlp-course) — 第 1-3 章，理解 tokenizer + 模型
- [Illustrated RLHF](https://huggingface.co/blog/rlhf) — RLHF 图解

## 推荐视频

- [3Blue1Brown — Attention in transformers, visually explained](https://www.youtube.com/watch?v=eMlx5fFNoYc) — 26min
- [StatQuest — Transformer Neural Networks](https://www.youtube.com/watch?v=zxQyTK8quyY) — 循序渐进

## 论文（最后看）

- "Attention Is All You Need" (Vaswani et al., 2017)
- "LoRA: Low-Rank Adaptation of Large Language Models" (Hu et al., 2021)

## 工具

- [OpenAI Tokenizer](https://platform.openai.com/tokenizer) — 在线看 token 化结果
- [Ollama](https://ollama.com) — 本地模型管理
- [llama.cpp](https://github.com/ggerganov/llama.cpp) — C++ 推理引擎
```

- [ ] **Step 4: Commit**

```bash
git add docs/appendix/
git commit -m "docs: add glossary, troubleshooting, and resources appendix"
```

---

## 阶段 5：质量收尾

### Task 5.1: 更新根目录 README

**Files:**
- Modify: `README.md`

- [ ] **Step 1: 重写 README 反映新结构**

```markdown
# LLM 从零到精通 — 动手实战学习路径

> 零基础、不啃论文、不背公式。先跑起来，再理解原理。
> 30 分钟建立完整认知 → 7 个 Phase 逐步深入 → 成为 LLM 工程专家。

---

## 快速开始

```powershell
# 0. 检查环境
python tools/check_env.py

# 1. 获取 API Key（platform.deepseek.com 免费注册）
$env:DEEPSEEK_API_KEY = "sk-你的key"

# 2. 装依赖 + 跑第一次对话
cd phase1-api
pip install -r requirements.txt
python main.py --config config.example.toml
```

输入问题，看屏幕上逐字出现回答。你刚完成了一次 LLM API 调用。

---

## 学习路径

```
Phase 0  基础认知        30 分钟纯阅读，建立心智模型
   ↓
Phase 1  API 精通        调 SDK、手写 HTTP、多 provider benchmark
   ↓
Phase 2  模型内部        纯 numpy 手写 Transformer 前向传播 ★
   ↓
Phase 3  本地部署        Ollama、llama.cpp、KV Cache、量化实验
   ↓
Phase 4  应用构建        RAG 检索增强 + Agent 智能体
   ↓
Phase 5  模型定制        Prompt Engineering + LoRA 微调
   ↓
Phase 6  生产上线        日志、成本、压测、网关
   ↓
Phase 7  源码深水区      llama.cpp C++ 源码阅读（可选）
```

详见 `docs/learning-path.md`。

---

## 三条阅读路线

| 你想要 | 读这个 | 时间 |
|--------|--------|------|
| **先搞懂 LLM 到底是什么** | `docs/start-here.md` | 30 分钟 |
| **直接开始系统学习** | `docs/learning-path.md` | 7 Phase 课程表 |
| **遇到困惑查一下** | `docs/faq.md` | 随时 |

---

## 项目结构

```
├── README.md                    ← 项目入口
├── CLAUDE.md                    ← Claude Code 配置
├── .gitignore
├── .github/workflows/           ← CI
│
├── docs/                        ← 📚 全部阅读材料
│   ├── start-here.md
│   ├── learning-path.md
│   ├── faq.md
│   ├── concepts/                ← Token/Embedding/Training/架构
│   ├── guides/                  ← Prompt Engineering 手册
│   └── appendix/                ← 术语表/排错/资源
│
├── phase0-fundamentals/         ← Phase 0：基础认知
├── phase1-api/                  ← Phase 1：API 精通
├── phase2-transformer/          ← Phase 2：Transformer 内部
├── phase3-local-deploy/         ← Phase 3：本地部署
├── phase4-apps/                 ← Phase 4：RAG + Agent
├── phase5-customize/            ← Phase 5：Prompt + LoRA
├── phase6-production/           ← Phase 6：日志/成本/网关
├── phase7-source/               ← Phase 7：llama.cpp 源码
│
├── projects/                    ← 🔗 综合实战
├── tools/                       ← 辅助工具
```

---

## 设计原则

- **Provider-agnostic**: 一个客户端，只改配置切换 DeepSeek/Ollama/Proxy
- **Minimal dependencies**: 早期 Phase 尽量少装包
- **Measurable learning**: 每次调用输出 `first_token_ms` 和 `total_ms`
- **Progressive complexity**: 每层的难度递增，没有跳跃
```

- [ ] **Step 2: Commit**

```bash
git add README.md
git commit -m "docs: rewrite README for new 7-phase structure"
```

---

### Task 5.2: 更新 CLAUDE.md

**Files:**
- Modify: `CLAUDE.md`

- [ ] **Step 1: 更新 CLAUDE.md 中的路径引用**

需要把 CLAUDE.md 中所有旧的路径引用更新为新路径。主要变更：

- Phase 编号全部更新（Phase 1-6 → Phase 0-7）
- 文件路径更新（`concepts/` → `docs/concepts/` 等）
- 运行命令中的路径更新

- [ ] **Step 2: Commit**

```bash
git add CLAUDE.md
git commit -m "docs: update CLAUDE.md for new project structure"
```

---

### Task 5.3: 最终验证

- [ ] **Step 1: 确认所有文件编译通过**

```powershell
Get-ChildItem -Path "G:\AI学习路径" -Recurse -Filter "*.py" |
  Where-Object { $_.FullName -notmatch '\\.git|__pycache__|\\.claude' } |
  ForEach-Object {
    python -m py_compile $_.FullName 2>&1
    if ($LASTEXITCODE -ne 0) {
      Write-Host "FAIL: $($_.FullName)" -ForegroundColor Red
    }
  }
```

- [ ] **Step 2: 确认文件结构符合 spec**

```powershell
# 验证关键目录存在
$paths = @(
    "docs/concepts", "docs/guides", "docs/appendix",
    "phase0-fundamentals",
    "phase1-api", "phase2-transformer", "phase3-local-deploy",
    "phase4-apps/rag", "phase4-apps/agent",
    "phase5-customize/finetune",
    "phase6-production", "phase7-source",
    "projects/01-personal-knowledge-base", "projects/02-code-review-bot",
    "tools", ".github/workflows"
)
foreach ($p in $paths) {
    $exists = Test-Path "G:\AI学习路径\$p"
    Write-Host ("[{0}] {1}" -f $(if ($exists) { "OK" } else { "MISSING" }), $p)
}
```

- [ ] **Step 3: 确认残留文件已删除**

```powershell
$residuals = @(
    "api调用实战", "howto",
    "meta-original-prompt.md", "meta-plan-artifact.md", "meta-short-video-draft.md",
    "START-HERE.md", "LEARNING-PATH.md", "FAQ.md",
    "concepts", "guides",
    "phase2-inference", "phase3-frameworks", "phase4-finetuning",
    "phase5-production", "phase6-advanced",
    "phase1-api/cli-chat", "phase1-api/ollama"
)
foreach ($r in $residuals) {
    $exists = Test-Path "G:\AI学习路径\$r"
    if ($exists) { Write-Host "RESIDUAL: $r 应该被删除" -ForegroundColor Yellow }
}
```

- [ ] **Step 4: 验证 .gitignore 生效**

```powershell
git status --short
# 确认 config.toml、conversations/、logs/ 不显示为 untracked
```

- [ ] **Step 5: 运行 smoke test**

```powershell
cd phase2-transformer
pip install numpy
python transformer.py
# 预期：正常输出 transformer demo

cd ../phase6-production
python -m py_compile logger.py cost.py gateway.py
# 预期：无错误
```

- [ ] **Step 6: 最终 commit**

```bash
git add -A
git commit -m "chore: final verification and cleanup"
```

---

## 实现顺序

```
阶段 1 (Task 1.1-1.4) → 基础就绪
阶段 2 (Task 2.1-2.6) → 文件全部在新位置
阶段 3 (Task 3.1-3.6) → Phase 2/3 新代码完
阶段 4 (Task 4.1-4.4) → README + exercises + appendix
阶段 5 (Task 5.1-5.3) → 收尾验证

每个 Task commit 一次。每个阶段结束时确保 `git status` 干净。
```

## 安全注意事项

1. **main.py 第 25 行硬编码了 API Key** `sk-你的key` — Task 2.6 Step 3 已修复。**建议用户立即去 DeepSeek 平台 revoke 旧 key（如果曾泄露）。**
2. 所有 `.toml` 文件（除 `*.example.toml`）已被 `.gitignore` 排除
3. `conversations/` 和 `logs/` 目录已被 `.gitignore` 排除
