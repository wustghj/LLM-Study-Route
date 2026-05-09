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
