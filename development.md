# FastAPI Project - Local Development Workflow Guide

## 1. Overview

Use this guide to run the project locally, switch between Docker containers and local dev servers, configure domains and environment variables, and find the right URLs during development.

This guide helps you:

- Bring up the entire stack quickly with Docker.
- Swap individual services between containerized and local dev modes.
- Configure domains (including `localhost.tiangolo.com`) for realistic routing.
- Understand which environment variables and files control your local setup.
- Discover the URLs for each service in development.

## 2. Quick-Start

Follow these steps to get a full local stack running:

- Ensure you have Docker and Docker Compose installed.
- Create or update your `.env` file at the repo root (you can base it on any existing template provided by your team).
- From the repo root, start the stack:

  ```
  docker compose watch
  ```

- Once services are up, open:
  - Frontend: `http://localhost:5173`
  - Backend API: `http://localhost:8000`
  - API docs: `http://localhost:8000/docs`

- To stop the stack:

  ```
  docker compose down
  ```

## 3. Key Concepts / Responsibilities

### 3.1 Stack layout

- `docker-compose.yml`
  - Defines the core stack (backend, frontend, database, Traefik, Adminer, MailCatcher, etc.).
  - Used automatically by `docker compose`.
- `docker-compose.override.yml`
  - Development overrides on top of `docker-compose.yml`.
  - Commonly mounts local source code into containers and exposes ports on `localhost`.
- `.env`
  - Lives at the repo root.
  - Provides configuration and secrets used by Docker Compose and the application.
  - Changes here affect container configuration on the next stack restart.

### 3.2 Ports and service responsibilities

By default, each service is exposed on a dedicated `localhost` port:

- Frontend: `http://localhost:5173`
- Backend API: `http://localhost:8000`
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
- Adminer (DB admin): `http://localhost:8080`
- Traefik dashboard: `http://localhost:8090`
- MailCatcher: `http://localhost:1080`

These ports match the local dev servers for backend and frontend, which lets you swap between Docker and local servers without changing URLs.

### 3.3 Domains and Traefik routing

You can also run the stack using subdomains under `localhost.tiangolo.com` to mimic production-style routing.

- Main domain is controlled by `DOMAIN` in `.env`.
- When `DOMAIN=localhost.tiangolo.com`:
  - Backend serves at `http://api.localhost.tiangolo.com`.
  - Frontend serves at `http://dashboard.localhost.tiangolo.com`.
  - Adminer: `http://localhost.tiangolo.com:8080`.
  - Traefik: `http://localhost.tiangolo.com:8090`.
  - MailCatcher: `http://localhost.tiangolo.com:1080`.
- Traefik configuration for local development lives in `docker-compose.override.yml`.

### 3.4 Local vs containerized dev servers

For both backend and frontend you can:

- Run the service from Docker only.
- Stop the container and run a local dev server on the same port.

The routing and URLs stay the same because ports match between Docker and local processes.

## 4. Usage Examples

### 4.1 Start the full stack with Docker

From the repo root:

```
docker compose watch
```

This starts all services and watches for code changes (where configured). It also uses the `.env` file to populate environment variables in containers.

To follow logs for all services in another terminal:

```
docker compose logs -f
```

To see logs for a single service, for example the backend:

```
docker compose logs -f backend
```

### 4.2 Switch the frontend from container to local dev server

You might want faster hot-reload or local tooling for the frontend while keeping the rest of the stack in Docker.

- Stop the `frontend` container:

  ```
  docker compose stop frontend
  ```

- Start the local frontend dev server:

  ```
  cd frontend
  npm install
  npm run dev
  ```

- Access the frontend at:
  - `http://localhost:5173` (ports are the same as in Docker).

When done, stop the local dev server and restart the container if needed:

```
docker compose up -d frontend
```

### 4.3 Switch the backend from container to local dev server

Similarly, you can run the backend locally while leaving the rest of the stack in Docker.

- Stop the `backend` container:

  ```
  docker compose stop backend
  ```

- Start the local FastAPI dev server:

  ```
  cd backend
  uv run fastapi dev app/main.py
  ```

- Access the backend at:
  - `http://localhost:8000`
  - Docs: `http://localhost:8000/docs`

To switch back to the containerized backend, stop the local dev server and run:

```
docker compose up -d backend
```

### 4.4 Configure `localhost.tiangolo.com` routing

To test production-like subdomains locally:

- Edit `.env` at the repo root and set:

  ```
  DOMAIN=localhost.tiangolo.com
  ```

- Restart the stack so Traefik picks up the new domain:

  ```
  docker compose down
  docker compose watch
  ```

- Use these URLs:
  - Frontend: `http://dashboard.localhost.tiangolo.com`
  - Backend: `http://api.localhost.tiangolo.com`
  - Swagger UI: `http://api.localhost.tiangolo.com/docs`
  - ReDoc: `http://api.localhost.tiangolo.com/redoc`
  - Adminer: `http://localhost.tiangolo.com:8080`
  - Traefik: `http://localhost.tiangolo.com:8090`
  - MailCatcher: `http://localhost.tiangolo.com:1080`

`localhost.tiangolo.com` and all its subdomains resolve to `127.0.0.1`, so you do not need additional host file entries.

### 4.5 Update environment variables safely

When you change environment variables (either in `.env` or your shell), restart the stack so containers receive the new values.

- After editing `.env`:

  ```
  docker compose down
  docker compose watch
  ```

- If you only need to restart a single service (for example, the backend):

  ```
  docker compose restart backend
  ```

Keep in mind that secrets and credentials should be handled carefully and may be excluded from version control depending on your workflow.

### 4.6 Use pre-commit locally

The project includes a pre-commit configuration for linting and formatting.

- Install hooks into this repo (from the root):

  ```
  uv run pre-commit install
  ```

- Run checks on all files:

  ```
  uv run pre-commit run --all-files
  ```

Pre-commit will then run automatically before each commit and help keep code style consistent.

## 5. Dependencies & Interactions

- `docker-compose.yml`
  - Core service definitions and networking.
  - Reads configuration from `.env`.
- `docker-compose.override.yml`
  - Dev-time overrides (volumes, ports, Traefik for local routing).
  - Included automatically when you run `docker compose`.
- `.env`
  - Central place for configuration and secrets used by the stack.
  - Changing values requires a container restart to take effect.
- `backend/`
  - Contains the FastAPI application.
  - Expects supporting services (database, etc.) to be available via Docker networking.
- `frontend/`
  - Contains the frontend application.
  - Talks to the backend via the configured API URL (by default `http://localhost:8000` or `http://api.localhost.tiangolo.com`).

### Idiosyncrasies

- Ports are deliberately aligned between Docker containers and local dev servers so you can swap implementations without changing URLs in your browser or environment.
- Local Traefik is only for development and lives inside Docker; in production, Traefik (or another proxy) is typically managed outside this compose stack.
- Some scripts or tooling may rely on environment variables set before calling `docker compose`; check any project-specific scripts under `scripts/` if you see unexpected behavior.

## 6. Further Reading / Related Docs

- `./deployment.md` — how deployment works and how Traefik is configured outside local development.
- `./docker-compose.yml` — main Docker Compose configuration for all services.
- `./docker-compose.override.yml` — local development overrides, including Traefik and volume mounts.
- `./.env` — environment configuration used by Docker Compose and the applications.
- `./.pre-commit-config.yaml` — linting and formatting hooks run by `pre-commit`.