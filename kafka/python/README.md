# Kafka Python 学习脚本

这里使用 `confluent-kafka` 分别演示 Topic 管理、消息生产、订阅消费、消费者组和 Offset 提交。脚本默认从宿主机连接 `localhost:9092`。

## 准备环境

在仓库根目录执行：

```bash
docker compose -f kafka/docker-compose.yml up -d
uv sync
```

如果不用 `uv`，也可以激活 Python 3.12 虚拟环境后执行 `pip install confluent-kafka`。

## 推荐学习顺序

所有命令都在仓库根目录执行。

1. 查看和创建 Topic：

   ```bash
   uv run python kafka/python/admin.py list
   uv run python kafka/python/admin.py create
   uv run python kafka/python/admin.py describe
   ```

2. 运行端到端演示：

   ```bash
   uv run python kafka/python/demo.py --count 5
   ```

3. 打开两个终端观察实时订阅。先启动消费者：

   ```bash
   uv run python kafka/python/consumer.py --from-beginning
   ```

   再在另一个终端发送消息：

   ```bash
   uv run python kafka/python/producer.py --count 10 --interval 0.5
   ```

4. 使用同一个消费者组运行两个消费者，观察三个分区如何在组成员间分配：

   ```bash
   uv run python kafka/python/consumer.py --group shared-learning-group
   ```

5. 换一个全新的 `--group` 并增加 `--from-beginning`，观察不同消费者组可以独立消费同一批消息。

## 常用参数与清理

用 `--help` 查看每个脚本的参数。例如消费 5 条后退出：

```bash
uv run python kafka/python/consumer.py --group test-001 --from-beginning --max-messages 5
```

删除学习 Topic 会同时删除其中的消息，必须显式确认：

```bash
uv run python kafka/python/admin.py delete --topic learning-events --yes
```

连接其他 Kafka 时可覆盖环境变量：

```bash
KAFKA_BOOTSTRAP_SERVERS=192.168.1.10:9092 uv run python kafka/python/admin.py list
```
