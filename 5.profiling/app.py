import asyncio
import time
import threading
from collections import deque
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

app = FastAPI(title="Inference Mock")

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

# 限流
MAX_CONCURRENCY = 429
sem = asyncio.Semaphore(MAX_CONCURRENCY)

# 请求/响应结构
class InferRequest(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=4000)
    max_new_tokens: int = Field(64, ge=1, le=512)
    latency_ms: int = Field(80, ge=0, le=5000)  # mock 推理耗时
    timeout_ms: int = Field(1500, ge=1, le=20000)

class InferResponse(BaseModel):
    text: str
    prompt_tokens: int
    new_tokens: int
    latency_ms: int

def fake_tokenize(s: str) -> int:
    # mock：粗略用空格拆分当 token 数
    return max(1, len(s.split()))

async def mock_infer(req: InferRequest) -> str:
    # mock：sleep一会儿模拟推理
    await asyncio.sleep(req.latency_ms / 1000.0)
    # mock：返回生成文本
    return req.prompt + " " + ("<tok> " * req.max_new_tokens).strip()

@app.get("/healthz")
async def healthz():
    return {"ok": True}

@app.post("/infer", response_model=InferResponse)
async def infer(req: InferRequest):
    start = time.perf_counter()

    # 并发限流：拿不到就排队等
    async with sem:
        try:
            # timeout
            # 给单次推理一个硬上限，防止慢请求无限占资源
            text = await asyncio.wait_for(mock_infer(req), timeout=req.timeout_ms / 1000.0)
        except asyncio.TimeoutError:
            raise HTTPException(status_code=504, detail="inference timeout")
        
    latency_ms = int((time.perf_counter() - start) * 1000)
    return InferResponse(
        text=text,
        prompt_tokens=fake_tokenize(req.prompt),
        new_tokens=req.max_new_tokens,
        latency_ms=latency_ms,
    )