#!/bin/sh
set -eu
SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
. "$SCRIPT_DIR/../../scripts/lib.sh"
NS=k8s-study-01

preflight
assert_study_namespace "$NS"
pod=$($KUBECTL get pod -n "$NS" -l app=reconciler-demo -o jsonpath='{.items[0].metadata.name}')
uid=$($KUBECTL get pod "$pod" -n "$NS" -o jsonpath='{.metadata.uid}')
$KUBECTL delete pod "$pod" -n "$NS" --wait=true >/dev/null
wait_deployment "$NS" reconciler-demo
if $KUBECTL get pod -n "$NS" -l app=reconciler-demo -o jsonpath='{range .items[*]}{.metadata.uid}{"\n"}{end}' | grep -Fx "$uid" >/dev/null; then
  die "旧 Pod UID 仍然存在，未观察到替换"
fi
$KUBECTL get pod -n "$NS" -l app=reconciler-demo -o custom-columns='NAME:.metadata.name,UID:.metadata.uid,READY:.status.containerStatuses[0].ready'
printf '证据：被删除 Pod 的 UID=%s，Deployment 已创建新 Pod 恢复期望副本数。\n' "$uid"
