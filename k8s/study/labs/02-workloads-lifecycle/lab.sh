#!/bin/sh
set -eu
SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
. "$SCRIPT_DIR/../../scripts/lib.sh"
NS=k8s-study-02

reset_namespace "$NS"
$KUBECTL apply -n "$NS" -f - <<'YAML' >/dev/null
apiVersion: apps/v1
kind: Deployment
metadata: {name: lifecycle-web}
spec:
  replicas: 1
  selector:
    matchLabels: {app: lifecycle-web}
  template:
    metadata:
      labels: {app: lifecycle-web}
    spec:
      containers:
        - name: web
          image: busybox:1.37
          imagePullPolicy: IfNotPresent
          command: ["sh", "-c", "mkdir -p /www; echo release-$RELEASE >/www/index.html; exec httpd -f -p 8080 -h /www"]
          env: [{name: RELEASE, value: v1}]
          ports: [{name: http, containerPort: 8080}]
          startupProbe:
            tcpSocket: {port: http}
            periodSeconds: 1
            failureThreshold: 30
          readinessProbe:
            httpGet: {path: /, port: http}
            periodSeconds: 2
          livenessProbe:
            tcpSocket: {port: http}
            periodSeconds: 10
          resources:
            requests: {cpu: 10m, memory: 8Mi}
            limits: {cpu: 100m, memory: 32Mi}
---
apiVersion: batch/v1
kind: Job
metadata: {name: lifecycle-job}
spec:
  template:
    spec:
      restartPolicy: Never
      containers:
        - name: worker
          image: busybox:1.37
          imagePullPolicy: IfNotPresent
          command: ["sh", "-c", "echo job-completed-with-exit-0"]
          resources:
            requests: {cpu: 5m, memory: 4Mi}
            limits: {cpu: 50m, memory: 16Mi}
YAML
wait_deployment "$NS" lifecycle-web
$KUBECTL wait job/lifecycle-job -n "$NS" --for=condition=complete --timeout=60s >/dev/null
$KUBECTL set env deployment/lifecycle-web -n "$NS" RELEASE=v2 >/dev/null
wait_deployment "$NS" lifecycle-web
revision=$($KUBECTL get deployment lifecycle-web -n "$NS" -o jsonpath='{.metadata.annotations.deployment\.kubernetes\.io/revision}')
[ "$revision" -ge 2 ] || die "Deployment revision 没有增加"
$KUBECTL get deployment,replicaset,pod,job -n "$NS"
$KUBECTL logs job/lifecycle-job -n "$NS" | grep -F 'job-completed-with-exit-0'
printf '证据：Deployment 已滚动到 revision=%s；Job condition=Complete。\n' "$revision"
