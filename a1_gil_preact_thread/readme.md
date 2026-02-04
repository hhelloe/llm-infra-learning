## n = 600000的输出
=== ThreadPoolExecutor | workers=1 | chunks=32 | n=600000 | pid=150580 ===
total primes = 49098
elapsed = 0.519s
parent process cpu% (approx) = 81.2%

=== ThreadPoolExecutor | workers=8 | chunks=32 | n=600000 | pid=150580 ===
total primes = 49098
elapsed = 0.869s
parent process cpu% (approx) = 0.0%

=== ProcessPoolExecutor | workers=8 | chunks=32 | n=600000 | pid=150580 ===
total primes = 49098
elapsed = 0.540s
parent process cpu% (approx) = 0.0%

## n=1200000的输出
=== ThreadPoolExecutor | workers=1 | chunks=32 | n=1200000 | pid=295300 ===
total primes = 92938
elapsed = 1.361s
parent process cpu% (approx) = 84.8%

=== ThreadPoolExecutor | workers=8 | chunks=32 | n=1200000 | pid=295300 ===
total primes = 92938
elapsed = 1.360s
parent process cpu% (approx) = 15.1%

=== ProcessPoolExecutor | workers=8 | chunks=32 | n=1200000 | pid=295300 ===
total primes = 92938
elapsed = 0.548s
parent process cpu% (approx) = 0.0%

## 分析
理论上说，并行的话应该会节省时间，但是在n=600000的时候不仅没有节省时间，而且线程并行和进程并行都变慢了
发现实际上是因为多进程的管理开销 > 并行带来的收益
于是我把n调大，改为800000但仍然不理想，最后继续调大改成1200000结果就符合预期了:
进程并行显著节省了时间（从1.361s跑完变成了0.548秒），线程并行无明显变化（1.361s和1.360s几乎无差别）
结论让人能直观的认识到python的gil（全局解释器锁）规定Python在同一时刻只允许一个线程执行Python字节码

## Addition
上述cpu利用率在并行时显得非常低，发现是因为只监控了父进程，于是写了一个函数监视子进程和父进程之和（变量名未修改，parent process其实是进程父子之和）
=== ThreadPoolExecutor | workers=1 | chunks=32 | n=1200000 | pid=146184 ===
total primes = 92938
elapsed = 1.317s
parent process cpu% (approx) = 70.6%

=== ThreadPoolExecutor | workers=8 | chunks=32 | n=1200000 | pid=146184 ===
total primes = 92938
elapsed = 1.366s
parent process cpu% (approx) = 5.6%

=== ProcessPoolExecutor | workers=8 | chunks=32 | n=1200000 | pid=146184 ===
total primes = 92938
elapsed = 0.567s
parent process cpu% (approx) = 231.3%

## 结论
n 小，多进程不快反慢，n 大，多进程显著加速；多线程始终不加速甚至变慢。

这里能看出进程并行跑了大约2.3个核，如果要吃满更多核,大概需要解决下面的问题

任务太短（0.567s 级别，进程启动/IPC 占比大）
chunks=32 太碎（IPC + Future 收集开销）
负载不均（后段数字更大、判素更慢，尾部拖尾导致部分 worker 空等）
上三行，为ai生成的可能情况

所以线程在 CPython 下很难稳定吃满多核，还共享故障域；多进程能真并行、好隔离、好运维，所以推理服务更常用多进程。