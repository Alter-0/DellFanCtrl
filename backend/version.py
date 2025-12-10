"""项目版本信息"""
import os

def get_version() -> str:
    """从根目录 VERSION 文件读取版本号"""
    version_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), "VERSION")
    try:
        with open(version_file, "r") as f:
            return f.read().strip()
    except FileNotFoundError:
        return "unknown"

__version__ = get_version()
