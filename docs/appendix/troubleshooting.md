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
