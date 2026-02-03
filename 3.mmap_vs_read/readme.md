## 100Mb:

read.py
normal read time: 0.04393267631530762
data size: 104857600

mmap.py
mmap time: 0.0
first 10 bytes: b'\x96\xd6p\x96k$\xcc`M~'

## 800Mb:

read.py
normal read time: 0.03081798553466797
data size: 104857600

mmap.py'
mmap time: 0.0005040168762207031
first 10 bytes: b'\x96\xd6p\x96k$\xcc`M~'

## 结论
可以看出mmap因为几乎没读数据只建映射，所以打开速度极快

并且read直接读取全部，立刻占用了100/800Mb
mmap只占用访问到的page

所以文件越大，mmap优势越明显

## 所以为什么模型权重常用mmap加载

模型权重很大、只读、按需访问，用 mmap 可以避免一次性拷贝，减少内存占用，并让多个进程共享同一份权重页。