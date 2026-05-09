# LoRA 微调 Demo — 纯小白版

> Phase 4：让模型学会你想要的说话方式——不需要从头训练

---

## 一句话理解

微调 = 给一个已经训练好的模型"补课"。

模型已经在互联网上读了海量文本（预训练），什么都会一点。但如果你想要它用特定的风格说话——比如"回答要简洁，不超过三句话"——你需要给它补补课。LoRA 就是一种极低成本的补课方式。

---

## LoRA 是什么

```
原始模型（十亿参数，全冻结）           LoRA 新增（约 1% 参数，只训练这个）
┌────────────────────────┐          ┌──────────────────┐
│  巨大的权重矩阵          │          │  两个小矩阵 A × B  │
│  不动、不训练            │    +     │  rank=8           │
│  就像一本已经印好的书     │          │  参数占比 < 1%    │
└────────────────────────┘          └──────────────────┘

结果：原书内容没变，但贴了几张便利贴——阅读体验变了。
```

**为什么这很重要：** 不需要几百张 GPU 训练几个月。一张消费级显卡（4GB 显存），几 MB 训练数据，几分钟到几十分钟就完成。

---

## 项目文件

| 文件 | 做什么 | 你学到什么 |
|------|--------|-----------|
| `prepare_data.py` | 生成 200 条训练数据（JSONL 格式） | 训练数据长什么样 |
| `train.py` | 跑 QLoRA 微调（4bit 量化版 LoRA） | 训练的实际流程 |
| `inference.py` | 微调前后对比 | 微调到底改了什么 |

---

## 安装

```powershell
cd phase4-finetuning/finetune

# 建议用单独虚拟环境（依赖比较多）
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

> 主要依赖：`torch`, `transformers`, `peft`, `bitsandbytes`, `trl`, `datasets`。大约需要 3-5 GB 磁盘空间。

---

## 三步走

### 第 1 步：生成训练数据

```powershell
python prepare_data.py
# 输出：train_data.jsonl（200 条对话数据）

# 偷看一眼数据长什么样
python -c "import json; print(json.loads(open('train_data.jsonl').readline())['messages'][1]['content'][:200])"
```

每条数据就是一个对话：
```json
{
  "messages": [
    {"role": "user", "content": "什么是内存泄漏？"},
    {"role": "assistant", "content": "分配的内存没释放。用智能指针避免。"}
  ]
}
```

你可以修改 `prepare_data.py`，换成你自己想要的对话风格——比如"用幽默的语气回答"或"每条回答都用 Markdown 格式"。

### 第 2 步：训练

```powershell
# 基础用法（需要 NVIDIA GPU ≥ 4GB 显存）
python train.py --model-name Qwen/Qwen2.5-1.5B-Instruct

# 显存不够？减小批次
python train.py --model-name Qwen/Qwen2.5-1.5B-Instruct --batch-size 2

# 实在没 GPU？用 CPU（非常慢，1-2 小时）
python train.py --use-cpu
```

**训练时间参考：**

| 硬件 | 模型大小 | 数据量 | 大约时间 |
|------|---------|--------|---------|
| RTX 3060 (12GB) | 1.5B | 200 条 | 3-5 分钟 |
| RTX 3060 (12GB) | 7B | 200 条 | 15-20 分钟 |
| 纯 CPU (16 核) | 1.5B | 200 条 | 1-2 小时 |

训练过程会输出 loss 值（越低越好，代表模型在"学会"）。如果 loss 一直不降——数据有问题，或者学习率不对。

### 第 3 步：看效果

```powershell
# 自动对比微调前后
python inference.py

# 问一个具体问题
python inference.py --query "什么是 RAII？"

# 只看微调前
python inference.py --base-only

# 只看微调后
python inference.py --lora-only
```

---

## 重要概念速查

| 概念 | 一句话 |
|------|--------|
| **LoRA** | 冻结原模型，只训练新增的小矩阵（约 1% 参数） |
| **QLoRA** | LoRA + 4bit 量化——显存需求再降 4 倍 |
| **Rank (r)** | LoRA 矩阵的大小，8-16 通常够；越大越强但也越慢 |
| **Alpha** | 控制 LoRA 的影响强度，通常是 rank 的 2 倍 |
| **Epoch** | 把全部训练数据过一遍 = 1 个 epoch |
| **过拟合** | 模型把训练数据"背下来"了，碰到新问题反而答不好 |
| **灾难性遗忘** | 微调过度，模型忘了原本会的东西 |

---

## 硬件要求

| 模型大小 | 方法 | 最低显存 | 实用建议 |
|----------|------|---------|---------|
| 1.5B | QLoRA (4bit) | 4 GB | 大部分游戏本都能跑 |
| 7B | QLoRA (4bit) | 8 GB | RTX 3060/4060 以上 |
| 7B | LoRA (16bit) | 16 GB | RTX 4080/4090 |
| 13B | QLoRA (4bit) | 16 GB | 需要高端显卡 |

> 没有独显？可以用 Google Colab 免费 GPU（搜索 "Colab QLoRA tutorial"）。

---

## 我们让模型学了什么

训练数据的目标是让模型用**简洁的工程师风格**回答：

**微调前（啰嗦版）：**
> RAII 是 Resource Acquisition Is Initialization 的缩写，这是一种 C++ 编程中的重要设计模式，它的核心思想是将资源的获取和释放与对象的生命周期绑定...

**微调后（简洁版）：**
> 资源获取即初始化。构造函数拿资源，析构函数释放。
> ```cpp
> std::lock_guard<std::mutex> lock(m);
> ```

---

## 试试你自己的数据

跑通默认数据后，最有价值的下一步是**换你自己的数据**：

1. 修改 `prepare_data.py`，把问答内容换成你想要的风格
2. 收集 50-200 条对话（数据越多效果越好，但 50 条也能看到变化）
3. 重新训练
4. 用 `inference.py --query` 对比效果

---

## 常见问题

| 问题 | 原因 | 解决 |
|------|------|------|
| `CUDA out of memory` | 显存不够 | 减小 `--batch-size`，或换 1.5B 模型 |
| `bitsandbytes not found` | 没装好 | `pip install bitsandbytes`；Windows 可能需要从源码装 |
| 训练完模型回答反而更差了 | 过拟合 | 减少 epoch（`--num-epochs 1`），或增加数据量 |
| loss 一直不降 | 学习率不对或数据有问题 | 试试 `--lora-r 16`，或检查数据格式 |
| CPU 训练慢到忍不了 | CPU 本来就不适合训练 | 用 Google Colab 免费 GPU |
