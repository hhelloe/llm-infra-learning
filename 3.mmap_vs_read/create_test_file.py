# create_test_file.py
import os

FILE = "test_100mb.bin"
SIZE = 800 * 1024 * 1024  # 100MB

if not os.path.exists(FILE):
    with open(FILE, "wb") as f:
        f.write(os.urandom(SIZE))

print("file ready:", FILE)