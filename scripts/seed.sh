#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

echo "--- Running migrations ---"
cd services/auth && alembic upgrade head && cd -
cd services/catalog && alembic upgrade head && cd -
cd services/order && alembic upgrade head && cd -
