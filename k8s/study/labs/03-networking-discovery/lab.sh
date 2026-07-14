#!/bin/sh
set -eu
SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
. "$SCRIPT_DIR/../../scripts/lib.sh"
NS=k8s-study-03

reset_namespace "$NS"
$KUBECTL apply -n "$NS" -f - <<'YAML' >/dev/null
apiVersion: apps/v1
kind: Deployment
metadata: {name: web}
spec:
  replicas: 2
  selector:
    matchLabels: {app: web}
  template:
    metadata:
      labels: {app: web}
    spec:
      containers:
        - name: web
          image: busybox:1.37
          imagePullPolicy: IfNotPresent
          command: ["sh", "-c", "mkdir -p /www; echo service-discovery-ok >/www/index.html; exec httpd -f -p 8080 -h /www"]
          ports: [{name: http, containerPort: 8080}]
          readinessProbe: {tcpSocket: {port: http}, periodSeconds: 2}
          resources:
            requests: {cpu: 5m, memory: 4Mi}
            limits: {cpu: 50m, memory: 16Mi}
---
apiVersion: v1
kind: Service
metadata: {name: web}
spec:
  selector: {app: web}
  ports: [{name: http, port: 80, targetPort: http}]
---
apiVersion: v1
kind: Pod
metadata: {name: net-client}
spec:
  containers:
    - name: client
      image: busybox:1.37
      imagePullPolicy: IfNotPresent
      command: ["sh", "-c", "sleep 3600"]
      resources:
        requests: {cpu: 5m, memory: 4Mi}
        limits: {cpu: 50m, memory: 16Mi}
YAML
wait_deployment "$NS" web
$KUBECTL wait pod/net-client -n "$NS" --for=condition=Ready --timeout=60s >/dev/null
addresses=$($KUBECTL get endpointslice -n "$NS" -l kubernetes.io/service-name=web -o jsonpath='{range .items[*].endpoints[*]}{.addresses[0]}{"\n"}{end}')
count=$(printf '%s\n' "$addresses" | grep -c .)
assert_equal 2 "$count" "EndpointSlice 后端地址数不正确"
dns_output=$($KUBECTL exec -n "$NS" net-client -- nslookup web 2>&1 || true)
printf '%s\n' "$dns_output" | grep -F 'web.k8s-study-03.svc.cluster.local'
body=$($KUBECTL exec -n "$NS" net-client -- wget -qO- http://web)
assert_equal service-discovery-ok "$body" "Service 请求结果不正确"
$KUBECTL get service,endpointslice,pod -n "$NS" -o wide
printf '证据：DNS 解析成功，EndpointSlice 有 %s 个地址，Service 返回 %s。\n' "$count" "$body"
