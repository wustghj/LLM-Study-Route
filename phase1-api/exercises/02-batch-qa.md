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
