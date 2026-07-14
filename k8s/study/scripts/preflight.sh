#!/bin/sh
set -eu
SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
. "$SCRIPT_DIR/lib.sh"

preflight
$KUBECTL get nodes -o custom-columns='NAME:.metadata.name,READY:.status.conditions[?(@.type=="Ready")].status,VERSION:.status.nodeInfo.kubeletVersion'
printf '课程 Namespace：\n'
$KUBECTL get namespace -l "$STUDY_LABEL_KEY=$STUDY_LABEL_VALUE" --no-headers 2>/dev/null || true
