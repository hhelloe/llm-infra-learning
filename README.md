# llm-infra-learning
llm infra learn process
这个仓库总的来说用于做以下的事情
1. Day 1｜进程 / 线程 / GIL：学：进程 vs 线程，Python GIL 是什么，什么时候有用/没用；做：写一个多线程 + 多进程 demo，对比 CPU 利用率；能回答：推理服务为什么常用多进程而不是多线程？

2. Day 2｜并发模型（async / queue）：学：threading / multiprocessing / asyncio 的适用场景；做：写一个 producer–consumer 队列（模拟请求进来、worker 处理）；能回答：streaming 推理适合用哪种并发模型？

3. Day 3｜内存 & I/O：学：虚拟内存、page、mmap，阻塞 I/O vs 非阻塞 I/O；做：对比普通读文件 vs mmap 读文件；能回答：模型权重为什么常用 mmap 加载？

4. Day 4｜网络基础（服务端视角）：学：HTTP vs gRPC，keep-alive、timeout、retry；做：用 FastAPI 写一个简单推理 mock 接口；能回答：为什么推理服务要限流/熔断？

5. Day 5｜性能 profiling（CPU 侧）：学：latency / throughput / p99；做：给 Day 4 的接口加 timing 和简单 profiling；能回答：为什么 batch 大吞吐高，但延迟可能变差？

6. Day 6–7｜总结 & 复盘：输出：一页笔记《一次推理请求的完整系统路径》；检查点：能画出客户端 → 服务 → GPU → 返回。

7. Day 8｜GPU 结构：学：GPU / SM / warp / register / shared / L1 / L2 / HBM；做：画一张自己的 GPU 结构图；能回答：shared、L1、L2 的关系。

8. Day 9｜kernel / warp / divergence：学：kernel launch，warp lockstep，branch divergence；做：写一个 if/else kernel（或看示例）理解 divergence；能回答：为什么分支多会慢？

9. Day 10｜内存带宽 & 访存：学：memory bandwidth，coalesced vs random access；做：理解“连续访问 vs 随机访问”的 kernel 示例；能回答：KV cache 为什么是带宽瓶颈？

10. Day 11｜Stream & 异步：学：CUDA stream，async copy，pinned memory；做：理解一张 compute + memcpy overlap 的时间线图；能回答：async copy 什么时候会退化成同步？

11. Day 12｜Nsight Systems：学：nsys timeline 怎么看；做：跑一个 PyTorch 推理并截图一张 trace；能回答：launch overhead 在 trace 里长什么样？

12. Day 13–14｜总结：输出：一页笔记《GPU 慢的 4 种典型原因》（launch / divergence / bandwidth / sync）。

13. Day 15｜vLLM 架构：学：prefill vs decode，continuous batching；做：跑 vLLM demo；能回答：为什么 decode 是瓶颈？

14. Day 16｜KV Cache & PagedAttention：学：KV cache 生命周期，block / page allocator；做：画 KV cache 内存分布图；能回答：为什么不用连续内存？

15. Day 17｜调度：学：continuous batching，chunked prefill；做：改一个参数观察吞吐变化；能回答：长短请求混跑的问题？

16. Day 18｜推理加速：学：FlashAttention，CUDA Graph，量化思路；做：理解 FlashAttention 的数据复用逻辑；能回答：CUDA Graph 解决的是什么问题？

17. Day 19｜Speculative Decoding：学：speculative decoding / EAGLE；做：画流程图；能回答：什么场景收益最大？风险是什么？

18. Day 20–21｜确定 PR 选题：选一个 profiling / batching 参数 / prefix cache；写 README 草稿（问题 / 怀疑 / 实验）。

19. Day 22–23｜动代码：做：fork 项目并实现实验性改动；要求：改动不大但逻辑清楚。

20. Day 24｜跑实验：做：baseline vs optimized；记录：tokens/s、TTFT、显存占用。

21. Day 25｜完善 README：必须包含问题、为什么怀疑、实验结果、局限性。

22. Day 26｜整理简历素材：写清楚你改了什么、带来了什么变化、学到了什么 trade-off。

23. Day 27–28｜模拟面试：自问自答为什么这里慢、为什么这样改、有没有更极端场景。

completed:
a1_gil_preact_thread
a2_producer_consumer