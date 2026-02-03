import os
import time
import math
import psutil
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor

# 示例 CPU 密集型任务：判断质数 + 计数
def is_prime(n: int) -> bool:
    if n < 2:
        return False
    if n % 2 == 0:
        return n == 2
    r = int(math.isqrt(n))
    for i in range(3, r + 1, 2):
        if n % i == 0:
            return False
    return True

def count_primes(lo: int, hi: int) -> int:
    c = 0
    for x in range(lo, hi):
        if is_prime(x):
            c += 1
    return c

# psutil库工具打印进程 CPU 使用情况
def monitor_cpu(pid: int, stop_after: float = 0.5):
    p = psutil.Process(pid)
    # 第一次cpu_percent通常为0，需要预热
    p.cpu_percent(interval=None)
    time.sleep(stop_after)
    cpu = p.cpu_percent(interval=None)
    return cpu

def run_case(executor_cls, workers: int, chunks: int, n: int):
    """
    把区间 [2, n) 切成 chunks 份，丢给 workers 并行跑
    """
    pid = os.getpid()
    print(f"\n=== {executor_cls.__name__} | workers={workers} | chunks={chunks} | n={n} | pid={pid} ===")

    # 切块
    span = n - 2
    step = span // chunks
    ranges = []
    start = 2
    for i in range(chunks):
        end = start + step
        if i == chunks - 1:
            end = n
        ranges.append((start, end))
        start = end

    t0 = time.time()
    # 开始并行
    with executor_cls(max_workers=workers) as ex:
        futures = [ex.submit(count_primes, lo, hi) for lo, hi in ranges]

        # 简单监控一下当前进程的CPU占用（注意：多进程时这里只监控父进程）
        cpu_parent = monitor_cpu(pid)

        total = sum(f.result() for f in futures)

    t1 = time.time()
    print(f"total primes = {total}")
    print(f"elapsed = {t1 - t0:.3f}s")
    print(f"parent process cpu% (approx) = {cpu_parent:.1f}%")
    return t1 - t0