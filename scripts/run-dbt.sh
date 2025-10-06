#!/usr/bin/env bash
set -euo pipefail

# Run dbt inside the docker-compose environment
# This will build the analytics models for Tableau consumption.

# Ensure the analytics schema exists
docker compose exec -T db psql -U "${POSTGRES_USER}" -d "${POSTGRES_DB}" -c "CREATE SCHEMA IF NOT EXISTS analytics;"

# Run dbt using the dedicated service (defined in docker-compose)
docker compose run --rm dbt bash -lc "dbt deps && dbt run --profiles-dir /usr/app && dbt test --profiles-dir /usr/app"