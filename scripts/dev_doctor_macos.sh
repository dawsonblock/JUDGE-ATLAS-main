#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

failures=0

pass() {
  echo "[PASS] $1"
}

fail() {
  echo "[FAIL] $1"
  if [[ -n "${2:-}" ]]; then
    echo "       Repair: $2"
  fi
  failures=$((failures + 1))
}

check_command() {
  local name="$1"
  local cmd="$2"
  local repair="$3"
  if eval "$cmd" >/dev/null 2>&1; then
    pass "$name"
  else
    fail "$name" "$repair"
  fi
}

check_port_free() {
  local port="$1"
  if lsof -n -iTCP:"${port}" -sTCP:LISTEN >/dev/null 2>&1; then
    fail "Port ${port} is already in use" "lsof -n -iTCP:${port} -sTCP:LISTEN && stop conflicting process"
  else
    pass "Port ${port} is available"
  fi
}

cd "${ROOT_DIR}"

echo "== JUDGE_ATLASX macOS doctor =="

echo "-- Docker --"
check_command "docker CLI available" "command -v docker" "brew install --cask docker"
check_command "docker compose available" "docker compose version" "Start Docker Desktop and retry"
if docker info >/dev/null 2>&1; then
  pass "Docker Desktop engine is running"
else
  fail "Docker Desktop engine is not running" "Open Docker Desktop and wait for engine startup"
fi

echo "-- Node/npm --"
if command -v node >/dev/null 2>&1; then
  node_version="$(node -v 2>/dev/null || true)"
  node_major="$(echo "${node_version}" | sed -E 's/^v([0-9]+).*/\1/')"
  if [[ "${node_major}" == "22" ]]; then
    pass "Node 22 active (${node_version})"
  else
    fail "Node 22 active" "nvm install 22 && nvm use 22 (current: ${node_version:-unknown})"
  fi
else
  fail "node command available" "nvm install 22 && nvm use 22"
fi

if command -v npm >/dev/null 2>&1; then
  npm_version="$(npm -v 2>/dev/null || true)"
  npm_major="$(echo "${npm_version}" | sed -E 's/^([0-9]+).*/\1/')"
  if [[ -n "${npm_major}" && "${npm_major}" -ge 10 ]]; then
    pass "npm >=10 available (${npm_version})"
  else
    fail "npm >=10 available" "Upgrade npm with Node 22 toolchain (current: ${npm_version:-unknown})"
  fi
else
  fail "npm command available" "Install Node 22 via nvm"
fi

echo "-- Python --"
if command -v python3 >/dev/null 2>&1; then
  py_version="$(python3 --version 2>/dev/null || true)"
  pass "python3 available (${py_version})"
else
  fail "python3 available" "pyenv install 3.11.9 && pyenv local 3.11.9"
fi

echo "-- Project files --"
if [[ -f .env ]]; then
  pass ".env exists"
else
  fail ".env exists" "cp .env.example .env"
fi

if [[ -d backend/.venv ]]; then
  pass "backend virtual environment exists"
else
  fail "backend virtual environment exists" "cd backend && python3 -m venv .venv"
fi

if [[ -d frontend/node_modules ]]; then
  pass "frontend dependencies installed"
else
  fail "frontend dependencies installed" "cd frontend && npm ci"
fi

if [[ -x backend/.venv/bin/python ]]; then
  if backend/.venv/bin/python -c "import fastapi" >/dev/null 2>&1; then
    pass "backend dependencies installed"
  else
    fail "backend dependencies installed" "cd backend && source .venv/bin/activate && pip install -e '.[test]'"
  fi
else
  fail "backend python executable available" "cd backend && python3 -m venv .venv"
fi

echo "-- Port availability --"
check_port_free 3000
check_port_free 8000
check_port_free 5432
check_port_free 6379
check_port_free 9000
check_port_free 9001

echo ""
if [[ "${failures}" -eq 0 ]]; then
  echo "DEV_DOCTOR: PASS"
  exit 0
fi

echo "DEV_DOCTOR: FAIL (${failures} issue(s))"
exit 1
