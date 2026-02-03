import os
import time
import mmap
import random
import psutil

FILE = "big.bin"
FILE_SIZE_MB = 512           # 跑通后再加大
STRIDE = 4096                # 按 4KB 访问，模拟“按页访问”
SAMPLES = 20000              # 访问多少次（越大越能拉开差距）


def mem_mb() -> float:
    # 获取当前进程占用了多少MB物理内存
    p = psutil.Process(os.getpid())
    return p.memory_info().rss / 1024 / 1024

def make_file(path: str, size_mb: int):
    """生成一个大文件（随机内容），避免被压缩/稀疏文件优化影响。"""
    if os.path.exists(path) and os.path.getsize(path) == size_mb * 1024 * 1024:
        print(f"[make_file] exists: {path} ({size_mb} MB)")
        return

    print(f"[make_file] creating {path} ({size_mb} MB)...")
    chunk = os.urandom(1024 * 1024)  # 1MB
    with open(path, "wb") as f:
        for _ in range(size_mb):
            f.write(chunk)
    print("[make_file] done")