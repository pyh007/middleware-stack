# 主动回忆与间隔复习

一个主题完成后，在大约第 1、3、7、14、30、90 天复习。每次先闭卷作答，再查看参考要点。

```bash
python {{STUDY_RELATIVE}}/scripts/review.py --list-topics
python {{STUDY_RELATIVE}}/scripts/review.py --count 3
```

答错的问题应立即重跑关联实验，并在 `ROADMAP.md` 更新掌握等级和下次日期。
