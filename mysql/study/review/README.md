# 主动回忆与间隔复习

## 推荐节奏

一个主题完成后，在第 1、3、7、14、30、90 天复习。每次复习先闭卷作答，再查看参考要点；只重新阅读不算复习。

在仓库根目录运行：

```bash
make -C mysql review-list
make -C mysql review
uv run --project . python mysql/study/scripts/review.py --topic index --count 5
```

脚本会逐题显示问题。按回车后才展示参考要点和对应实验。答错的问题应立即重跑实验，并在 `ROADMAP.md` 中降低掌握等级或记录新的复习日期。

## 15 分钟复习模板

1. 3 分钟：从记忆中画出主题知识地图。
2. 5 分钟：随机回答三道题。
3. 5 分钟：重跑一个关键 `EXPLAIN ANALYZE`。
4. 2 分钟：记录最薄弱的一点和下次复习日期。
