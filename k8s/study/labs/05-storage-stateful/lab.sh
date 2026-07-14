#!/bin/sh
set -eu
SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
. "$SCRIPT_DIR/../../scripts/lib.sh"
NS=k8s-study-05

reset_namespace "$NS"
$KUBECTL apply -n "$NS" -f - <<'YAML' >/dev/null
apiVersion: v1
kind: PersistentVolumeClaim
metadata: {name: study-data}
spec:
  accessModes: ["ReadWriteOnce"]
  resources:
    requests: {storage: 64Mi}
---
apiVersion: batch/v1
kind: Job
metadata: {name: writer}
spec:
  template:
    spec:
      restartPolicy: Never
      containers:
        - name: writer
          image: busybox:1.37
          imagePullPolicy: IfNotPresent
          command: ["sh", "-c", "printf persistent-evidence-v1 >/data/evidence.txt; sync; cat /data/evidence.txt"]
          volumeMounts: [{name: data, mountPath: /data}]
          resources:
            requests: {cpu: 5m, memory: 4Mi}
            limits: {cpu: 50m, memory: 16Mi}
      volumes:
        - name: data
          persistentVolumeClaim: {claimName: study-data}
YAML
$KUBECTL wait job/writer -n "$NS" --for=condition=complete --timeout=120s >/dev/null
$KUBECTL apply -n "$NS" -f - <<'YAML' >/dev/null
apiVersion: v1
kind: Pod
metadata: {name: reader}
spec:
  restartPolicy: Never
  containers:
    - name: reader
      image: busybox:1.37
      imagePullPolicy: IfNotPresent
      command: ["sh", "-c", "value=$(cat /data/evidence.txt); echo $value; sleep 3600"]
      volumeMounts: [{name: data, mountPath: /data}]
      resources:
        requests: {cpu: 5m, memory: 4Mi}
        limits: {cpu: 50m, memory: 16Mi}
  volumes:
    - name: data
      persistentVolumeClaim: {claimName: study-data}
YAML
$KUBECTL wait pod/reader -n "$NS" --for=condition=Ready --timeout=120s >/dev/null
phase=$($KUBECTL get pvc study-data -n "$NS" -o jsonpath='{.status.phase}')
assert_equal Bound "$phase" "PVC 未绑定"
evidence=$($KUBECTL logs reader -n "$NS")
assert_equal persistent-evidence-v1 "$evidence" "读取到的持久化内容不正确"
$KUBECTL get pvc,pod,job -n "$NS" -o wide
printf '证据：PVC=%s；writer 完成后，独立 reader 读取到 %s。\n' "$phase" "$evidence"
