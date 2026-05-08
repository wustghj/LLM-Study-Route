# Agent Demo — 基于 Function Calling 的智能助手

> Phase 3：让模型能调用工具、能自主决策

## 一句话理解

普通 LLM = 只能说话，不能做事。
Agent = 能说话 + 能调工具 + 能根据结果决定下一步。

## 架构

```
用户：计算 2^10 等于多少？
  │
  ├─→ LLM 思考："用户要计算，我可以用 calculator 工具"
  │     └─→ 返回 function_call: calculator({expression: "2 ** 10"})
  │
  ├─→ Agent 执行工具 → 得到结果 "2 ** 10 = 1024"
  │     └─→ 把结果发给 LLM
  │
  └─→ LLM 回答："2^10 = 1024"
```

## 安装

```powershell
# 不需要额外依赖，用 CLI 客户端已有的 openai 包
cd api调用实战/agent-demo
```

## 运行

```powershell
$env:DEEPSEEK_API_KEY="sk-..."
python agent.py
```

## 示例对话

```
你> 计算 12345 × 6789 等于多少？

[Agent 思考中... 第 1 轮]
  → 调用工具：calculator({'expression': '12345 * 6789'}) 执行完毕（2ms）
[Agent] 12345 × 6789 = 83,827,205

---

你> 现在几点了？

[Agent 思考中... 第 1 轮]
  → 调用工具：get_current_time({}) 执行完毕（1ms）
[Agent] 当前时间是 2026-05-08 11:30:00

---

你> 看看本目录下有哪些文件？

[Agent 思考中... 第 1 轮]
  → 调用工具：list_directory({'path': '.'}) 执行完毕（3ms）
[Agent] 本目录的文件：
  📄 agent.py
  📄 README.md
  📄 requirements.txt
```

## Agent 能用的工具

| 工具 | 作用 | 示例输入 |
|------|------|----------|
| `calculator` | 执行数学计算 | `12345 * 6789` |
| `get_current_time` | 获取当前时间 | — |
| `list_directory` | 列出目录内容 | `.` 或 `../cli-chat` |

## 自己加工具

编辑 `agent.py`，在 `TOOLS` 列表和 `TOOL_MAP` 字典里加：

```python
# 1. 定义工具描述（让 LLM 知道有这工具）
TOOLS = [
    ...,
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "读取指定文件的内容",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "文件路径"},
                },
                "required": ["path"],
            },
        },
    },
]

# 2. 实现工具函数
def tool_read_file(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

# 3. 注册到映射
TOOL_MAP["read_file"] = tool_read_file
```

## Function Calling 协议

LLM 返回的 function_call 长这样：

```json
{
  "finish_reason": "tool_calls",
  "message": {
    "tool_calls": [{
      "id": "call_xxx",
      "function": {
        "name": "calculator",
        "arguments": "{\"expression\": \"2 ** 10\"}"
      }
    }]
  }
}
```

Agent 要做的事：

1. 解析 `function.name` 和 `function.arguments`
2. 调用本地对应的 Python 函数
3. 把结果作为 `role: "tool"` 消息发给 LLM
4. LLM 看到结果后决定是继续调工具还是给出最终回答

## 与 main.py 的区别

| 文件 | 做什么 | 交互方式 |
|------|--------|----------|
| `main.py` | 普通聊天（一问一答） | 你说一句、模型回一句 |
| `agent.py` | Agent 对话（可调用工具） | 你说一句、模型可能调多个工具再回答 |
