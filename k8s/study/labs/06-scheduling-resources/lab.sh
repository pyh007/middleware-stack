#!/bin/sh
set -eu
SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
. "$SCRIPT_DIR/../../scripts/lib.sh"
NS=k8s-study-06

reset_namespace "$NS"
$KUBECTL apply -n "$NS" -f - <<'YAML' >/dev/null
apiVersion: v1
kind: LimitRange
metadata: {name: defaults}
spec:
  limits:
    - type: Container
      defaultRequest: {cpu: 10m, memory: 8Mi}
      default: {cpu: 100m, memory: 32Mi}
---
apiVersion: v1
kind: ResourceQuota
metadata: {name: study-quota}
spec:
  hard:
    requests.cpu: "1"
    requests.memory: 256Mi
    limits.cpu: "2"
    limits.memory: 512Mi
    pods: "10"
---
apiVersion: apps/v1
kind: Deployment
metadata: {name: resource-demo}
spec:
  replicas: 1
  selector:
    matchLabels: {app: resource-demo}
  template:
    metadata:
      labels: {app: resource-demo}
    spec:
      containers:
        - name: worker
          image: busybox:1.37
          imagePullPolicy: IfNotPresent
          command: ["sh", "-c", "sleep 3600"]
          resources:
            requests: {cpu: 20m, memory: 8Mi}
            limits: {cpu: 100m, memory: 32Mi}
YAML
wait_deployment "$NS" resource-demo
pod=$($KUBECTL get pod -n "$NS" -l app=resource-demo -o jsonpath='{.items[0].metadata.name}')
node=$($KUBECTL get pod "$pod" -n "$NS" -o jsonpath='{.spec.nodeName}')
qos=$($KUBECTL get pod "$pod" -n "$NS" -o jsonpath='{.status.qosClass}')
request_cpu=$($KUBECTL get pod "$pod" -n "$NS" -o jsonpath='{.spec.containers[0].resources.requests.cpu}')
limit_cpu=$($KUBECTL get pod "$pod" -n "$NS" -o jsonpath='{.spec.containers[0].resources.limits.cpu}')
assert_equal Burstable "$qos" "Pod QoS 不正确"
assert_equal 20m "$request_cpu" "CPU request 不正确"
assert_equal 100m "$limit_cpu" "CPU limit 不正确"
[ -n "$node" ] || die "Pod 尚未绑定节点"
$KUBECTL get resourcequota,limitrange,pod -n "$NS"
printf '证据：Pod 调度到 %s，QoS=%s，CPU request=%s、limit=%s。\n' "$node" "$qos" "$request_cpu" "$limit_cpu"
