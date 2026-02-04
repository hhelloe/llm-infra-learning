PS F:\code\llm-infra-learning> Invoke-RestMethod -Uri http://127.0.0.1:8000/batch/test -Method POST -ContentType "application/json" -Body '{
>>   "batch_size": 1,
>>   "num_requests": 50,
>>   "latency_ms": 80
>> }'

batch_size                  : 1
num_requests                : 50
total_requests              : 50
successful                  : 50
failed                      : 0
avg_server_latency_ms       : 2378.8
min_server_latency_ms       : 90
max_server_latency_ms       : 4667
p50_server_latency_ms       : 2333
p90_server_latency_ms       : 4198
p99_server_latency_ms       : 4573
total_time_ms               : 4667
throughput_requests_per_sec : 10.71

PS F:\code\llm-infra-learning> Invoke-RestMethod -Uri http://127.0.0.1:8000/batch/test -Method POST -ContentType "application/json" -Body '{
>>   "batch_size": 4,
>>   "num_requests": 50,
>>   "latency_ms": 80
>> }'

batch_size                  : 4
num_requests                : 50
total_requests              : 50
successful                  : 50
failed                      : 0
avg_server_latency_ms       : 2108.98
min_server_latency_ms       : 90
max_server_latency_ms       : 4382
p50_server_latency_ms       : 2052
p90_server_latency_ms       : 3919
p99_server_latency_ms       : 4289
total_time_ms               : 4383
throughput_requests_per_sec : 11.41

PS F:\code\llm-infra-learning> Invoke-RestMethod -Uri http://127.0.0.1:8000/batch/test -Method POST -ContentType "application/json" -Body '{
>>   "batch_size": 8,
>>   "num_requests": 50,
>>   "latency_ms": 80
>> }'

batch_size                  : 8
num_requests                : 50
total_requests              : 50
successful                  : 50
failed                      : 0
avg_server_latency_ms       : 1780.36
min_server_latency_ms       : 95
max_server_latency_ms       : 4018
p50_server_latency_ms       : 1682
p90_server_latency_ms       : 3550
p99_server_latency_ms       : 3924
total_time_ms               : 4019
throughput_requests_per_sec : 12.44

如上数据
batch=1：total_time ≈ 4667ms，QPS ≈ 10.71
batch=4：total_time ≈ 4383ms，QPS ≈ 11.41
batch=8：total_time ≈ 4019ms，QPS ≈ 12.44

50 个请求并发涌入时，batch=1 要串行处理 50 次，batch=8 只需 6-7 批
mock 是批推理，但等待窗口和队列开销抵消了部分收益，所以吞吐提升温和而非剧烈