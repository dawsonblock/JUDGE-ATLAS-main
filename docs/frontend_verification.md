# Frontend Verification Guide

## Node Version Requirement

The frontend requires **Node 22**. This is enforced at three levels:

| Location | Setting |
|---|---|
| `frontend/.nvmrc` | `22` |
| `frontend/package.json` engines | `>=22 <23` |
| `scripts/release_gate.py` | `nvm use 22` + `--expected-major 22` |
| `scripts/check_frontend_node_gate.py` | defaults `--expected-major 22` (accepts any 22.x) |

## Setup

```bash
# Install and activate Node 22 via nvm
nvm install 22
nvm use 22

# Verify
node --version   # must be v22.x.x

# Install dependencies
cd frontend
npm ci

# Run checks
npm run lint
npm run typecheck
npm run test:contracts
npm run build
```

## Automatic Version Switching

With `frontend/.nvmrc` present, `nvm` will automatically switch to Node 22 when you `cd frontend` if you have `nvm` shell hooks enabled.

## Common Failure Modes

### `BLOCKED_NODE_VERSION`
The release gate emits this signal when `nvm use 22` fails. Fix:
```bash
nvm install 22
nvm use 22
```

### `engine-strict` rejection
`frontend/.npmrc` sets `engine-strict=true`. If you run `npm install` or `npm ci`
under the wrong Node version, npm will reject with an engines violation. Fix:
switch to Node 22 first, then retry.

### `vitest: command not found`
Occurs when `npm ci` was not run. Run `npm ci` under Node 22 before running tests.

## CI Reference

The release gate (`scripts/release_gate.py`) runs all frontend steps under
`nvm use 22` and validates the version with `scripts/check_frontend_node_gate.py`.

A mismatch between the running Node version and Node 22 causes the
`frontend_node_gate` step to emit `BLOCKED_NODE_VERSION` and fail with exit 1.
The gate does not fall back to other Node versions.
