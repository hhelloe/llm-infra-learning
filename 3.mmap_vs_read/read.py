# read_normal.py
import time

FILE = "test_100mb.bin"

start = time.time()
with open(FILE, "rb") as f:
    data = f.read()   # 整个文件进内存
end = time.time()

print("normal read time:", end - start)
print("data size:", len(data))
