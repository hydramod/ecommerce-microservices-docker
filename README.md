# E-Commerce Microservices (Python Only)

See docs and deploy/docker-compose.yaml for local run.


## Quick demo

```bash
# 1. Start infra
docker compose -f deploy/docker-compose.yaml --env-file deploy/.env up -d --build

# 2. Run DB migrations
./scripts/seed.sh

# 3. Run end-to-end flow (admin creates product, customer buys, payment → order PAID)
./scripts/run_demo.sh
```


## Local venv setup (optional)

Instead of running everything in Docker, you can create a venv to run Alembic, tests, or services locally:

```bash
python3 -m venv .venv
source .venv/bin/activate   # Linux/macOS
# .venv\Scripts\Activate.ps1  # Windows PowerShell

pip install -r requirements-dev.txt

# now you can run alembic locally, e.g.
cd services/auth && alembic upgrade head
```


## Automation

Common tasks are available via the **Makefile** and helper scripts.

```bash
# one-time local setup (venv + deps)
make setup

# start the stack
cp deploy/.env.example deploy/.env
echo "SVC_INTERNAL_KEY=dev-internal-key" >> deploy/.env
make up

# migrate DBs
make seed

# run end-to-end demo
make demo

# stop everything
make down
```


### Windows (PowerShell)

If `make setup` fails with a bash error on Windows, use the PowerShell scripts instead:

```powershell
# 1) Setup local venv and install deps
powershell -ExecutionPolicy Bypass -File .\scripts\setup.ps1

# 2) Start the stack
Copy-Item deploy\.env.example deploy\.env
Add-Content deploy\.env "SVC_INTERNAL_KEY=dev-internal-key"
docker compose -f deploy/docker-compose.yaml --env-file deploy/.env up -d --build

# 3) Run DB migrations
powershell -ExecutionPolicy Bypass -File .\scripts\seed.ps1

# 4) Run the end-to-end demo
powershell -ExecutionPolicy Bypass -File .\scripts\run_demo.ps1
```
Or open **Git Bash** and run the original `make` targets there.
