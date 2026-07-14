#!/bin/sh
set -eu
SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
. "$SCRIPT_DIR/../../scripts/lib.sh"
K8S_ROOT=$(CDPATH= cd -- "$SCRIPT_DIR/../../.." && pwd)
NS=middleware-stack

preflight
printf '将应用 %s/kafka；不会删除既有 PVC。\n' "$K8S_ROOT"
$KUBECTL apply -k "$K8S_ROOT/kafka"
update_revision=$($KUBECTL get statefulset kafka -n "$NS" -o jsonpath='{.status.updateRevision}')
pod_revision=$($KUBECTL get pod kafka-0 -n "$NS" -o jsonpath='{.metadata.labels.controller-revision-hash}' 2>/dev/null || true)
if [ -n "$pod_revision" ] && [ "$pod_revision" != "$update_revision" ]; then
  printf '检测到 StatefulSet 更新停滞：Pod revision=%s，目标 revision=%s；重建 kafka-0，PVC 保留。\n' "$pod_revision" "$update_revision"
  $KUBECTL delete pod kafka-0 -n "$NS" --wait=true
fi
$KUBECTL rollout status statefulset/kafka -n "$NS" --timeout=300s
$KUBECTL rollout status deployment/kafka-ui -n "$NS" --timeout=300s
$KUBECTL exec kafka-0 -n "$NS" -- /opt/kafka/bin/kafka-topics.sh --bootstrap-server localhost:29092 --list
$KUBECTL get statefulset,deployment,pod,service,endpointslice,pvc -n "$NS" -o wide
printf '综合项目验证完成：Kafka/UI Ready，Kafka CLI 可访问；PVC 保留。\n'
