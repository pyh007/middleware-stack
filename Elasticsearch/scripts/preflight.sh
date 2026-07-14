#!/bin/sh
# Elasticsearch 根课程环境启动前检查。
set -eu

ES_VERSION=${ES_VERSION:-9.4.3-arm64}
ES_PORT=${ES_PORT:-9200}
KIBANA_PORT=${KIBANA_PORT:-5601}
ES_REQUIRED_DISK_GB=${ES_REQUIRED_DISK_GB:-1}
ALLOW_LOW_DISK=${ALLOW_LOW_DISK:-0}
CHECK_KIBANA_PORT=${CHECK_KIBANA_PORT:-0}
ES_IMAGE="docker.elastic.co/elasticsearch/elasticsearch:${ES_VERSION}"

fail() {
    printf '预检失败：%s\n' "$1" >&2
    exit 1
}

command -v docker >/dev/null 2>&1 || fail "找不到 docker 命令"
docker info >/dev/null 2>&1 || fail "Docker daemon 不可用"
docker compose version >/dev/null 2>&1 || fail "docker compose 不可用"

case "$ES_REQUIRED_DISK_GB" in
    ''|*[!0-9]*) fail "ES_REQUIRED_DISK_GB 必须是非负整数" ;;
esac

check_port() {
    port=$1
    owner=$2
    label=$3
    if [ "$(docker inspect -f '{{.State.Running}}' "$owner" 2>/dev/null || true)" = "true" ]; then
        printf '%s\n' "端口 ${port}：由课程容器 ${owner} 使用"
        return
    fi
    if command -v lsof >/dev/null 2>&1 && lsof -nP -iTCP:"${port}" -sTCP:LISTEN 2>/dev/null | sed -n '2p' | grep -q .; then
        fail "127.0.0.1:${port} 已被其他进程占用（${label}）"
    fi
    printf '%s\n' "端口 ${port}：可用"
}

check_space() {
    label=$1
    available_kb=$2
    required_kb=$((ES_REQUIRED_DISK_GB * 1024 * 1024))
    available_gb=$((available_kb / 1024 / 1024))
    if [ "$available_kb" -lt "$required_kb" ]; then
        if [ "$ALLOW_LOW_DISK" = "1" ]; then
            printf '%s\n' "警告：${label} 可用约 ${available_gb}GB，低于要求 ${ES_REQUIRED_DISK_GB}GB；ALLOW_LOW_DISK=1 已显式放行。"
        else
            fail "${label} 可用约 ${available_gb}GB，低于要求 ${ES_REQUIRED_DISK_GB}GB；释放空间或显式设置 ALLOW_LOW_DISK=1"
        fi
    else
        printf '%s\n' "${label}可用空间：约 ${available_gb}GB（要求至少 ${ES_REQUIRED_DISK_GB}GB）"
    fi
}

check_port "$ES_PORT" es-study-single Elasticsearch
if [ "$CHECK_KIBANA_PORT" = "1" ]; then
    check_port "$KIBANA_PORT" es-study-kibana Kibana
fi

host_available_kb=$(df -Pk / | awk 'NR == 2 {print $4}')
check_space "宿主机 " "$host_available_kb"

if docker image inspect "$ES_IMAGE" >/dev/null 2>&1; then
    docker_available_kb=$(docker run --rm --entrypoint /bin/sh "$ES_IMAGE" -c "df -Pk / | awk 'NR == 2 {print \$4}'")
    check_space "Docker 虚拟盘 " "$docker_available_kb"
else
    printf '%s\n' "镜像尚未下载，跳过 Docker 虚拟盘检查：${ES_IMAGE}"
fi

printf '%s\n' "预检通过：Elasticsearch ${ES_VERSION}，Basic License，本地端口 ${ES_PORT}。"
