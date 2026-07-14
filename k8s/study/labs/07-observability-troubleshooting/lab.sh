#!/bin/sh
set -eu
SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
. "$SCRIPT_DIR/../../scripts/lib.sh"
NS=k8s-study-07

reset_namespace "$NS"
$KUBECTL apply -n "$NS" -f - <<'YAML' >/dev/null
apiVersion: apps/v1
kind: Deployment
metadata: {name: observable-web}
spec:
  replicas: 1
  selector:
    matchLabels: {app: observable-web}
  template:
    metadata:
      labels: {app: observable-web}
    spec:
      containers:
        - name: web
          image: busybox:1.37
          imagePullPolicy: IfNotPresent
          command: ["sh", "-c", "mkdir -p /www; echo observable-ok >/www/index.html; echo app-started port=8080; exec httpd -f -p 8080 -h /www"]
          ports: [{name: http, containerPort: 8080}]
          readinessProbe: {tcpSocket: {port: http}, periodSeconds: 2}
          resources:
            requests: {cpu: 5m, memory: 4Mi}
            limits: {cpu: 50m, memory: 16Mi}
---
apiVersion: v1
kind: Service
metadata: {name: observable-web}
spec:
  selector: {app: observable-web}
  ports: [{port: 80, targetPort: http}]
---
apiVersion: v1
kind: Pod
metadata: {name: observer}
spec:
  containers:
    - name: observer
      image: busybox:1.37
      imagePullPolicy: IfNotPresent
      command: ["sh", "-c", "until body=$(wget -qO- http://observable-web); do sleep 1; done; echo request=GET response=$body; sleep 3600"]
      resources:
        requests: {cpu: 5m, memory: 4Mi}
        limits: {cpu: 50m, memory: 16Mi}
YAML
wait_deployment "$NS" observable-web
$KUBECTL wait pod/observer -n "$NS" --for=condition=Ready --timeout=60s >/dev/null
response=$($KUBECTL exec -n "$NS" observer -- wget -qO- http://observable-web)
assert_equal observable-ok "$response" "端到端请求失败"
pod=$($KUBECTL get pod -n "$NS" -l app=observable-web -o jsonpath='{.items[0].metadata.name}')
logs=$($KUBECTL logs "$pod" -n "$NS")
printf '%s\n' "$logs" | grep -F 'app-started port=8080' >/dev/null || die "服务端日志中没有启动证据"
i=0
observer_logs=''
while [ "$i" -lt 30 ]; do
  observer_logs=$($KUBECTL logs observer -n "$NS" 2>/dev/null || true)
  printf '%s\n' "$observer_logs" | grep -F 'request=GET response=observable-ok' >/dev/null && break
  i=$((i + 1))
  sleep 1
done
printf '%s\n' "$observer_logs" | grep -F 'request=GET response=observable-ok' >/dev/null || die "调用方日志中没有请求证据"
$KUBECTL get deployment,pod,service,endpointslice -n "$NS" -o wide
$KUBECTL get events -n "$NS" --sort-by=.lastTimestamp | tail -n 12
printf '应用日志：\n%s\n' "$logs"
printf '调用日志：\n%s\n' "$observer_logs"
printf '证据：业务响应=%s；状态、端点、Events 和应用访问日志构成完整观察链。\n' "$response"
