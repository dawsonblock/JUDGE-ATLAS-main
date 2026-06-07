# macOS + VS Code Setup

> See the full guide: [MACOS_VSCODE_ALPHA_SETUP.md](./MACOS_VSCODE_ALPHA_SETUP.md)

## Quick Reference

### Prerequisites

- Python 3.11.x (`pyenv` recommended — see `.python-version`)
- Node 22.x / npm 10.x (`nvm` recommended — see `.nvmrc`)
- Docker Desktop or Colima (for full-stack dev)
- VS Code with Python + ESLint extensions

### First-time setup

```bash
# 1. Copy environment template
cp .env.example .env
# Review all placeholder values before running

# 2. Bootstrap all dependencies
make setup

# 3. Verify local environment
python3 scripts/check_local_dev_environment.py
```

### Start the stack

```bash
make dev      # starts Docker Compose full stack
make stop     # tears down
```

### Run tests

```bash
make test              # all backend tests
make frontend-check    # lint + typecheck + build frontend
```

### Generate proof

```bash
make proof
```

For the full annotated setup guide including required environment variables,
config consistency checks, and VS Code workspace settings, see
[MACOS_VSCODE_ALPHA_SETUP.md](./MACOS_VSCODE_ALPHA_SETUP.md).
