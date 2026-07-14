#!/bin/sh
set -eu
SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
. "$SCRIPT_DIR/../../scripts/lib.sh"
NS=k8s-study-03

preflight
assert_study_namespace "$NS"
$KUBECTL patch service web -n "$NS" --type=merge -p '{"spec":{"selector":{"app":"missing"}}}' >/dev/null
i=0
while [ "$i" -lt 30 ]; do
  addresses=$($KUBECTL get endpointslice -n "$NS" -l kubernetes.io/service-name=web -o jsonpath='{range .items[*].endpoints[*]}{.addresses[0]}{"\n"}{end}' 2>/dev/null || true)
  [ -z "$addresses" ] && break
  i=$((i + 1))
  sleep 1
done
[ -z "$addresses" ] || die "错误 selector 下仍然存在 EndpointSlice 地址"
printf '故障证据：Service 存在，但 EndpointSlice 没有后端地址。\n'
$KUBECTL get service,endpointslice -n "$NS" -o wide
$KUBECTL patch service web -n "$NS" --type=merge -p '{"spec":{"selector":{"app":"web"}}}' >/dev/null
i=0
while [ "$i" -lt 30 ]; do
  addresses=$($KUBECTL get endpointslice -n "$NS" -l kubernetes.io/service-name=web -o jsonpath='{range .items[*].endpoints[*]}{.addresses[0]}{"\n"}{end}' 2>/dev/null || true)
  [ -n "$addresses" ] && break
  i=$((i + 1))
  sleep 1
done
[ -n "$addresses" ] || die "恢复 selector 后 EndpointSlice 未恢复"
printf '恢复证据：selector=app:web，EndpointSlice 地址重新出现。\n'
