#!/usr/bin/env python3
"""只清理 lab:redis: 前缀的课程数据。"""

from lab_common import LAB_PREFIX, cleanup_prefix, redis_client


def main() -> None:
    client = redis_client()
    try:
        deleted = cleanup_prefix(client)
        remaining = sum(1 for _ in client.scan_iter(match=f"{LAB_PREFIX}*"))
        if remaining:
            raise RuntimeError(f"重置后仍有 {remaining} 个实验键")
        print(f"安全重置完成：删除 {deleted} 个 {LAB_PREFIX}* 键，其他键未触碰。")
    finally:
        client.close()


if __name__ == "__main__":
    main()
