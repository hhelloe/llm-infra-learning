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

# 子进程和父进程一起监控
def monitor_cpu_tree(pid: int, interval: float = 0.5, verbose: bool = False) -> float:
    """
    监控 pid 这个父进程 + 其子进程(递归) 在 interval 秒内的 CPU 使用率总和。
    返回 total_cpu_percent（按 psutil 的口径：可能 > 100%）。
    """
    parent = psutil.Process(pid)

    # 采样开始时拿一次进程树（ProcessPoolExecutor 的 worker 通常是 child）
    procs = [parent] + parent.children(recursive=True)

    # 预热：cpu_percent(None) 第一次没意义，必须先调用一次建立基线
    for p in procs:
        try:
            p.cpu_percent(interval=None)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass

    time.sleep(interval)

    total = 0.0
    per = []
    for p in procs:
        try:
            cpu = p.cpu_percent(interval=None)
            total += cpu
            if verbose:
                per.append((p.pid, cpu))
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass

    if verbose:
        per.sort(key=lambda x: x[1], reverse=True)
        print("cpu% by pid:", per)

    return total

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

        # 监控当前进程的CPU占用（多进程时这里只监控父进程）
        cpu_parent = monitor_cpu_tree(pid)

        total = sum(f.result() for f in futures)

    t1 = time.time()
    print(f"total primes = {total}")
    print(f"elapsed = {t1 - t0:.3f}s")
    print(f"parent process cpu% (approx) = {cpu_parent:.1f}%")
    return t1 - t0

def main():
    # 让任务足够重一些，才看得出差异
    n = 2400_000     # 机器快的话可以改成 600_000 或 800_000
    cpu_cnt = os.cpu_count() or 4
    workers = min(8, cpu_cnt)   # 不要盲目开很大
    chunks = workers * 4        # 让任务分更细一点

    # 1) 单线程（线程池1个worker）
    run_case(ThreadPoolExecutor, workers=1, chunks=chunks, n=n)

    # 2) 多线程（CPU密集型：通常不会更快，常常更慢）
    run_case(ThreadPoolExecutor, workers=workers, chunks=chunks, n=n)

    # 3) 多进程（CPU密集型：通常显著变快）
    run_case(ProcessPoolExecutor, workers=workers, chunks=chunks, n=n)

if __name__ == "__main__":
    main()