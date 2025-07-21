import os
import subprocess
import sys


def main():
    """启动Streamlit应用"""
    print("🚀 启动 CyberAlchemy 应用...")

    # 检查是否在正确的目录
    if not os.path.exists("app.py"):
        print("❌ 错误: 请在包含 app.py 的目录中运行此脚本")
        return

    try:
        # 运行Streamlit应用
        subprocess.run(
            [
                sys.executable,
                "-m",
                "streamlit",
                "run",
                "app.py",
                "--server.port",
                "8501",
                "--server.address",
                "localhost",
                "--theme.base",
                "dark",
            ],
            check=True,
        )
    except subprocess.CalledProcessError as e:
        print(f"❌ 启动应用时出现错误: {e}")
    except KeyboardInterrupt:
        print("\n👋 应用已停止")


if __name__ == "__main__":
    main()
