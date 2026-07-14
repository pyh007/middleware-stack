#!/usr/bin/env python3
"""寻找一个 Redis Cluster Hash Tag，使键落入槽 0。"""

import binascii


for number in range(100_000):
    tag = f"slot-zero-{number}"
    if binascii.crc_hqx(tag.encode(), 0) % 16_384 == 0:
        print(tag)
        break
else:
    raise SystemExit("未在搜索范围内找到 slot 0 Hash Tag")
