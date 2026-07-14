# 生产审计与综合项目参考答案

1. 先看 PodScheduled 与 PVC Bound，再看 image pull Events、容器 waiting/lastState、`logs --previous`、配置引用和探针失败。按数据路径排除层次，避免一开始修改多个参数。节点磁盘、内存和 inode 也要与容器错误对应。
2. 控制器只恢复进程数量。消息是否丢失取决于写入确认、日志是否已持久化、PVC 可用性、Kafka 复制与 ISR、controller 元数据和客户端重试语义。
3. 缺少 Broker 和 Controller 多副本、故障域分散、ISR 保障、滚动升级验证、容量冗余、监控告警、安全认证、备份恢复与故障演练。PVC 只解决一个存储生命周期问题。
4. 以环境变量注入的 ConfigMap 只在容器启动时读取。应把配置变更作为版本化发布，先 diff 和兼容检查，触发受控 rollout，观察 Kafka 健康与业务指标；保留旧配置和清晰的回滚步骤。
5. tag 仍可能被仓库重新指向其他内容，digest 才能唯一标识镜像字节。生产还需漏洞扫描、签名验证、来源限制和升级流程。
6. Kubernetes 层验证副本、Ready、重启、Events、资源和 PVC；Kafka 层验证 controller/broker、Topic、读写、offset 与日志；业务层验证成功率、延迟、积压和数据一致性，并确认告警恢复、回滚可用及 RPO/RTO 满足目标。
