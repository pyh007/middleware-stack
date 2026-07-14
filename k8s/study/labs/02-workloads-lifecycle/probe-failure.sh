#!/bin/sh
set -eu
SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
. "$SCRIPT_DIR/../../scripts/lib.sh"
NS=k8s-study-02

preflight
assert_study_namespace "$NS"
$KUBECTL scale deployment/lifecycle-web -n "$NS" --replicas=0 >/dev/null
$KUBECTL wait pod -n "$NS" -l app=lifecycle-web --for=delete --timeout=60s >/dev/null 2>&1 || true
$KUBECTL patch deployment lifecycle-web -n "$NS" --type=strategic -p '{"spec":{"template":{"spec":{"containers":[{"name":"web","readinessProbe":{"httpGet":{"path":"/missing","port":"http"}}}]}}}}' >/dev/null
$KUBECTL scale deployment/lifecycle-web -n "$NS" --replicas=1 >/dev/null
$KUBECTL wait pod -n "$NS" -l app=lifecycle-web --for=jsonpath='{.status.phase}'=Running --timeout=60s >/dev/null
if $KUBECTL wait pod -n "$NS" -l app=lifecycle-web --for=condition=Ready --timeout=10s >/dev/null 2>&1; then
  die "错误 readinessProbe 未使 rollout 失败"
fi
ready=$($KUBECTL get pod -n "$NS" -l app=lifecycle-web -o jsonpath='{.items[0].status.containerStatuses[0].ready}')
assert_equal false "$ready" "错误 readinessProbe 下容器不应 Ready"
$KUBECTL get pod -n "$NS" -l app=lifecycle-web -o custom-columns='NAME:.metadata.name,PHASE:.status.phase,READY:.status.containerStatuses[0].ready'
$KUBECTL get events -n "$NS" --sort-by=.lastTimestamp | tail -n 12
$KUBECTL patch deployment lifecycle-web -n "$NS" --type=strategic -p '{"spec":{"template":{"spec":{"containers":[{"name":"web","readinessProbe":{"httpGet":{"path":"/","port":"http"}}}]}}}}' >/dev/null
wait_deployment "$NS" lifecycle-web
printf '证据：错误 readiness 路径阻止 Pod Ready；恢复路径后 rollout 成功。\n'
