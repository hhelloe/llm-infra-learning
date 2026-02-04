import asyncio
import time
from dataclasses import dataclass
from fastapi import HTTPException, Body
from pydantic import BaseModel, Field
from typing import List

from ..metrics import LatencyStats, percentile

# 配置参数
BATCH_SIZE = 4
MAX_BATCH_WAIT_MS = 50

# 统计对象
stats = LatencyStats(maxlen=5000)

# 待处理队列
queue: asyncio.Queue = asyncio.Queue()


@dataclass
class Pending:
    req: "BatchInferRequest"
    enqueued_at: float
    fut: asyncio.Future


class BatchInferRequest(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=4000)
    max_new_tokens: int = Field(64, ge=1, le=512)
    latency_ms: int = Field(80, ge=0, le=5000)
    timeout_ms: int = Field(1500, ge=1, le=20000)


class SingleInferResponse(BaseModel):
    text: str
    batch_wait_ms: int      # 凑批等待时间
    batch_infer_ms: int     # 批推理实际耗时
    server_latency_ms: int  # 总延迟 = batch_wait_ms + batch_infer_ms


class BatchTestRequest(BaseModel):
    batch_size: int = Field(4, ge=1, le=32)
    num_requests: int = Field(16, ge=1, le=100)
    prompt: str = Field("请介绍一下Python")
    max_new_tokens: int = Field(64, ge=1, le=512)
    latency_ms: int = Field(80, ge=0, le=5000)


class BatchTestResult(BaseModel):
    batch_size: int
    num_requests: int
    total_requests: int
    successful: int
    failed: int
    avg_server_latency_ms: float
    min_server_latency_ms: int
    max_server_latency_ms: int
    p50_server_latency_ms: int
    p90_server_latency_ms: int
    p99_server_latency_ms: int
    total_time_ms: int
    throughput_requests_per_sec: float


async def mock_batch_infer(reqs: List[BatchInferRequest]) -> List[str]:
    # 模拟批推理：耗时由最慢请求决定（尾部绑架）
    sleep_ms = max(r.latency_ms for r in reqs)
    await asyncio.sleep(sleep_ms / 1000.0)
    return [r.prompt + " " + ("<tok> " * r.max_new_tokens).strip() for r in reqs]


async def batch_worker():
    # 后台 worker：凑批并执行推理
    while True:
        first: Pending = await queue.get()
        batch = [first]
        t_first = first.enqueued_at
        deadline = t_first + (MAX_BATCH_WAIT_MS / 1000.0)

        # 在等待窗口内尽量凑够 BATCH_SIZE
        while len(batch) < BATCH_SIZE:
            timeout = deadline - time.perf_counter()
            if timeout <= 0:
                break
            try:
                nxt = await asyncio.wait_for(queue.get(), timeout=timeout)
                batch.append(nxt)
            except asyncio.TimeoutError:
                break

        # 计算每个请求的 batch wait 时间
        now = time.perf_counter()
        waits_ms = [int((now - p.enqueued_at) * 1000) for p in batch]

        # 执行批推理
        i0 = time.perf_counter()
        try:
            texts = await mock_batch_infer([p.req for p in batch])
        except Exception as e:
            for p in batch:
                if not p.fut.done():
                    p.fut.set_exception(e)
            continue
        infer_ms = int((time.perf_counter() - i0) * 1000)

        # 分发结果
        for p, text, wait_ms in zip(batch, texts, waits_ms):
            server_latency_ms = wait_ms + infer_ms
            stats.add(server_latency_ms)
            if not p.fut.done():
                p.fut.set_result(SingleInferResponse(
                    text=text,
                    batch_wait_ms=wait_ms,
                    batch_infer_ms=infer_ms,
                    server_latency_ms=server_latency_ms,
                ))


async def run_concurrent_requests(req: BatchTestRequest) -> List[SingleInferResponse]:
    # 并发发送测试请求（无阻塞入队）
    loop = asyncio.get_running_loop()
    futures = []
    start_time = time.perf_counter()

    for _ in range(req.num_requests):
        fut = loop.create_future()
        test_req = BatchInferRequest(
            prompt=req.prompt,
            max_new_tokens=req.max_new_tokens,
            latency_ms=req.latency_ms,
            timeout_ms=5000,
        )
        queue.put_nowait(Pending(req=test_req, enqueued_at=time.perf_counter(), fut=fut))
        futures.append(fut)

    # 等待所有结果
    results = await asyncio.gather(
        *[asyncio.wait_for(fut, timeout=10.0) for fut in futures],
        return_exceptions=True
    )

    # 转换异常结果
    final_results = []
    for r in results:
        if isinstance(r, Exception):
            final_results.append(SingleInferResponse(
                text=f"Error: {str(r)}",
                batch_wait_ms=0,
                batch_infer_ms=0,
                server_latency_ms=0,
            ))
        else:
            final_results.append(r)
    return final_results


