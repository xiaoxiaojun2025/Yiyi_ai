"""
测试运行脚本
提供便捷的测试执行命令

使用方法:
  python run_tests.py              # 运行纯软件测试（默认）
  python run_tests.py software     # 运行纯软件测试
  python run_tests.py hardware     # 运行硬件测试
  python run_tests.py all          # 运行所有测试
  python run_tests.py test_xxx.py  # 运行特定测试文件
"""
import subprocess
import sys
from pathlib import Path


# 获取项目根目录（tests 目录的父目录）
project_root = Path(__file__).parent.parent


def run_tests(test_path: str = "test_software_only", verbose: bool = True, html_report: bool = False):
    """运行测试"""
    cmd = [sys.executable, "-m", "pytest"]
    
    if verbose:
        cmd.append("-v")
    
    if html_report:
        # HTML报告输出到项目根目录的 out 文件夹
        report_path = project_root / "out" / "test_report.html"
        report_path.parent.mkdir(exist_ok=True)
        cmd.extend([f"--html={report_path}", "--self-contained-html"])
    
    # 使用相对于项目根目录的完整路径
    full_test_path = str(Path(__file__).parent / test_path)
    cmd.append(full_test_path)
    
    print(f"\n运行命令: {' '.join(cmd)}\n")
    result = subprocess.run(cmd, cwd=project_root)
    return result.returncode


def run_software_tests():
    """运行纯软件测试"""
    print("=" * 60)
    print("运行纯软件测试（无需硬件）")
    print("=" * 60)
    return run_tests("test_software_only")


def run_hardware_tests():
    """运行硬件测试"""
    print("=" * 60)
    print("运行硬件测试（需要MAX30102传感器）")
    print("=" * 60)
    print("\n⚠️  请确保:")
    print("  1. MAX30102传感器已正确连接")
    print("  2. I2C接口已启用")
    print("  3. 手指准备贴在传感器上\n")
    input("按Enter键开始测试...")
    return run_tests("test_with_hardware", html_report=True)


def run_all_tests():
    """运行所有测试"""
    print("=" * 60)
    print("运行所有测试")
    print("=" * 60)
    return run_tests(".", html_report=True)


def run_specific_test(test_file: str):
    """运行特定测试文件"""
    print(f"运行测试: {test_file}")
    return run_tests(test_file)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "software":
            sys.exit(run_software_tests())
        elif command == "hardware":
            sys.exit(run_hardware_tests())
        elif command == "all":
            sys.exit(run_all_tests())
        elif command.endswith(".py"):
            sys.exit(run_specific_test(command))
        else:
            print(f"未知命令: {command}")
            print("可用命令: software, hardware, all, <test_file.py>")
            sys.exit(1)
    else:
        # 默认运行纯软件测试
        sys.exit(run_software_tests())