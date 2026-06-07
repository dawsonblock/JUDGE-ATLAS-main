#!/usr/bin/env python3
"""Validate runtime/tooling versions for local proof execution.

Checks:
- Python version (3.11.x or 3.12.x)
- Node major version (22)
- npm major version (>=10)
- Docker CLI availability
- Docker Compose availability
- Pinned service image tags in docker-compose.yml (Postgres, Redis, MinIO)
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path


def _run(cmd: list[str]) -> tuple[int, str]:
    try:
        proc = subprocess.run(
            cmd,
            check=False,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError:
        return 127, ""
    output = (proc.stdout or "").strip()
    if not output:
        output = (proc.stderr or "").strip()
    return proc.returncode, output


def _parse_version_triplet(text: str) -> tuple[int, int, int] | None:
    match = re.search(r"(\d+)\.(\d+)\.(\d+)", text)
    if not match:
        return None
    return int(match.group(1)), int(match.group(2)), int(match.group(3))


def _parse_major(text: str) -> int | None:
    match = re.search(r"(\d+)", text)
    if not match:
        return None
    return int(match.group(1))


def _emit(name: str, passed: bool, detail: str) -> None:
    status = "PASS" if passed else "FAIL"
    print(f"{name}: {status} ({detail})")


def _extract_service_images(compose_text: str) -> dict[str, str]:
    services: dict[str, str] = {}
    current_service: str | None = None
    in_services = False

    for raw_line in compose_text.splitlines():
        line = raw_line.rstrip("\n")
        if not line.strip() or line.lstrip().startswith("#"):
            continue

        indent = len(line) - len(line.lstrip(" "))
        stripped = line.strip()

        if stripped == "services:":
            in_services = True
            current_service = None
            continue
        if not in_services:
            continue

        if indent == 2 and stripped.endswith(":"):
            current_service = stripped[:-1].strip()
            continue

        if current_service and indent >= 4 and stripped.startswith("image:"):
            image_val = stripped.split(":", 1)[1].strip().strip("\"'")
            services[current_service] = image_val

    return services


def _is_pinned(image: str) -> bool:
    if ":" not in image:
        return False
    tag = image.rsplit(":", 1)[1].strip()
    if not tag:
        return False
    return tag.lower() not in {"latest"}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".", help="Repository root")
    args = parser.parse_args()

    repo_root = Path(args.root).resolve()
    failures = 0

    py_rc, py_out = _run(["python3", "--version"])
    py_ver = _parse_version_triplet(py_out)
    py_ok = py_rc == 0 and py_ver is not None and py_ver[0] == 3 and py_ver[1] in {11, 12}
    _emit("Python", py_ok, py_out or "not found")
    if not py_ok:
        failures += 1

    node_rc, node_out = _run(["node", "--version"])
    node_major = _parse_major(node_out)
    node_ok = node_rc == 0 and node_major == 22
    _emit("Node 22", node_ok, node_out or "not found")
    if not node_ok:
        failures += 1

    npm_rc, npm_out = _run(["npm", "--version"])
    npm_major = _parse_major(npm_out)
    npm_ok = npm_rc == 0 and npm_major is not None and npm_major >= 10
    _emit("npm", npm_ok, npm_out or "not found")
    if not npm_ok:
        failures += 1

    docker_rc, docker_out = _run(["docker", "version", "--format", "{{.Client.Version}}"])
    docker_ok = docker_rc == 0 and bool(docker_out)
    _emit("Docker", docker_ok, docker_out or "not available")
    if not docker_ok:
        failures += 1

    compose_rc, compose_out = _run(["docker", "compose", "version", "--short"])
    compose_ok = compose_rc == 0 and bool(compose_out)
    _emit("Docker Compose", compose_ok, compose_out or "not available")
    if not compose_ok:
        failures += 1

    compose_path = repo_root / "docker-compose.yml"
    if not compose_path.exists():
        _emit("Pinned service images", False, "docker-compose.yml missing")
        failures += 1
    else:
        compose_text = compose_path.read_text(encoding="utf-8")
        images = _extract_service_images(compose_text)
        required_services = ("db", "redis", "minio")
        missing = [svc for svc in required_services if svc not in images]
        unpinned = [svc for svc in required_services if svc in images and not _is_pinned(images[svc])]
        if missing or unpinned:
            detail_parts: list[str] = []
            if missing:
                detail_parts.append("missing=" + ",".join(missing))
            if unpinned:
                detail_parts.append("unpinned=" + ",".join(f"{svc}:{images[svc]}" for svc in unpinned))
            _emit("Pinned service images", False, "; ".join(detail_parts))
            failures += 1
        else:
            detail = ", ".join(f"{svc}:{images[svc]}" for svc in required_services)
            _emit("Pinned service images", True, detail)

    if failures:
        print(f"RUNTIME_CHECK: FAIL ({failures} check(s) failed)")
        return 1

    print("RUNTIME_CHECK: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
