PS F:\code\llm-infra-learning> curl http://127.0.0.1:8000/healthz
{"ok":true}

PS F:\code\llm-infra-learning> Invoke-RestMethod `
>>   -Uri http://127.0.0.1:8000/infer `
>>   -Method POST `
>>   -ContentType "application/json" `
>>   -Body '{
>>     "prompt": "hello",
>>     "max_new_tokens": 16,
>>     "latency_ms": 120,
>>     "timeout_ms": 1500
>>   }'

text
----                                                                                       
hello <tok> <tok> <tok> <tok> <tok> <tok> <tok> <tok> <tok> <tok> <tok> <tok> <tok> <tok>… 

PS F:\code\llm-infra-learning> Invoke-RestMethod `
>>   -Uri http://127.0.0.1:8000/infer `
>>   -Method POST `
>>   -ContentType "application/json" `
>>   -Body '{
>>     "prompt": "hello",
>>     "max_new_tokens": 16,
>>     "latency_ms": 500,
>>     "timeout_ms": 300 
>>   }'
Invoke-RestMethod:                                                                         
{
  "detail": "inference timeout"
}

以上输出可看出inference mock成功运行

timeout 决定单个请求的上限损害（app.py第48行体现）

semaphore 决定系统的最大承载并发（app.py第10行体现）

keep-alive 决定单位请求的连接成本，这是fastapi连接层默认行为，只要不显式关就会默认打开，这里没打算细究现象，知道是原理复用tcp这一点即可