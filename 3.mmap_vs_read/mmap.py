import mmap
import time

FILE = "test_100mb.bin"

start = time.time()
with open(FILE, "rb") as f:
    mm = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)
    # 访问一下，确保真的用到
    first_10 = mm[:10]
end = time.time()

print("mmap time:", end - start)
print("first 10 bytes:", first_10)

mm.close()
