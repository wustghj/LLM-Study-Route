"""
train.py — LoRA 微调训练脚本

使用 QLoRA 在消费级 GPU 上微调小模型。
核心概念：
  - LoRA：冻结原始权重，训练新增的小矩阵（约原始参数量的 1%）
  - QLoRA：在 LoRA 基础上把原始模型量化到 4bit，进一步降低显存
  - 训练完成后可以合并权重或单独保存 LoRA 权重

依赖：
    pip install torch transformers accelerate peft bitsandbytes trl

用法：
    # 1. 先生成训练数据
    python prepare_data.py

    # 2. 开始训练
    python train.py --model-name Qwen/Qwen2.5-1.5B-Instruct

    # 3. 推理对比
    python inference.py

显存需求：
  - Qwen2.5-1.5B + QLoRA（4bit）：约 4-6 GB 显存
  - 如果没有 GPU，可以用 --use-cpu 参数（但会非常慢）
"""

import json
import os
import sys
import time
from dataclasses import dataclass, field
from typing import Optional

import torch


# =========================================================================
# 配置参数（可以直接修改，也可以用命令行覆盖）
# =========================================================================

@dataclass
class TrainingConfig:
    # 模型
    model_name: str = "Qwen/Qwen2.5-1.5B-Instruct"

    # LoRA 参数
    lora_r: int = 8              # LoRA rank（越高越强，但越大）
    lora_alpha: int = 16         # LoRA alpha（缩放系数）
    lora_dropout: float = 0.05   # 防过拟合

    # 训练参数
    batch_size: int = 4
    learning_rate: float = 2e-4
    num_epochs: int = 3
    max_seq_length: int = 512

    # 数据
    data_path: str = "train_data.jsonl"

    # 输出
    output_dir: str = "lora_output"

    # 硬件
    use_cpu: bool = False        # 没用 GPU 时强制用 CPU


def print_memory_usage():
    """打印当前 GPU 显存占用"""
    if torch.cuda.is_available():
        allocated = torch.cuda.memory_allocated() / 1024**3
        reserved = torch.cuda.memory_reserved() / 1024**3
        print(f"[显存] 已分配: {allocated:.2f} GB, 已预留: {reserved:.2f} GB")


