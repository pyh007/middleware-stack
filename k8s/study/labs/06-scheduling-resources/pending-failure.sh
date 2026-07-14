#!/bin/sh
set -eu
SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
. "$SCRIPT_DIR/../../scripts/lib.sh"
NS=k8s-study-06-pending

reset_namespace "$NS"
$KUBECTL apply -n "$NS" -f - <<'YAML' >/dev/null
apiVersion: v1
kind: Pod
metadata: {name: impossible-request}
spec:
  restartPolicy: Never
  containers:
    - name: worker
      image: busybox:1.37
      command: ["sh", "-c", "sleep 3600"]
      resources:
        requests: {cpu: "500", memory: 8Mi}
        limits: {cpu: "500", memory: 16Mi}
YAML
if $KUBECTL wait pod/impossible-request -n "$NS" --for=condition=PodScheduled --timeout=10s >/dev/null 2>&1; then
  $KUBECTL delete pod impossible-request -n "$NS" --wait=true >/dev/null
  die "不可满足的 CPU request 竟然完成调度"
fi
reason=$($KUBECTL get pod impossible-request -n "$NS" -o jsonpath='{.status.conditions[?(@.type=="PodScheduled")].reason}')
assert_equal Unschedulable "$reason" "Pending 原因不正确"
$KUBECTL describe pod impossible-request -n "$NS" | sed -n '/Events:/,$p'
$KUBECTL delete pod impossible-request -n "$NS" --wait=true >/dev/null
$KUBECTL delete namespace "$NS" --wait=true --timeout=120s >/dev/null
printf '证据：超出节点容量的 request 导致 PodScheduled=False、reason=%s；证据采集后已清理隔离 Namespace。\n' "$reason"
