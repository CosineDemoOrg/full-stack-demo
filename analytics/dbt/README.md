DBT workflow for building a Tableau-ready dataset

Overview
- Creates analytics schema and models in Postgres using dbt-postgres.
- Models:
  - users: base user attributes sourced from public."user"
  - items: base item attributes sourced from public.item
  - tableau_user_dataset: aggregated user table with item_count for Tableau

Prerequisites
- Docker and docker compose
- Running Postgres service from this stack

Usage
1) Ensure the stack is up and the database is healthy:
   docker compose up -d db adminer backend

2) Create the analytics models:
   scripts/run-dbt.sh

   This will:
   - Ensure schema analytics exists
   - Run dbt (deps, run, test) using the dbt service
   - Build tables in the analytics schema:
     - analytics.users
     - analytics.items
     - analytics.tableau_user_dataset

Connecting from Tableau
- Connect to PostgreSQL using the same .env credentials.
- Database: ${POSTGRES_DB}
- Host: The host/IP of your Postgres instance (localhost if running locally, or the container host in production)
- Port: ${POSTGRES_PORT}
- Schema: analytics
- Table: tableau_user_dataset

Notes
- Profiles are templated to use environment variables from .env via the dbt service definition.
- If you prefer running dbt locally, install dbt-postgres and run:
  dbt deps && dbt run --profiles-dir .