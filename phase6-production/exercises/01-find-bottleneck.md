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
