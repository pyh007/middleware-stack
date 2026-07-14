# Kubernetes 本地运行与学习入口

`k8s/` 是独立的基础设施学习主题。根目录保存集群命令入口和可部署运行清单，完整课程、练习、答案、复习与事故案例统一放在 [study/](study/README.md)。

当前运行环境使用本机 Docker Desktop Kubernetes；课程脚本默认只允许 `docker-desktop` 上下文，并把实验隔离在带 `middleware-stack.dev/study=true` 标签的 `k8s-study-*` Namespace。不会修改其他 Namespace，也不会停止 Docker Desktop。

```bash
make -C k8s help
make -C k8s up
make -C k8s all
```

`kafka/` 是可部署的单节点 Kafka/Kafka UI 运行清单，作为课程最终综合案例。它使用 `middleware-stack` Namespace 和持久卷，不包含在安全全量任务中。部署、重启或清理前应先阅读 [Kafka 运行说明](kafka/README.md)；课程侧的事故分析见 [Kafka 综合事故](study/cases/kafka-incident/README.md)。

集群级的节点中断、etcd 恢复、多节点升级不在当前单节点 Docker Desktop 默认课程中运行。它们需要单独、可销毁的集群，并且只能通过未来增加的显式命令执行。