def train(config: TrainingConfig):
    """
    使用 QLoRA 微调模型。

    流程：
      1. 加载 4bit 量化模型（bitsandbytes）
      2. 在模型上插入 LoRA 适配器
      3. 加载训练数据（对话格式）
      4. 训练（只训练 LoRA 参数）
      5. 保存 LoRA 权重
    """

    # =========================================================
    # 1. 检测硬件
    # =========================================================
    if config.use_cpu or not torch.cuda.is_available():
        device = "cpu"
        print("⚠️ 使用 CPU 训练（非常慢，建议用 GPU）")
    else:
        device = "cuda"
        print(f"✅ 使用 GPU 训练: {torch.cuda.get_device_name(0)}")
        print(f"   显存总量: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB")

    print_memory_usage()

    # =========================================================
    # 2. 加载 4bit 量化模型
    # =========================================================
    from transformers import (
        AutoModelForCausalLM,
        AutoTokenizer,
        BitsAndBytesConfig,
        TrainingArguments,
    )

    print(f"\n正在加载模型：{config.model_name}")
    t0 = time.perf_counter()

    # 4bit 量化配置（QLoRA 的核心）
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.bfloat16 if device == "cuda" else torch.float32,
        bnb_4bit_use_double_quant=True,
    )

    model = AutoModelForCausalLM.from_pretrained(
        config.model_name,
        quantization_config=bnb_config if device == "cuda" else None,
        device_map="auto" if device == "cuda" else "cpu",
        torch_dtype=torch.bfloat16 if device == "cuda" else torch.float32,
        trust_remote_code=True,
    )

    tokenizer = AutoTokenizer.from_pretrained(
        config.model_name,
        trust_remote_code=True,
    )
    tokenizer.pad_token = tokenizer.eos_token

    print(f"模型加载完成（{int((time.perf_counter() - t0) * 1000)}ms）")
    print_memory_usage()

    # =========================================================
    # 3. 插入 LoRA 适配器
    # =========================================================
    from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training

    # 准备 kbit 训练（冻结某些层）
    model = prepare_model_for_kbit_training(model)

    # LoRA 配置
    lora_config = LoraConfig(
        r=config.lora_r,
        lora_alpha=config.lora_alpha,
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
        lora_dropout=config.lora_dropout,
        bias="none",
        task_type="CAUSAL_LM",
    )

    model = get_peft_model(model, lora_config)

    # 打印可训练参数
    trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
    total = sum(p.numel() for p in model.parameters())
    print(f"\nLoRA 可训练参数: {trainable:,} / {total:,} ({trainable / total * 100:.2f}%)")

    # =========================================================
    # 4. 加载训练数据
    # =========================================================
    from datasets import load_dataset

    print(f"\n正在加载训练数据：{config.data_path}")

    dataset = load_dataset("json", data_files=config.data_path, split="train")

    # 将对话格式转为模型输入格式
    def format_chat(example):
        """将 messages 格式转为模型需要的文本格式"""
        text = tokenizer.apply_chat_template(
            example["messages"],
            tokenize=False,
            add_generation_prompt=False,
        )
        return {"text": text}

    dataset = dataset.map(format_chat)

    # 分割训练/验证集
    split_dataset = dataset.train_test_split(test_size=0.1, seed=42)
    train_dataset = split_dataset["train"]
    eval_dataset = split_dataset["test"]

    print(f"训练集: {len(train_dataset)} 条, 验证集: {len(eval_dataset)} 条")

    # =========================================================
    # 5. 训练
    # =========================================================
    from trl import SFTTrainer

    training_args = TrainingArguments(
        output_dir=config.output_dir,
        per_device_train_batch_size=config.batch_size,
        per_device_eval_batch_size=config.batch_size,
        learning_rate=config.learning_rate,
        num_train_epochs=config.num_epochs,
        logging_steps=10,
        eval_strategy="steps" if len(eval_dataset) > 0 else "no",
        eval_steps=50,
        save_strategy="epoch",
        save_total_limit=2,
        report_to="none",           # 不想用 wandb 等
        fp16=device == "cuda",
        remove_unused_columns=False,
        max_seq_length=config.max_seq_length,
    )

    trainer = SFTTrainer(
        model=model,
        tokenizer=tokenizer,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=eval_dataset if len(eval_dataset) > 0 else None,
        dataset_text_field="text",
        max_seq_length=config.max_seq_length,
    )

    print(f"\n{'=' * 50}")
    print(f"开始训练...")
    print(f"{'=' * 50}")
    train_start = time.perf_counter()

    trainer.train()

    train_time = int(time.perf_counter() - train_start)
    print(f"\n训练完成！耗时 {train_time // 60} 分 {train_time % 60} 秒")

    # =========================================================
    # 6. 保存模型
    # =========================================================
    print(f"\n保存 LoRA 权重到 {config.output_dir}")
    trainer.save_model(config.output_dir)
    tokenizer.save_pretrained(config.output_dir)

    print(f"✅ 训练全部完成！")
    print(f"   模型: {config.model_name}")
    print(f"   LoRA 权重: {config.output_dir}")
    print(f"   可训练参数: {trainable:,} ({trainable / total * 100:.2f}%)")
    print(f"   训练耗时: {train_time // 60} 分 {train_time % 60} 秒")
    print(f"\n运行以下命令对比微调前后的效果：")
    print(f"   python inference.py")

    return config.output_dir


def main():
    import argparse
    parser = argparse.ArgumentParser(description="LoRA 微调训练")
    parser.add_argument("--model-name", default="Qwen/Qwen2.5-1.5B-Instruct",
                        help="基础模型名称（默认 Qwen2.5-1.5B）")
    parser.add_argument("--data-path", default="train_data.jsonl",
                        help="训练数据路径")
    parser.add_argument("--output-dir", default="lora_output",
                        help="LoRA 权重输出目录")
    parser.add_argument("--batch-size", type=int, default=4,
                        help="批次大小（根据显存调整）")
    parser.add_argument("--num-epochs", type=int, default=3,
                        help="训练轮数")
    parser.add_argument("--lora-r", type=int, default=8,
                        help="LoRA rank")
    parser.add_argument("--use-cpu", action="store_true",
                        help="强制使用 CPU")
    args = parser.parse_args()

    config = TrainingConfig(
        model_name=args.model_name,
        data_path=args.data_path,
        output_dir=args.output_dir,
        batch_size=args.batch_size,
        num_epochs=args.num_epochs,
        lora_r=args.lora_r,
        use_cpu=args.use_cpu,
    )

    train(config)


if __name__ == "__main__":
    main()
