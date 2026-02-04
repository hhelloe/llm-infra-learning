import threading
import time
from collections import deque

class LatencyStats:
    """保存最近 N 次请求的延迟，用来算 p50/p90/p99"""
    def __init__(self, maxlen=5000):
        self.maxlen = maxlen
        self.lock = threading.Lock()
        self.latencies_ms = deque(maxlen=maxlen)
        self.req_timestamps = deque(maxlen=maxlen)  # 用于粗算 QPS

    def add(self, latency_ms: int):
        now = time.time()
        with self.lock:
            self.latencies_ms.append(latency_ms)
            self.req_timestamps.append(now)

    def snapshot(self):
        with self.lock:
            l = list(self.latencies_ms)
            t = list(self.req_timestamps)
        return l, t

def percentile(sorted_list, p: float) -> int:
    if not sorted_list:
        return 0
    # p in [0,100]
    idx = int((p / 100.0) * (len(sorted_list) - 1))
    return sorted_list[idx]
