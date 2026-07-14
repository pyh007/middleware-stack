#!/bin/sh
set -eu

KUBECTL=${KUBECTL:-kubectl}
STUDY_LABEL_KEY=middleware-stack.dev/study
STUDY_LABEL_VALUE=true

die() {
  printf 'ERROR: %s\n' "$*" >&2
  exit 1
}

preflight() {
  command -v "$KUBECTL" >/dev/null 2>&1 || die "找不到 kubectl"
  context=$($KUBECTL config current-context 2>/dev/null) || die "无法读取 kubectl 上下文"
  allowed=${K8S_STUDY_ALLOWED_CONTEXTS:-docker-desktop}
  case ",$allowed," in
    *",$context,"*) ;;
    *) die "当前上下文为 $context；允许列表为 $allowed。若它确实是可销毁的本地集群，请显式设置 K8S_STUDY_ALLOWED_CONTEXTS" ;;
  esac
  $KUBECTL get --raw=/readyz >/dev/null 2>&1 || die "API Server 未就绪"
  printf '上下文=%s，API Server=Ready\n' "$context"
}

guard_namespace_name() {
  case "$1" in
    k8s-study-*) ;;
    *) die "拒绝操作非课程 Namespace：$1" ;;
  esac
}

assert_study_namespace() {
  namespace=$1
  guard_namespace_name "$namespace"
  value=$($KUBECTL get namespace "$namespace" -o "jsonpath={.metadata.labels['middleware-stack\\.dev/study']}" 2>/dev/null || true)
  [ "$value" = "$STUDY_LABEL_VALUE" ] || die "Namespace $namespace 缺少课程标签，拒绝修改"
}

create_namespace() {
  namespace=$1
  guard_namespace_name "$namespace"
  $KUBECTL create namespace "$namespace" --dry-run=client -o yaml | $KUBECTL apply -f - >/dev/null
  $KUBECTL label namespace "$namespace" "$STUDY_LABEL_KEY=$STUDY_LABEL_VALUE" purpose=learning --overwrite >/dev/null
}

reset_namespace() {
  namespace=$1
  preflight
  guard_namespace_name "$namespace"
  if $KUBECTL get namespace "$namespace" >/dev/null 2>&1; then
    assert_study_namespace "$namespace"
    $KUBECTL delete namespace "$namespace" --wait=true --timeout=120s >/dev/null
  fi
  create_namespace "$namespace"
  printf '已重建隔离 Namespace：%s\n' "$namespace"
}

wait_deployment() {
  namespace=$1
  name=$2
  $KUBECTL rollout status "deployment/$name" -n "$namespace" --timeout=120s
}

assert_equal() {
  expected=$1
  actual=$2
  message=$3
  [ "$expected" = "$actual" ] || die "${message}：期望 $expected，实际 $actual"
}
