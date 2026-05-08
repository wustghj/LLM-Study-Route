"""
inference.py — 对比微调前后的模型表现

用法：
    # 先训练
    python train.py

    # 再对比
    python inference.py                          # 对比微调前后
    python inference.py --query "什么是RAII？"    # 问特定问题
    python inference.py --base-only              # 只看微调前
    python inference.py --lora-only              # 只看微调后
"""

import json
import os
import sys
import time
from pathlib import Path
from typing import Optional

import torch


LORA_PATH = "lora_output"
BASE_MODEL = "Qwen/Qwen2.5-1.5B-Instruct"

TEST_QUESTIONS = [
    "什么是 RAII？",
    "解释一下智能指针",
    "指针和引用的区别",
    "什么是 KV Cache？",
    "Ollama 和 llama.cpp 的关系？",
    "你是一个什么模型？",
]


def load_base_model():
    """加载基础模型（未微调）"""
    from transformers import AutoModelForCausalLM, AutoTokenizer

    print(f"正在加载基础模型：{BASE_MODEL}")
    t0 = time.perf_counter()

    tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL, trust_remote_code=True)
    tokenizer.pad_token = tokenizer.eos_token

    model = AutoModelForCausalLM.from_pretrained(
        BASE_MODEL,
        device_map="auto",
        torch_dtype=torch.bfloat16 if torch.cuda.is_available() else torch.float32,
        trust_remote_code=True,
    )

    print(f"  加载完成（{int((time.perf_counter() - t0) * 1000)}ms）")
    return model, tokenizer


def load_lora_model():
    """加载微调后的模型（基础模型 + LoRA 权重）"""
    from peft import PeftModel
    from transformers import AutoModelForCausalLM, AutoTokenizer

    lora_path = Path(LORA_PATH)
    if not lora_path.exists():
        print(f"错误：找不到 LoRA 权重目录 {LORA_PATH}")
        print("请先运行 python train.py")
        sys.exit(1)

    print(f"正在加载 LoRA 微调模型：{BASE_MODEL} + {LORA_PATH}")
    t0 = time.perf_counter()

    tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL, trust_remote_code=True)
    tokenizer.pad_token = tokenizer.eos_token

    base = AutoModelForCausalLM.from_pretrained(
        BASE_MODEL,
        device_map="auto",
        torch_dtype=torch.bfloat16 if torch.cuda.is_available() else torch.float32,
        trust_remote_code=True,
    )

    model = PeftModel.from_pretrained(base, LORA_PATH)

    print(f"  加载完成（{int((time.perf_counter() - t0) * 1000)}ms）")
    return model, tokenizer


def generate_answer(
    model,
    tokenizer,
    question: str,
    system_prompt: str | None = None,
    max_new_tokens: int = 256,
) -> tuple[str, int]:
    """用模型生成回答，返回 (文本, 耗时ms)"""
    if system_prompt is None:
        system_prompt = "你是一个 C++ 后端工程师，回答极其简洁，只给结论和关键代码。"

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": question},
    ]

    # 转成模型输入格式
    text = tokenizer.apply_chat_template(
        messages, tokenize=False, add_generation_prompt=True
    )

    inputs = tokenizer(text, return_tensors="pt").to(model.device)

    t0 = time.perf_counter()
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            temperature=0.3,
            do_sample=True,
            pad_token_id=tokenizer.eos_token_id,
        )
    elapsed = int((time.perf_counter() - t0) * 1000)

    # 解码，去掉输入部分
    full_output = tokenizer.decode(outputs[0], skip_special_tokens=True)
    # 找到 assistant 部分
    if "assistant" in full_output:
        answer = full_output.split("assistant")[-1].strip()
        # 去掉开头的可能的标记
        for prefix in ["\n", "：", ":", "】", "】"]:
            if answer.startswith(prefix):
                answer = answer[len(prefix):].strip()
    else:
        answer = full_output[len(text):].strip()

    return answer, elapsed


def print_comparison(
    question: str,
    base_answer: str,
    lora_answer: str,
    base_ms: int,
    lora_ms: int,
):
    """并排显示微调前后的回答"""
    print("\n" + "=" * 70)
    print(f"问题：{question}")
    print("=" * 70)

    print(f"\n📦 微调前（{base_ms}ms）：")
    print("-" * 40)
    print(base_answer[:300])

    print(f"\n🎯 微调后（{lora_ms}ms）：")
    print("-" * 40)
    print(lora_answer[:300])

    print("=" * 70)


def main():
    import argparse
    parser = argparse.ArgumentParser(description="对比微调前后的模型效果")
    parser.add_argument("--query", default=None, help="指定问题（默认跑所有测试问题）")
    parser.add_argument("--base-only", action="store_true", help="只看微调前")
    parser.add_argument("--lora-only", action="store_true", help="只看微调后")
    args = parser.parse_args()

    questions = [args.query] if args.query else TEST_QUESTIONS

    use_base = not args.lora_only
    use_lora = not args.base_only

    # 加载模型
    base_model = None
    lora_model = None
    base_tokenizer = None
    lora_tokenizer = None

    if use_base:
        base_model, base_tokenizer = load_base_model()

    if use_lora:
        lora_model, lora_tokenizer = load_lora_model()

    print(f"\n{'=' * 70}")
    print(f"微调效果对比 — {BASE_MODEL}")
    print(f"LoRA 权重：{LORA_PATH if use_lora else '未使用'}")
    print(f"{'=' * 70}\n")

    for question in questions:
        base_answer = ""
        lora_answer = ""
        base_ms = 0
        lora_ms = 0

        if use_base:
            print(f"  基础模型推理中...", flush=True)
            base_answer, base_ms = generate_answer(base_model, base_tokenizer, question)

        if use_lora:
            print(f"  微调模型推理中...", flush=True)
            lora_answer, lora_ms = generate_answer(lora_model, lora_tokenizer, question)

        if use_base and use_lora:
            print_comparison(question, base_answer, lora_answer, base_ms, lora_ms)
        elif use_base:
            print(f"\n📦 微调前 [{question}]（{base_ms}ms）：")
            print(base_answer[:400])
        elif use_lora:
            print(f"\n🎯 微调后 [{question}]（{lora_ms}ms）：")
            print(lora_answer[:400])

    print("\n✅ 对比完成")

    # 简单评判
    if use_base and use_lora:
        print("\n💡 观察要点：")
        print("  1. 微调后的回答是否更简洁？是否符合 C++ 工程师风格？")
        print("  2. 微调是否影响了对非训练内容的回答质量？（灾难性遗忘）")
        print("  3. 微调后的回答速度有没有变化？")


if __name__ == "__main__":
    main()
