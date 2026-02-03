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

def worker(wid: int, req_q: Queue, out_q: Queue):
    """模拟推理 worker：取请求 -> 生成 token -> 流式输出"""
    while True:
        req = req_q.get()  # 阻塞等待
        if req is STOP:
            req_q.task_done()
            print(f"[worker-{wid}] stop")
            break

        rid = req["rid"]
        # 模拟推理逐 token 生成
        n_tokens = random.randint(10, 25)
        for t in range(n_tokens):
            time.sleep(random.uniform(0.01, 0.03))
            out_q.put((rid, wid, f"T{t}"))
        out_q.put((rid, wid, "[DONE]"))

        req_q.task_done()

def streamer(out_q: Queue, n_requests: int):
    """模拟向客户端 streaming：不断取 token 并输出"""
    done = set()
    while len(done) < n_requests:
        try:
            rid, wid, token = out_q.get(timeout=1.0)
        except Empty:
            continue

        if token == "[DONE]":
            if rid not in done:
                done.add(rid)
            print(f"[stream] rid={rid} from worker-{wid} DONE ({len(done)}/{n_requests})")
        else:
            print(f"[stream] rid={rid} from worker-{wid} token={token}")

        out_q.task_done()


def main():
    n_requests = 20
    n_workers = 4

    req_q = Queue(maxsize=50)   # 请求队列：调度 + 背压
    out_q = Queue(maxsize=500)  # 输出队列：token streaming

    # 启动 streamer（模拟写回客户端）
    t_stream = threading.Thread(target=streamer, args=(out_q, n_requests), daemon=True)
    t_stream.start()

    # 启动workers
    workers = []
    for wid in range(n_workers):
        t = threading.Thread(target=worker, args=(wid, req_q, out_q), daemon=True)
        t.start()
        workers.append(t)

    # 启动 producer（模拟请求涌入）
    t_prod = threading.Thread(target=producer, args=(req_q, n_requests, True), daemon=True)
    t_prod.start()