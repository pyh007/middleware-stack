# 主动回忆与间隔复习

每次复习先闭卷，禁止先翻答案。默认在第一次学会后的第 1、3、7、14、30、90 天复习；连续两次能给出机制和证据才提高等级。

```bash
make -C kafka review-list
make -C kafka review
uv run --project . python kafka/study/scripts/review.py --topic delivery-semantics --count 3
uv run --project . python kafka/study/scripts/review.py --seed 42 --count 5 --no-wait
```

回答统一使用六段式：结论、机制、实验或指标证据、适用边界、副作用、生产验证。题库中的每道题都链接到已存在的实验、案例或 Runbook。

复习结束后在 [ROADMAP](../ROADMAP.md) 写实际日期和证据。答错机制题就重读模块；答错证据题就重跑实验；答错处置题就按 [生产排查 Runbook](../runbooks/diagnosis.md) 走一遍，不把重复阅读算成掌握。
