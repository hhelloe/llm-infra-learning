import asyncio
import time
from fastapi import HTTPException
from pydantic import BaseModel, Field

from ..metrics import LatencyStats, percentile

stats = LatencyStats(maxlen=5000)
# 限流
MAX_CONCURRENCY = 8
sem = asyncio.Semaphore(MAX_CONCURRENCY)

# 请求/响应结构
class InferRequest(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=4000)
    max_new_tokens: int = Field(64, ge=1, le=512)
    latency_ms: int = Field(80, ge=0, le=5000)  # mock 推理耗时
    timeout_ms: int = Field(1500, ge=1, le=20000)

class InferResponse(BaseModel):
    text: str
    server_latency_ms: int
    queue_wait_ms: int
    infer_ms: int


def fake_tokenize(s: str) -> int:
    # mock：粗略用空格拆分当 token 数
    return max(1, len(s.split()))


async def mock_infer(req: InferRequest) -> str:
    # mock：sleep一会儿模拟推理
    await asyncio.sleep(req.latency_ms / 1000.0)
    # mock：返回生成文本
    return req.prompt + " " + ("<tok> " * req.max_new_tokens).strip()


# 注册路由的主函数
def register_routes(app):
    @app.get("/metrics")
    async def metrics():
        latencies, ts = stats.snapshot()
        latencies.sort()
        now = time.time()
        # 粗算最近 10 秒 QPS
        window = 10.0
        recent = [x for x in ts if x >= now - window]
        qps = len(recent) / window if window > 0 else 0.0
        return {
            "count": len(latencies),
            "p50_ms": percentile(latencies, 50),
            "p90_ms": percentile(latencies, 90),
            "p99_ms": percentile(latencies, 99),
            "qps_10s": round(qps, 2),
        }

    @app.post("/infer", response_model=InferResponse)
    async def infer(req: InferRequest):
        t0 = time.perf_counter()

        # 记录进入 semaphore 前后的时间差 = queue wait
        q0 = time.perf_counter()
        async with sem:
            queue_wait_ms = int((time.perf_counter() - q0) * 1000)

            i0 = time.perf_counter()
            try:
                text = await asyncio.wait_for(mock_infer(req), timeout=req.timeout_ms / 1000.0)
            except asyncio.TimeoutError:
                raise HTTPException(status_code=504, detail="inference timeout")
            infer_ms = int((time.perf_counter() - i0) * 1000)

        server_latency_ms = int((time.perf_counter() - t0) * 1000)
        stats.add(server_latency_ms)

        return InferResponse(
            text=text,
            server_latency_ms=server_latency_ms,
            queue_wait_ms=queue_wait_ms,
            infer_ms=infer_ms,
        )
