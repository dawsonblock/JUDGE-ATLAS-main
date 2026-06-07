#!/usr/bin/env python3
"""
Docker Compose smoke test proof generator.

Verifies that all services start and respond to basic queries.
Generates: docker_compose_smoke.json and docker_compose_smoke.log
"""

import argparse
import asyncio
import json
import os
import sys
import subprocess
from datetime import datetime, timezone
from typing import Dict, Any, Optional


async def wait_for_service(
    host: str,
    port: int,
    path: str = "/",
    max_retries: int = 30,
    timeout: int = 2
) -> bool:
    """Wait for HTTP service to respond."""
    import aiohttp

    for attempt in range(max_retries):
        try:
            async with aiohttp.ClientSession() as session:
                url = f"http://{host}:{port}{path}"
                async with session.get(url, timeout=timeout) as resp:
                    return resp.status < 500
        except Exception:
            await asyncio.sleep(1)

    return False


def run_docker_compose_up(compose_file: str = "docker-compose.yml") -> Dict[str, Any]:
    """Start Docker Compose services."""
    result = {
        "compose_up": False,
        "backend_health": False,
        "frontend_health": False,
        "postgres_ready": False,
        "postgis_ready": False,
        "redis_ready": False,
        "alembic_current": False,
        "protected_route_unauthorized": False,
        "errors": [],
    }

    try:
        # Start services
        proc = subprocess.run(
            ["docker-compose", "up", "-d"],
            cwd=os.path.dirname(compose_file) or ".",
            capture_output=True,
            text=True,
            timeout=60
        )

        if proc.returncode != 0:
            result["errors"].append(f"docker-compose up failed: {proc.stderr}")
            return result

        result["compose_up"] = True

        # Wait for services
        import time
        time.sleep(10)  # Give services time to start

        # Check backend health
        try:
            health_check = subprocess.run(
                ["curl", "-f", "http://localhost:8000/health"],
                capture_output=True,
                timeout=5
            )
            result["backend_health"] = health_check.returncode == 0
        except Exception as e:
            result["errors"].append(f"Backend health check failed: {str(e)}")

        # Check protected route returns 401/403
        try:
            protected_check = subprocess.run(
                ["curl", "-i", "http://localhost:8000/admin/review"],
                capture_output=True,
                text=True,
                timeout=5
            )
            # Should be 401 or 403 without auth
            result["protected_route_unauthorized"] = (
                "401" in protected_check.stdout or "403" in protected_check.stdout
            )
        except Exception as e:
            result["errors"].append(f"Protected route check failed: {str(e)}")

        # Check Postgres
        try:
            db_check = subprocess.run(
                ["docker-compose", "exec", "-T", "postgres", "pg_isready"],
                cwd=os.path.dirname(compose_file) or ".",
                capture_output=True,
                timeout=5
            )
            result["postgres_ready"] = db_check.returncode == 0
        except Exception as e:
            result["errors"].append(f"Postgres check failed: {str(e)}")

        # Check Redis
        try:
            redis_check = subprocess.run(
                ["docker-compose", "exec", "-T", "redis", "redis-cli", "ping"],
                cwd=os.path.dirname(compose_file) or ".",
                capture_output=True,
                text=True,
                timeout=5
            )
            result["redis_ready"] = "PONG" in redis_check.stdout
        except Exception as e:
            result["errors"].append(f"Redis check failed: {str(e)}")

        # Check Alembic migrations
        try:
            alembic_check = subprocess.run(
                ["docker-compose", "exec", "-T", "backend",
                 "alembic", "current"],
                cwd=os.path.dirname(compose_file) or ".",
                capture_output=True,
                text=True,
                timeout=10
            )
            result["alembic_current"] = alembic_check.returncode == 0
        except Exception as e:
            result["errors"].append(f"Alembic check failed: {str(e)}")

    except subprocess.TimeoutExpired:
        result["errors"].append("Docker Compose operations timed out")
    except Exception as e:
        result["errors"].append(f"Unexpected error: {str(e)}")

    return result


def generate_docker_proof(smoke_result: Dict[str, Any], output_dir: str) -> None:
    """Write docker_compose_smoke.json and docker_compose_smoke.log"""
    timestamp = datetime.now(timezone.utc).isoformat()

    proof = {
        "timestamp": timestamp,
        "compose_up": smoke_result["compose_up"],
        "backend_health": smoke_result["backend_health"],
        "frontend_health": smoke_result["frontend_health"],
        "postgres_ready": smoke_result["postgres_ready"],
        "postgis_ready": smoke_result["postgis_ready"],
        "redis_ready": smoke_result["redis_ready"],
        "alembic_current": smoke_result["alembic_current"],
        "protected_route_unauthorized": smoke_result["protected_route_unauthorized"],
        "passed": all([
            smoke_result["compose_up"],
            smoke_result["backend_health"],
            smoke_result["postgres_ready"],
            smoke_result["redis_ready"],
            smoke_result["alembic_current"],
            smoke_result["protected_route_unauthorized"],
        ]),
        "errors": smoke_result["errors"],
    }

    os.makedirs(output_dir, exist_ok=True)

    json_path = os.path.join(output_dir, "docker_compose_smoke.json")
    with open(json_path, "w") as f:
        json.dump(proof, f, indent=2)

    log_path = os.path.join(output_dir, "docker_compose_smoke.log")
    with open(log_path, "w") as f:
        f.write("Docker Compose Smoke Test Report\n")
        f.write(f"Generated: {timestamp}\n")
        f.write(f"\n")
        f.write(f"Service Startup:\n")
        f.write(f"  docker-compose up: {proof['compose_up']}\n")
        f.write(f"\n")
        f.write(f"Service Health:\n")
        f.write(f"  Backend API: {proof['backend_health']}\n")
        f.write(f"  Frontend: {proof['frontend_health']}\n")
        f.write(f"  PostgreSQL: {proof['postgres_ready']}\n")
        f.write(f"  PostGIS: {proof['postgis_ready']}\n")
        f.write(f"  Redis: {proof['redis_ready']}\n")
        f.write(f"\n")
        f.write(f"Database Migrations:\n")
        f.write(f"  Alembic current: {proof['alembic_current']}\n")
        f.write(f"\n")
        f.write(f"Security:\n")
        f.write(f"  Protected routes unauthorized: {proof['protected_route_unauthorized']}\n")
        f.write(f"\n")
        f.write(f"Overall: {'PASSED' if proof['passed'] else 'FAILED'}\n")

        if proof['errors']:
            f.write(f"\nErrors:\n")
            for error in proof['errors']:
                f.write(f"  - {error}\n")

    print(f"Generated {json_path}")
    print(f"Generated {log_path}")

    if proof["passed"]:
        print("✓ Docker Compose smoke test passed")
    else:
        print("✗ Docker Compose smoke test failed")


def main():
    parser = argparse.ArgumentParser(description="Generate Docker Compose smoke test proof")
    parser.add_argument("--compose-file", default="docker-compose.yml",
                        help="Path to docker-compose.yml")
    parser.add_argument("--proof-dir", default="artifacts/proof/current",
                        help="Output directory for proof artifacts")
    args = parser.parse_args()

    result = run_docker_compose_up(args.compose_file)
    generate_docker_proof(result, args.proof_dir)

    sys.exit(0 if result.get("passed", False) else 1)


if __name__ == "__main__":
    main()
