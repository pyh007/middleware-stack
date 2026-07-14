#!/bin/sh
set -eu
SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
. "$SCRIPT_DIR/lib.sh"

preflight
resources=$($KUBECTL get namespace -l "$STUDY_LABEL_KEY=$STUDY_LABEL_VALUE" -o name)
if [ -z "$resources" ]; then
  printf '没有需要清理的课程 Namespace。\n'
  exit 0
fi

for resource in $resources; do
  namespace=${resource#namespace/}
  assert_study_namespace "$namespace"
  $KUBECTL delete "$resource" --wait=true --timeout=120s
done
printf '已清理全部带课程标签的 k8s-study-* Namespace；其他 Namespace 未修改。\n'
