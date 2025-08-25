# E-Commerce Microservices (Python)

A small, dockerized microservices stack that demonstrates an e-commerce flow end-to-end:

* **Auth** – JWT auth (FastAPI + Postgres)
* **Catalog** – products, categories, inventory (FastAPI + Postgres + MinIO S3)
* **Cart** – user cart in Redis (FastAPI + Redis)
* **Order** – creates orders, emits events (FastAPI + Postgres + Kafka)
* **Payment** – mock payment API that emits events (FastAPI + Kafka)
* **Shipping** – shipment lifecycle (FastAPI + Postgres + Kafka)
* **Notifications** – email via MailHog, reacts to events (FastAPI + Kafka + MailHog)
* **Gateway** – Traefik (routes `/auth`, `/catalog`, `/cart`, `/order`, `/payment`, `/shipping`, `/notifications`)

> ⚠️ For demo use only. Secrets and security are deliberately simplified.

---

## Contents

* [Quick start](#quick-start)
* [Environment](#environment)
* [Demo script](#demo-script)
* [Services & endpoints](#services--endpoints)
* [Events](#events)
* [Local development](#local-development)
* [Troubleshooting](#troubleshooting)

---

## Quick start

Bring everything up with Docker, run DB migrations, then execute the demo.

### 1) Start the stack

```bash
# from repo root
cp deploy/.env.example deploy/.env
docker compose -f deploy/docker-compose.yaml --env-file deploy/.env up -d --build
```

This starts: Postgres, Redis, Kafka+ZooKeeper, MinIO, MailHog, Traefik gateway and all services.

* Traefik dashboard: [http://localhost:8080](http://localhost:8080)
* MailHog UI: [http://localhost:8025](http://localhost:8025)

### 2) Run database migrations

Use the **cross-platform Python script**:

```bash
# requires a local Python (3.11+ recommended)
python scripts/seed.py
```

> The script auto-reads `deploy/.env`, rewrites DSN host to `localhost`, and runs `alembic upgrade head` for each service with migrations (auth, catalog, order, shipping).

Windows PowerShell alternative:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\seed.ps1
```

### 3) Run the end-to-end demo

You can run either the PowerShell or Python demo script.

**PowerShell (recommended on Windows):**

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\run_demo.ps1
```

**Python (any platform):**

```bash
python scripts/run_demo.py
```

The demo will:

1. Register/login **admin** and **customer**
2. Create **category** and **product**, restock inventory
3. Customer adds to **cart**, **checkout** (creates shipment draft)
4. **Payment** mock success (emits event)
5. **Shipping** moves to `READY_TO_SHIP` and dispatches
6. Prints the last few **emails** captured by **MailHog**

---

## Environment

Copy and tweak `deploy/.env.example`:

```dotenv
POSTGRES_DSN=postgresql+psycopg://postgres:postgres@postgres:5432/appdb
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=appdb

REDIS_URL=redis://redis:6379/0

KAFKA_BOOTSTRAP=kafka:9092
KAFKA_BROKERS=kafka:9092

S3_ENDPOINT=http://minio:9000
S3_BUCKET=media
S3_ACCESS_KEY=admin
S3_SECRET_KEY=adminadmin

JWT_SECRET=devsecret
JWT_ALGORITHM=HS256

# internal call protection between services
SVC_INTERNAL_KEY=devkey
```

Notes:

* Each service also has sensible defaults for `*_BASE` (e.g., `http://catalog:8000`) so you typically don’t need to set them for Docker networking.
* The demo script reads MailHog from `http://localhost:8025`.

---

## Demo script

The PowerShell demo (`scripts/run_demo.ps1`) mirrors the Python one and adds:

* **Non-throwing 4xx/5xx** HTTP handling so you see response JSON even on errors
* **Friendly 409** messages (e.g., “Email already registered”)
* **Resilient MailHog parsing** (handles `Subject` as list or string; `To` from root or headers)
* **Shipping poll → READY\_TO\_SHIP → dispatch** flow

Typical successful run ends with:

```
=== DEMO COMPLETE ===
```

---

## Services & endpoints

### Common

* Health: `GET /<service>/health`
* Info:   `GET /<service>/v1/_info` (if present)

### Catalog (via gateway `/catalog`)

* `POST /v1/categories/` – create category (Admin JWT)
* `POST /v1/products/` – create product (Admin JWT)
* `GET  /v1/products/{id}` – fetch product
* `POST /v1/inventory/restock` – restock (Admin JWT + `X-Internal-Key`)

### Cart (via gateway `/cart`)

* `POST /v1/cart/items` – add item to cart (Customer JWT)
  Body: `{ "product_id": int, "qty": int }`

### Order (via gateway `/order`)

* `POST /v1/orders/checkout` – create order and **reserve inventory**; **creates shipment draft** in Shipping
  Body (shipping address):

  ```json
  {
    "address_line1": "1 Demo Street",
    "address_line2": "",
    "city": "Dublin",
    "country": "IE",
    "postcode": "D01XYZ"
  }
  ```
* `GET /v1/orders/{order_id}` – fetch order with items

### Payment (via gateway `/payment`)

* `POST /v1/payments/mock-succeed` – simulate successful payment
  Body: `{ "order_id": int, "amount_cents": int, "currency": "USD" }`

### Shipping (via gateway `/shipping`)

* `GET  /v1/shipments?order_id={id}` – list shipments for an order
* `POST /v1/shipments/{id}/dispatch` – mark shipped; sets carrier/tracking in demo

**Statuses**:
`PENDING_PAYMENT → READY_TO_SHIP → DISPATCHED`

### Notifications (via gateway `/notifications`)

* Reacts to events and sends email to **MailHog**.
  MailHog UI: [http://localhost:8025](http://localhost:8025)

---

## Events

All events are on Kafka (bootstrap `kafka:9092` inside Docker).

* **Topic:** `order.events`

  * `order.created` – emitted by Order on checkout

* **Topic:** `payment.events`

  * `payment.succeeded` – emitted by Payment mock API
  * (optionally `payment.failed` in extended flows)

* **Topic:** `shipping.events`

  * `shipping.ready` – when a shipment moves to READY\_TO\_SHIP
  * `shipping.dispatched` – when dispatched

**Consumers**

* **Shipping** consumes `order.created` and `payment.succeeded`
* **Notifications** consumes `order.created`, `payment.succeeded`, `shipping.dispatched` and emails the user

---

## Local development

### Scripts

Cross-platform Python helpers (in `scripts/`):

* `gen-service-reqs.py` – generate per-service `requirements.txt` via pipreqs (optional, dev)
* `rebuild.py` – clean rebuild all images/containers using compose/bake
* `seed.py` – run Alembic migrations for services with DBs
* `setup.py` – local dev bootstrap (venv, pre-commit, etc.)

Windows-specific demo:

* `run_demo.ps1` – full end-to-end demo through the gateway
  (A Python equivalent `run_demo.py` is also available.)

### Virtual env (optional)

```bash
python -m venv .venv
# Linux/macOS
source .venv/bin/activate
# Windows PowerShell
# .\.venv\Scripts\Activate.ps1

pip install -r requirements-dev.txt
# Example: run a single service locally
cd services/auth && uvicorn app.main:app --reload
```

---

## Troubleshooting

**409 Conflict on create**
The scripts still proceed and print a friendly note like “already exists”.

**“Shipping create failed” / 500 on shipping**
Run migrations: `python scripts/seed.py` (ensures `shipments` table exists).

**Cart returns 404 on add**
Usually means Cart cannot reach Catalog. Check `CATALOG_BASE` for the Cart container and that Catalog is healthy.

**Kafka connection errors**
Ensure `zookeeper` and `kafka` are up, and services depend on `kafka` in compose.

**Port conflicts**
Free or change host ports in `deploy/docker-compose.yaml`:

* Traefik: `80`, `8080`
* MailHog: `8025`
* MinIO: `9000`, `9001`
* Kafka: `9092`
* Redis: `6379`
* Postgres: `5432`

**Reset everything**

```bash
docker compose -f deploy/docker-compose.yaml --env-file deploy/.env down -v
docker compose -f deploy/docker-compose.yaml --env-file deploy/.env up -d --build
python scripts/seed.py
```

---
