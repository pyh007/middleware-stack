#!/usr/bin/env python3
"""Elasticsearch 学习实验共用的最小 REST 客户端。"""

from __future__ import annotations

import base64
import json
import os
import time
from typing import Any
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


ES_URL = os.getenv("ES_URL", "http://127.0.0.1:9200").rstrip("/")
ES_USER = os.getenv("ES_USER", "elastic")
ES_PASSWORD = os.getenv("ES_PASSWORD", "elastic-local-123")


class ElasticsearchError(RuntimeError):
    def __init__(self, status: int, payload: Any) -> None:
        super().__init__(f"Elasticsearch HTTP {status}: {payload}")
        self.status = status
        self.payload = payload


def request(
    method: str,
    path: str,
    body: Any | None = None,
    *,
    params: dict[str, Any] | None = None,
    expected: tuple[int, ...] = (200,),
    ndjson: bool = False,
    user: str | None = None,
    password: str | None = None,
    timeout: float = 30.0,
) -> Any:
    query = f"?{urlencode(params, doseq=True)}" if params else ""
    url = f"{ES_URL}/{path.lstrip('/')}{query}"
    data: bytes | None = None
    headers = {"Accept": "application/json"}
    if body is not None:
        if ndjson:
            data = body.encode("utf-8") if isinstance(body, str) else body
            headers["Content-Type"] = "application/x-ndjson"
        else:
            data = json.dumps(body, ensure_ascii=False).encode("utf-8")
            headers["Content-Type"] = "application/json"
    token = base64.b64encode(
        f"{user or ES_USER}:{password or ES_PASSWORD}".encode("utf-8")
    ).decode("ascii")
    headers["Authorization"] = f"Basic {token}"
    req = Request(url, data=data, headers=headers, method=method)
    try:
        with urlopen(req, timeout=timeout) as response:
            status = response.status
            raw = response.read()
    except HTTPError as exc:
        status = exc.code
        raw = exc.read()
    payload: Any
    if not raw:
        payload = {}
    else:
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            payload = raw.decode("utf-8", errors="replace")
    if status not in expected:
        raise ElasticsearchError(status, payload)
    return payload


def delete_index(name: str) -> None:
    request("DELETE", name, expected=(200, 404))


def recreate_index(name: str, definition: dict[str, Any]) -> None:
    delete_index(name)
    result = request("PUT", name, definition)
    assert result.get("acknowledged") is True, result


def bulk(actions: list[dict[str, Any]]) -> dict[str, Any]:
    payload = "\n".join(json.dumps(item, ensure_ascii=False) for item in actions) + "\n"
    result = request("POST", "_bulk", payload, ndjson=True)
    assert result.get("errors") is False, result
    return result


def wait_for(path: str, predicate: Any, timeout: float = 60.0) -> Any:
    deadline = time.monotonic() + timeout
    last: Any = None
    while time.monotonic() < deadline:
        last = request("GET", path)
        if predicate(last):
            return last
        time.sleep(1)
    raise AssertionError(f"等待 {path} 超时，最后状态：{last}")


def evidence(label: str, value: Any) -> None:
    rendered = json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True)
    print(f"\n[证据] {label}\n{rendered}")
