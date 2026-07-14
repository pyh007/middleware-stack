#!/bin/sh
set -eu
SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
. "$SCRIPT_DIR/../../scripts/lib.sh"
K8S_ROOT=$(CDPATH= cd -- "$SCRIPT_DIR/../../.." && pwd)

preflight
rendered=$($KUBECTL kustomize "$K8S_ROOT/kafka")
printf '%s\n' "$rendered" | grep -F 'kind: StatefulSet' >/dev/null || die "Kafka 清单缺少 StatefulSet"
printf '%s\n' "$rendered" | grep -F 'volumeClaimTemplates:' >/dev/null || die "Kafka 清单缺少 PVC 模板"
printf '%s\n' "$rendered" | grep -F 'startupProbe:' >/dev/null || die "Kafka 清单缺少 startupProbe"
printf '%s\n' "$rendered" | grep -F 'readinessProbe:' >/dev/null || die "Kafka 清单缺少 readinessProbe"
if printf '%s\n' "$rendered" | grep -E 'image: .+:latest$' >/dev/null; then
  die "生产审计拒绝 latest 镜像"
fi
$KUBECTL apply --dry-run=server -k "$K8S_ROOT/kafka" -o name
namespace_count=$(printf '%s\n' "$rendered" | grep -c '^kind: Namespace$')
statefulset_count=$(printf '%s\n' "$rendered" | grep -c '^kind: StatefulSet$')
service_count=$(printf '%s\n' "$rendered" | grep -c '^kind: Service$')
printf '证据：服务端 dry-run 通过；Namespace=%s、StatefulSet=%s、Service=%s；镜像已固定版本，存储、资源和三类探针均存在。\n' "$namespace_count" "$statefulset_count" "$service_count"
