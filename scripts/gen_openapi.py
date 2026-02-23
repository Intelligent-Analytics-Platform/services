#!/usr/bin/env python3
"""Generate a combined OpenAPI JSON spec for all microservices.

Usage (from services/ directory):
    uv run python scripts/gen_openapi.py

Output: docs/openapi.json

Each service's component schemas are prefixed with the service name
(e.g. ResponseModel → MetaResponseModel) to avoid collisions.
Each path carries a path-level `servers` entry pointing to its actual host:port.
"""

from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

# ── Service registry ─────────────────────────────────────────────────────────

SERVICES = [
    {
        "name": "meta",
        "prefix": "Meta",
        "module": "meta.app",
        "attr": "app",
        "server": "http://localhost:8000",
        "description": "Meta 元数据服务",
    },
    {
        "name": "identity",
        "prefix": "Identity",
        "module": "identity.app",
        "attr": "app",
        "server": "http://localhost:8001",
        "description": "Identity 身份认证服务",
    },
    {
        "name": "vessel",
        "prefix": "Vessel",
        "module": "vessel.app",
        "attr": "app",
        "server": "http://localhost:8002",
        "description": "Vessel 船舶管理服务",
    },
    {
        "name": "data",
        "prefix": "Data",
        "module": "data.app",
        "attr": "app",
        "server": "http://localhost:8003",
        "description": "Data 遥测数据服务",
    },
]

# Paths shared by all services (health checks) — keep only one copy
_SKIP_PATHS = {"/"}


# ── Helpers ──────────────────────────────────────────────────────────────────


def _prefix_refs(obj: object, prefix: str) -> object:
    """Recursively rewrite all $ref values under #/components/schemas/."""
    if isinstance(obj, dict):
        return {
            k: (
                "#/components/schemas/" + prefix + v.removeprefix("#/components/schemas/")
                if k == "$ref" and isinstance(v, str) and v.startswith("#/components/schemas/")
                else _prefix_refs(v, prefix)
            )
            for k, v in obj.items()
        }
    if isinstance(obj, list):
        return [_prefix_refs(item, prefix) for item in obj]
    return obj


def _import_app(module_path: str, attr: str):
    import importlib

    return getattr(importlib.import_module(module_path), attr)


# ── Merge ────────────────────────────────────────────────────────────────────


def merge(service_specs: list[tuple[dict, dict]]) -> dict:
    combined: dict = {
        "openapi": "3.1.0",
        "info": {
            "title": "船舶能效分析平台 API",
            "description": (
                "整合 Meta / Identity / Vessel / Data 四个微服务的 OpenAPI 文档。\n\n"
                "每条路径通过 path-level `servers` 字段标明所属服务：\n\n"
                "| 服务 | 地址 |\n"
                "|------|------|\n"
                "| Meta 元数据 | http://localhost:8000 |\n"
                "| Identity 身份认证 | http://localhost:8001 |\n"
                "| Vessel 船舶管理 | http://localhost:8002 |\n"
                "| Data 遥测数据 | http://localhost:8003 |"
            ),
            "version": "0.1.0",
        },
        "paths": {},
        "components": {"schemas": {}},
    }

    # Health-check placeholder (one entry covering all services)
    combined["paths"]["/"] = {
        "get": {
            "summary": "健康检查",
            "description": "各服务均提供此端点，替换 servers[0].url 后访问对应服务。",
            "operationId": "health_check",
            "tags": ["健康检查"],
            "responses": {"200": {"description": "Successful Response"}},
        },
        "servers": [
            {"url": svc["server"], "description": svc["description"]} for _, svc in service_specs
        ],
    }

    for spec, svc in service_specs:
        prefix = svc["prefix"]

        # ── Prefix component schemas ──────────────────────────────────────
        for name, body in spec.get("components", {}).get("schemas", {}).items():
            combined["components"]["schemas"][prefix + name] = _prefix_refs(
                copy.deepcopy(body), prefix
            )

        # ── Add paths ─────────────────────────────────────────────────────
        for path, item in spec.get("paths", {}).items():
            if path in _SKIP_PATHS:
                continue
            path_item = _prefix_refs(copy.deepcopy(item), prefix)
            path_item["servers"] = [{"url": svc["server"], "description": svc["description"]}]
            combined["paths"][path] = path_item

    return combined


# ── Entry point ───────────────────────────────────────────────────────────────


def main() -> None:
    services_dir = Path(__file__).parent.parent

    # Make each service package importable
    for svc in SERVICES:
        app_dir = str(services_dir / "apps" / svc["name"])
        if app_dir not in sys.path:
            sys.path.insert(0, app_dir)

    service_specs: list[tuple[dict, dict]] = []
    for svc in SERVICES:
        print(f"  [{svc['name']}] generating spec ...", flush=True)
        app = _import_app(svc["module"], svc["attr"])
        spec = app.openapi()
        n_paths = len(spec.get("paths", {}))
        n_schemas = len(spec.get("components", {}).get("schemas", {}))
        print(f"  [{svc['name']}] {n_paths} paths, {n_schemas} schemas")
        service_specs.append((spec, svc))

    combined = merge(service_specs)

    out_path = services_dir / "docs" / "openapi.json"
    out_path.parent.mkdir(exist_ok=True)
    out_path.write_text(json.dumps(combined, ensure_ascii=False, indent=2), encoding="utf-8")

    total_paths = len(combined["paths"])
    total_schemas = len(combined["components"]["schemas"])
    print(f"\nWrote {out_path}")
    print(f"  {total_paths} paths, {total_schemas} schemas")


if __name__ == "__main__":
    main()
