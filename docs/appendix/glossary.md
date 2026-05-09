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
