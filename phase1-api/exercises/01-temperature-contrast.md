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
