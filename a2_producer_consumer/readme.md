终端输出类似于
[stream] rid=17 from worker-2 token=T10
[stream] rid=19 from worker-0 token=T2
[stream] rid=18 from worker-1 token=T6
[stream] rid=16 from worker-3 token=T14
[stream] rid=19 from worker-0 token=T3
[stream] rid=17 from worker-2 token=T11
[stream] rid=16 from worker-3 token=T15
[stream] rid=18 from worker-1 token=T7
[stream] rid=19 from worker-0 token=T4
[stream] rid=17 from worker-2 token=T12
[stream] rid=16 from worker-3 token=T16
[stream] rid=18 from worker-1 token=T8
[stream] rid=19 from worker-0 token=T5
[stream] rid=17 from worker-2 token=T13
[stream] rid=16 from worker-3 token=T17
[stream] rid=16 from worker-3 token=T18
[stream] rid=18 from worker-1 token=T9
[stream] rid=19 from worker-0 token=T6
[stream] rid=17 from worker-2 token=T14
[stream] rid=17 from worker-2 token=T15
[stream] rid=19 from worker-0 token=T7
[stream] rid=16 from worker-3 token=T19
[stream] rid=18 from worker-1 token=T10
[stream] rid=17 from worker-2 token=T16
[stream] rid=19 from worker-0 token=T8
[stream] rid=18 from worker-1 token=T11
[stream] rid=16 from worker-3 token=T20
[stream] rid=17 from worker-2 token=T17
[stream] rid=17 from worker-2 DONE (17/20)
[stream] rid=18 from worker-1 token=T12
[stream] rid=19 from worker-0 token=T9
[stream] rid=16 from worker-3 token=T21
[stream] rid=16 from worker-3 DONE (18/20)
[stream] rid=18 from worker-1 token=T13
[stream] rid=19 from worker-0 token=T10
[worker-2] stop[worker-1] stop
[worker-0] stop[stream] rid=19 from worker-0 DONE (19/20)
[worker-3] stop

[stream] rid=18 from worker-1 token=T14

[stream] rid=18 from worker-1 DONE (20/20)
ALL DONE

直接写结论了
程序实际上是多线程并发，worker函数中我用sleep（模拟I/O等待）让worker休眠之后立马就有别的worker开始工作，这就是threading的意义
但threading在特别高压的情况用于streaming不如async，因为async每个工作只挂在协程上，非常轻量，等待时占用少，threading每个工作挂在线程上，如果工作太多占用会很大