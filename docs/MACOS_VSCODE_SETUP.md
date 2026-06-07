# macOS + VS Code Setup

This is the canonical local setup path for macOS developers using VS Code.

## 1. Install base tools

```bash
brew install pyenv nvm postgresql@16 redis
brew install --cask docker
```

Start Docker Desktop once after install and wait until it reports "Docker Engine running".

## 2. Node.js runtime (22.x)

```bash
nvm install 22
nvm use 22
node -v
npm -v
```

Expected:
- Node major: 22
- npm major: 10 or newer

## 3. Python runtime (3.11.x)

```bash
pyenv install 3.11.9
pyenv local 3.11.9
python3 --version
```

Expected:
- Python 3.11.x

## 4. Docker checks

```bash
docker version
docker compose version
docker info
```

## 5. Frontend bootstrap

```bash
cd frontend
npm ci
npm run typecheck
npm run test
npm run build
```

## 6. Backend bootstrap

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt || pip install -e ".[test]"
pytest
```

## 7. Full stack

```bash
docker compose up --build
```

## 8. Local doctor

Run the macOS doctor any time environment drift is suspected:

```bash
bash scripts/dev_doctor_macos.sh
```

The doctor prints pass/fail checks and exact repair commands for any failure.
