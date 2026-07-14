# 可观测性与排障练习题

1. get、describe、Events、logs、metrics 和 traces 分别最适合回答什么问题？
2. Pod CrashLoopBackOff 时，为什么 `kubectl logs --previous` 经常比当前日志更关键？
3. Events 能否作为长期审计记录？为什么事故现场要尽早保存？
4. Service 请求失败时，如何用最短证据链区分 DNS、端点、端口和应用错误？
5. 为什么“重启后恢复”不等于事故已经解决？重启前后各要记录什么？
6. 指标标签基数失控会带来什么生产问题，如何治理？
