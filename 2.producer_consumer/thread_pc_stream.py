import time
import random
import threading
from queue import Queue, Empty

STOP = None  # 停止信号

def producer(req_q: Queue, n_requests: int, burst: bool = True):
    """模拟请求进入：把请求放入队列"""
    for rid in range(n_requests):
        if not burst:
            time.sleep(random.uniform(0.02, 0.08))  # 平滑到达
        req = {"rid": rid, "prompt_len": random.randint(10, 200)}
        req_q.put(req)  # 队列满会阻塞：背压
        print(f"[producer] enqueue rid={rid} prompt_len={req['prompt_len']}")
    print("[producer] done")