def register_routes(app):
    @app.on_event("startup")
    async def _start_batch_worker():
        # 启动后台批处理 worker
        asyncio.create_task(batch_worker())

    @app.post("/batch/infer_one", response_model=SingleInferResponse)
    async def batch_infer_one(req: BatchInferRequest = Body(...)):
        # 单请求入队，等待批处理结果
        loop = asyncio.get_running_loop()
        fut = loop.create_future()
        await queue.put(Pending(req=req, enqueued_at=time.perf_counter(), fut=fut))

        try:
            return await asyncio.wait_for(fut, timeout=req.timeout_ms / 1000.0)
        except asyncio.TimeoutError:
            raise HTTPException(status_code=504, detail="inference timeout")

    @app.post("/batch/test", response_model=BatchTestResult)
    async def batch_test(req: BatchTestRequest):
        # 批量并发测试，返回性能统计
        test_stats = LatencyStats(maxlen=req.num_requests * 2)

        # 备份原始配置并使用测试配置
        global stats, BATCH_SIZE
        original_stats, stats = stats, test_stats
        original_batch_size, BATCH_SIZE = BATCH_SIZE, req.batch_size

        # 清空队列确保干净测试
        while not queue.empty():
            try:
                queue.get_nowait()
            except:
                break

        t0 = time.perf_counter()
        results = await run_concurrent_requests(req)
        total_time_ms = int((time.perf_counter() - t0) * 1000)

        # 恢复原始配置
        stats = original_stats
        BATCH_SIZE = original_batch_size

        successful = sum(1 for r in results if not r.text.startswith("Error:"))
        failed = len(results) - successful

        latencies, _ = test_stats.snapshot()
        latencies.sort()
        avg_latency = sum(latencies) / len(latencies) if latencies else 0.0
        throughput = len(results) / (total_time_ms / 1000.0) if total_time_ms > 0 else 0.0

        return BatchTestResult(
            batch_size=req.batch_size,
            num_requests=req.num_requests,
            total_requests=len(results),
            successful=successful,
            failed=failed,
            avg_server_latency_ms=round(avg_latency, 2),
            min_server_latency_ms=min(latencies) if latencies else 0,
            max_server_latency_ms=max(latencies) if latencies else 0,
            p50_server_latency_ms=percentile(latencies, 50) if latencies else 0,
            p90_server_latency_ms=percentile(latencies, 90) if latencies else 0,
            p99_server_latency_ms=percentile(latencies, 99) if latencies else 0,
            total_time_ms=total_time_ms,
            throughput_requests_per_sec=round(throughput, 2),
        )

    @app.get("/batch/metrics")
    async def batch_metrics():
        # 获取当前统计指标
        latencies, ts = stats.snapshot()
        latencies.sort()
        now = time.time()
        window = 10.0
        recent = [x for x in ts if x >= now - window]
        qps = len(recent) / window if window > 0 else 0.0
        avg_latency = sum(latencies) / len(latencies) if latencies else 0.0

        return {
            "count": len(latencies),
            "avg_latency_ms": round(avg_latency, 2),
            "p50_ms": percentile(latencies, 50) if latencies else 0,
            "p90_ms": percentile(latencies, 90) if latencies else 0,
            "p99_ms": percentile(latencies, 99) if latencies else 0,
            "qps_10s": round(qps, 2),
            "current_batch_size": BATCH_SIZE,
            "max_batch_wait_ms": MAX_BATCH_WAIT_MS,
        }

    @app.post("/batch/config")
    async def update_config(batch_size: int = Body(..., embed=True), max_wait_ms: int = Body(..., embed=True)):
        # 动态更新批处理配置
        global BATCH_SIZE, MAX_BATCH_WAIT_MS
        BATCH_SIZE = batch_size
        MAX_BATCH_WAIT_MS = max_wait_ms
        return {"batch_size": BATCH_SIZE, "max_batch_wait_ms": MAX_BATCH_WAIT_MS}
