# 可观测性与排障参考答案

1. get 看对象概要和 condition，describe 汇总配置、状态与相关 Events，Events 给出调度和 kubelet 等离散原因，logs 看进程行为，metrics 看趋势和饱和度，traces 串联一次请求跨服务耗时。必须与业务症状和时间窗口对应。
2. CrashLoop 中当前容器可能刚启动尚无关键输出，真正退出原因留在上一实例。`--previous` 可读取同一 Pod 中前一个容器实例日志，再结合 lastState、exitCode、OOMKilled 和 Events 判断。
3. 不能。Events 会聚合并过期，保留期有限，也不是完整审计。事故开始应保存 YAML、describe、Events、相关日志、版本和变更时间线，但注意脱敏。
4. 在调用方验证 DNS，再看 Service 配置与 EndpointSlice 是否有 Ready 地址，核对 port/targetPort 和容器监听，最后直连端点或从同网络路径请求应用。每步只改变一个变量。
5. 重启可能暂时释放资源或清除错误状态，但会丢失现场且根因可能复发。重启前保存时间线、状态、日志、资源和变更；重启后验证业务、数据一致性、资源趋势并继续根因分析。
6. 用户 ID、URL、Pod UID 等高基数字段会让时序数量和查询成本爆炸。应限定标签集合，把高基数信息放日志/追踪，设置采集预算、丢弃规则和监控平台告警。
