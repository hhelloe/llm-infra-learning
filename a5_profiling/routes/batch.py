import asyncio
import time
from fastapi import HTTPException
from pydantic import BaseModel, Field
from typing import List

from ..metrics import LatencyStats, percentile

stats = LatencyStats(maxlen=5000)

# Batch 配置
BATCH_SIZE = 4  # 默认每批处理 4 个请求
MAX_BATCH_WAIT_MS = 50  # 等待更多请求的最大等待时间


class BatchInferRequest(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=4000)
    max_new_tokens: int = Field(64, ge=1, le=512)
    latency_ms: int = Field(80, ge=0, le=5000)  # mock 推理耗时
    timeout_ms: int = Field(1500, ge=1, le=20000)


class SingleInferResponse(BaseModel):
    text: str
    server_latency_ms: int
    queue_wait_ms: int
    infer_ms: int


class BatchInferResponse(BaseModel):
    results: List[SingleInferResponse]
    batch_size: int
    total_ms: int


class BatchTestRequest(BaseModel):
    batch_size: int = Field(4, ge=1, le=32, description="每批处理的请求数")
    num_requests: int = Field(16, ge=1, le=100, description="总请求数")
    prompt: str = Field("请介绍一下Python", description="测试用 prompt")
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


def fake_tokenize(s: str) -> int:
    return max(1, len(s.split()))


async def mock_infer(req: BatchInferRequest) -> str:
    await asyncio.sleep(req.latency_ms / 1000.0)
    return req.prompt + " " + ("<tok> " * req.max_new_tokens).strip()


async def process_single_request(req: BatchInferRequest, stats_obj: LatencyStats) -> SingleInferResponse:
    t0 = time.perf_counter()

    q0 = time.perf_counter()
    i0 = time.perf_counter()
    try:
        text = await asyncio.wait_for(mock_infer(req), timeout=req.timeout_ms / 1000.0)
    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail="inference timeout")
    infer_ms = int((time.perf_counter() - i0) * 1000)
    queue_wait_ms = 0  # 无并发限流时为 0

    server_latency_ms = int((time.perf_counter() - t0) * 1000)
    stats_obj.add(server_latency_ms)

    return SingleInferResponse(
        text=text,
        server_latency_ms=server_latency_ms,
        queue_wait_ms=queue_wait_ms,
        infer_ms=infer_ms,
    )


async def process_batch(requests: List[BatchInferRequest], batch_size: int, stats_obj: LatencyStats) -> List[SingleInferResponse]:
    """批量处理请求"""
    results = []

    for i in range(0, len(requests), batch_size):
        batch = requests[i:i + batch_size]
        batch_start = time.perf_counter()

        # 并发处理当前批次的请求
        batch_results = await asyncio.gather(
            *[process_single_request(req, stats_obj) for req in batch],
            return_exceptions=True
        )

        for result in batch_results:
            if isinstance(result, Exception):
                results.append(SingleInferResponse(
                    text=f"Error: {str(result)}",
                    server_latency_ms=0,
                    queue_wait_ms=0,
                    infer_ms=0,
                ))
            else:
                results.append(result)

    return results


def register_routes(app):
    @app.post("/batch/infer", response_model=BatchInferResponse)
    async def batch_infer(requests: List[BatchInferRequest]):
        """
        批量推理接口
        - requests: 请求列表
        - 使用全局 BATCH_SIZE 进行分组处理
        """
        if not requests:
            raise HTTPException(status_code=400, detail="requests list is empty")

        t0 = time.perf_counter()
        results = await process_batch(requests, BATCH_SIZE, stats)
        total_ms = int((time.perf_counter() - t0) * 1000)

        return BatchInferResponse(
            results=results,
            batch_size=BATCH_SIZE,
            total_ms=total_ms,
        )

    @app.post("/batch/test", response_model=BatchTestResult)
    async def batch_test(req: BatchTestRequest):
        """
        批量测试接口
        - batch_size: 每批处理的请求数
        - num_requests: 总请求数
        - 返回性能统计结果
        """
        batch_stats = LatencyStats(maxlen=req.num_requests * 2)

        # 生成测试请求
        requests = [
            BatchInferRequest(
                prompt=req.prompt,
                max_new_tokens=req.max_new_tokens,
                latency_ms=req.latency_ms,
                timeout_ms=5000,
            )
            for _ in range(req.num_requests)
        ]

        t0 = time.perf_counter()

        # 批量处理
        results = await process_batch(requests, req.batch_size, batch_stats)

        total_time_ms = int((time.perf_counter() - t0) * 1000)

        # 统计成功/失败
        successful = sum(1 for r in results if not r.text.startswith("Error:"))
        failed = len(results) - successful

        # 获取延迟统计
        latencies, _ = batch_stats.snapshot()
        latencies.sort()

        if latencies:
            avg_latency = sum(latencies) / len(latencies)
        else:
            avg_latency = 0.0

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
        """获取批量推理的统计指标"""
        latencies, ts = stats.snapshot()
        latencies.sort()
        now = time.time()
        window = 10.0
        recent = [x for x in ts if x >= now - window]
        qps = len(recent) / window if window > 0 else 0.0

        if latencies:
            avg_latency = sum(latencies) / len(latencies)
        else:
            avg_latency = 0.0

        return {
            "count": len(latencies),
            "avg_latency_ms": round(avg_latency, 2),
            "p50_ms": percentile(latencies, 50) if latencies else 0,
            "p90_ms": percentile(latencies, 90) if latencies else 0,
            "p99_ms": percentile(latencies, 99) if latencies else 0,
            "qps_10s": round(qps, 2),
            "current_batch_size": BATCH_SIZE,
        }
    
async def mock_batch_infer(reqs: List[BatchInferRequest]) -> List[str]:
    # 模拟：一个 batch 的耗时由最慢请求决定（尾部绑架）
    sleep_ms = max(r.latency_ms for r in reqs)
    await asyncio.sleep(sleep_ms / 1000.0)

    outs = []
    for r in reqs:
        outs.append(r.prompt + " " + ("<tok> " * r.max_new_tokens).strip())
    return outs
