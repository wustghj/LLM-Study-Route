"""检查学习环境是否就绪。"""

import subprocess
import sys
import os


def check_python() -> bool:
    v = sys.version_info
    ok = v.major == 3 and v.minor >= 10
    print(f"  Python {v.major}.{v.minor}.{v.micro}: {'OK' if ok else '需要 3.10+'} "
          f"({sys.executable})")
    return ok


def check_pip_package(name: str, display: str = None) -> bool:
    try:
        __import__(name)
        print(f"  {display or name}: OK")
        return True
    except ImportError:
        print(f"  {display or name}: 未安装 (pip install {name})")
        return False


def check_gpu() -> str:
    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader"],
            capture_output=True, text=True, timeout=10,
        )
        if result.returncode == 0:
            info = result.stdout.strip()
            print(f"  GPU: {info}")
            return info
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    print("  GPU: 未检测到 NVIDIA GPU（纯 CPU 推理会很慢）")
    return ""


def check_ram() -> str:
    try:
        import psutil
        total = psutil.virtual_memory().total / (1024 ** 3)
        print(f"  RAM: {total:.1f} GB")
        return f"{total:.1f} GB"
    except ImportError:
        print("  RAM: 无法检测（pip install psutil 可以看详细内存信息）")
        return ""


def main():
    print("=" * 50)
    print("LLM 学习路径 — 环境检查")
    print("=" * 50)

    print("\n[Python]")
    py_ok = check_python()

    print("\n[核心依赖]")
    deps = [
        ("openai", "openai"),
        ("numpy", "numpy"),
        ("tomllib", "tomli/tomllib"),
    ]
    dep_ok = all(check_pip_package(name, display) for name, display in deps)

    print("\n[硬件]")
    check_gpu()
    check_ram()

    print("\n[网络]")
    try:
        import urllib.request
        urllib.request.urlopen("https://api.deepseek.com", timeout=5)
        print("  DeepSeek API: 可达")
    except Exception:
        print("  DeepSeek API: 不可达（可能需要 VPN/代理）")

    print("\n[API Key]")
    for var in ["DEEPSEEK_API_KEY", "OPENAI_API_KEY", "PROXY_API_KEY"]:
        val = os.getenv(var, "")
        if val:
            masked = val[:7] + "***" + val[-4:] if len(val) > 11 else "***"
            print(f"  {var}: {masked}")
        else:
            print(f"  {var}: 未设置")

    print("\n" + "=" * 50)
    if py_ok and dep_ok:
        print("环境就绪，可以开始学习！")
    else:
        print("请先解决上述问题再继续。")
    print("=" * 50)


if __name__ == "__main__":
    main()
