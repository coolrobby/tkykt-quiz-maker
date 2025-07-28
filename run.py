#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
坦克云课堂选择题生成器 - Streamlit版本启动脚本
适用于本地开发和云端部署
"""

import sys
import os
import subprocess

def main():
    """主启动函数"""
    print("🚀 启动坦克云课堂选择题生成器 - Streamlit版本")
    print("📊 正在检查环境...")
    
    # 检查Python版本
    if sys.version_info < (3, 8):
        print("❌ 错误: 需要Python 3.8或更高版本")
        sys.exit(1)
    
    print(f"✅ Python版本: {sys.version}")
    
    # 检查依赖
    try:
        import streamlit
        print(f"✅ Streamlit版本: {streamlit.__version__}")
    except ImportError:
        print("❌ 错误: 未安装Streamlit")
        print("请运行: pip install -r requirements.txt")
        sys.exit(1)
    
    try:
        import pandas
        print(f"✅ Pandas版本: {pandas.__version__}")
    except ImportError:
        print("❌ 错误: 未安装Pandas")
        sys.exit(1)
    
    try:
        import openpyxl
        print(f"✅ OpenPyXL版本: {openpyxl.__version__}")
    except ImportError:
        print("❌ 错误: 未安装OpenPyXL")
        sys.exit(1)
    
    # 确保输出目录存在
    output_dir = "outputs/generated_quizzes"
    os.makedirs(output_dir, exist_ok=True)
    print(f"✅ 输出目录: {os.path.abspath(output_dir)}")
    
    # 启动Streamlit应用
    print("🌐 启动Streamlit应用...")
    print("📱 访问地址: http://localhost:8501")
    print("⏹️  按 Ctrl+C 停止应用")
    print("-" * 50)
    
    try:
        # 使用subprocess启动streamlit
        cmd = [sys.executable, "-m", "streamlit", "run", "streamlit_app.py"]
        subprocess.run(cmd, check=True)
    except KeyboardInterrupt:
        print("\n👋 应用已停止")
    except subprocess.CalledProcessError as e:
        print(f"❌ 启动失败: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ 未知错误: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
