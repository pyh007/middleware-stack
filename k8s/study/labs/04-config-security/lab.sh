#!/bin/sh
set -eu
SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
. "$SCRIPT_DIR/../../scripts/lib.sh"
NS=k8s-study-04

reset_namespace "$NS"
$KUBECTL apply -n "$NS" -f - <<'YAML' >/dev/null
apiVersion: v1
kind: ConfigMap
metadata: {name: app-config}
data: {APP_MODE: learning}
---
apiVersion: v1
kind: Secret
metadata: {name: local-secret}
type: Opaque
stringData: {LOCAL_TOKEN: local-only-token}
---
apiVersion: v1
kind: ServiceAccount
metadata: {name: config-reader}
---
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata: {name: config-reader}
rules:
  - apiGroups: [""]
    resources: ["configmaps"]
    verbs: ["get", "list"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata: {name: config-reader}
subjects:
  - kind: ServiceAccount
    name: config-reader
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: Role
  name: config-reader
---
apiVersion: v1
kind: Pod
metadata: {name: secure-app}
spec:
  serviceAccountName: config-reader
  automountServiceAccountToken: false
  securityContext:
    runAsNonRoot: true
    runAsUser: 65534
    seccompProfile: {type: RuntimeDefault}
  restartPolicy: Never
  containers:
    - name: app
      image: busybox:1.37
      imagePullPolicy: IfNotPresent
      command: ["sh", "-c", "echo mode=$APP_MODE; echo token-length=${#LOCAL_TOKEN}; sleep 3600"]
      envFrom:
        - configMapRef: {name: app-config}
        - secretRef: {name: local-secret}
      securityContext:
        allowPrivilegeEscalation: false
        capabilities: {drop: ["ALL"]}
      resources:
        requests: {cpu: 5m, memory: 4Mi}
        limits: {cpu: 50m, memory: 16Mi}
YAML
$KUBECTL wait pod/secure-app -n "$NS" --for=condition=Ready --timeout=60s >/dev/null
logs=$($KUBECTL logs secure-app -n "$NS")
printf '%s\n' "$logs" | grep -F 'mode=learning'
printf '%s\n' "$logs" | grep -F 'token-length=16'
identity="system:serviceaccount:$NS:config-reader"
can_config=$($KUBECTL auth can-i list configmaps -n "$NS" --as="$identity")
can_secret=$($KUBECTL auth can-i get secrets -n "$NS" --as="$identity" || true)
assert_equal yes "$can_config" "ServiceAccount 应能列出 ConfigMap"
assert_equal no "$can_secret" "ServiceAccount 不应读取 Secret"
$KUBECTL get serviceaccount,role,rolebinding,pod -n "$NS"
printf '证据：配置进入容器；RBAC 对 ConfigMap=%s，对 Secret=%s；容器禁用提权并丢弃 capabilities。\n' "$can_config" "$can_secret"
