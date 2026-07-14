#!/bin/sh
set -eu
SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
. "$SCRIPT_DIR/../../scripts/lib.sh"
NS=k8s-study-01

reset_namespace "$NS"
$KUBECTL apply -n "$NS" -f - <<'YAML' >/dev/null
apiVersion: apps/v1
kind: Deployment
metadata:
  name: reconciler-demo
  labels: {app: reconciler-demo}
spec:
  replicas: 1
  selector:
    matchLabels: {app: reconciler-demo}
  template:
    metadata:
      labels: {app: reconciler-demo}
    spec:
      containers:
        - name: web
          image: busybox:1.37
          imagePullPolicy: IfNotPresent
          command: ["sh", "-c", "mkdir -p /www; echo reconciliation-ok >/www/index.html; exec httpd -f -p 8080 -h /www"]
          ports: [{name: http, containerPort: 8080}]
          readinessProbe:
            tcpSocket: {port: http}
            periodSeconds: 2
          resources:
            requests: {cpu: 10m, memory: 8Mi}
            limits: {cpu: 100m, memory: 32Mi}
YAML
wait_deployment "$NS" reconciler-demo
$KUBECTL scale deployment/reconciler-demo -n "$NS" --replicas=2 >/dev/null
wait_deployment "$NS" reconciler-demo

generation=$($KUBECTL get deployment reconciler-demo -n "$NS" -o jsonpath='{.metadata.generation}')
observed=$($KUBECTL get deployment reconciler-demo -n "$NS" -o jsonpath='{.status.observedGeneration}')
available=$($KUBECTL get deployment reconciler-demo -n "$NS" -o jsonpath='{.status.availableReplicas}')
assert_equal "$generation" "$observed" "控制器尚未观察到最新 generation"
assert_equal 2 "$available" "可用副本数不正确"
$KUBECTL get deployment,replicaset,pod -n "$NS" -o wide
printf '证据：spec.replicas=2，generation=%s，observedGeneration=%s，availableReplicas=%s。\n' "$generation" "$observed" "$available"
