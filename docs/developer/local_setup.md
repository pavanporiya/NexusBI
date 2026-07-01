# NexusBI Local Developer Setup Guide

This guide describes how to configure and run the NexusBI platform in your local development environment.

---

## 🛠️ Prerequisites

Ensure you have the following toolchains installed:
1. **Docker & Docker Compose** (to run PostgreSQL and Redis)
2. **Astral uv** (high-speed python package manager)
3. **Node.js 20+ & npm** (for Next.js frontend app development)

---

## 🚀 Step-by-Step Setup

### 1. Clone & Initialize Environment
Clone the repository and copy the environment configuration:
```bash
cp .env.example .env
```

### 2. Spin Up Database & Cache Services
Use Docker Compose to launch PostgreSQL and Redis containers:
```bash
make dev
```
To run the containers in the background, use:
```bash
docker compose -f deployment/docker-compose.yml up -d
```

### 3. Install Python Dependencies
Install the backend dependencies using `uv`:
```bash
cd backend
uv venv
uv pip install -e .
```

### 4. Apply Database Migrations
Run the initial Alembic schema migrations:
```bash
make db-migrate
```

### 5. Install Frontend Dependencies
Navigate to the frontend folder and install the packages:
```bash
cd frontend
npm install
```

---

## 🧪 Testing and Linting

To run formatting, type checking, and unit tests:

```bash
# Run all code linters (Ruff, MyPy, ESLint)
make lint

# Run code formatters
make format

# Run test suites
make test
```
