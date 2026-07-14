#!/bin/sh
set -eu
SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
. "$SCRIPT_DIR/../../scripts/lib.sh"
NS=middleware-stack

preflight
if ! $KUBECTL get namespace "$NS" >/dev/null 2>&1; then
  printf 'Kafka Namespace %s 不存在；先执行显式部署命令。\n' "$NS"
  exit 2
fi
$KUBECTL get statefulset,deployment,pod,service,endpointslice,pvc -n "$NS" -o wide
printf '\n最近 Events：\n'
$KUBECTL get events -n "$NS" --sort-by=.lastTimestamp | tail -n 20
ready=$($KUBECTL get statefulset kafka -n "$NS" -o jsonpath='{.status.readyReplicas}' 2>/dev/null || true)
if [ "${ready:-0}" != 1 ]; then
  printf '\nKafka 未就绪；上一实例日志：\n' >&2
  $KUBECTL logs kafka-0 -n "$NS" --previous --tail=80 2>&1 || $KUBECTL logs kafka-0 -n "$NS" --tail=80 2>&1 || true
  exit 2
fi
printf 'Kafka StatefulSet Ready=1。继续验证 Topic 与消息读写。\n'
