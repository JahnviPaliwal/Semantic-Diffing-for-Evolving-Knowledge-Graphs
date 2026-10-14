# Production Deployment Guide

This guide covers deployment strategies for **Semantic Diffing for Evolving Knowledge Graphs**, catering to containerized environments, cloud platforms, and serverless managed services.

---

## Architecture Overview

```
                        +----------------------------+
                        |  Reverse Proxy / Nginx     |
                        |  (Port 80 / 443)           |
                        +--------------+-------------+
                                       |
                   +-------------------+-------------------+
                   |                                       |
                   v                                       v
        +----------------------+               +-----------------------+
        | React 18 / Vite SPA  |               | FastAPI Backend       |
        | Static Assets / Nginx|               | (Port 8000)           |
        +----------------------+               +-----------+-----------+
                                                           |
                                      +--------------------+--------------------+
                                      |                                         |
                                      v                                         v
                         +--------------------------+              +--------------------------+
                         | PostgreSQL 16 Database   |              | Graph / Vector Store     |
                         | (SQLAlchemy 2.0/Alembic) |              | (NetworkX / Neo4j Store) |
                         +--------------------------+              +--------------------------+
```

---

## 1. Quick Start: Single-Host Docker Compose

The fastest way to deploy the complete stack (Postgres, Backend, Frontend, and optional Neo4j) is via `docker-compose.yml`.

### Step 1: Configure Environment
Copy `.env.example` to `.env` and configure credentials:
```bash
cp backend/.env.example .env
```
Key production variables to set:
```ini
POSTGRES_USER=prod_user
POSTGRES_PASSWORD=generate_a_secure_password_here
POSTGRES_DB=semantic_kg_diff
JWT_SECRET_KEY=generate_a_minimum_32_char_secret_key_here
GROQ_API_KEY=gsk_your_groq_production_key_here
CORS_ORIGINS=https://your-domain.com,https://api.your-domain.com
```

### Step 2: Launch Services
```bash
# Standard deployment (PostgreSQL + FastAPI Backend + React Nginx Frontend)
docker compose up -d --build

# Optional: Launch with Neo4j enterprise graph database profile
docker compose --profile with-neo4j up -d --build
```

### Step 3: Run Database Migrations
Migrations run automatically during startup, or can be triggered manually:
```bash
docker compose exec backend alembic upgrade head
```

Verify status:
```bash
curl http://localhost:8000/api/v1/health
curl http://localhost:8000/api/v1/ready
```

---

## 2. Split Cloud Deployment (PaaS / Serverless)

For high-scale setups, deploy the frontend and backend on dedicated cloud providers.

### A. Frontend (Vercel, Netlify, or Cloudflare Pages)
1. **Root Directory**: `frontend`
2. **Build Command**: `npm run build`
3. **Output Directory**: `dist`
4. **Environment Variables**:
   - `VITE_API_URL`: `https://api.your-domain.com/api/v1`
5. **SPA Rewrites**:
   - In `vercel.json`:
     ```json
     {
       "rewrites": [{ "source": "/(.*)", "destination": "/index.html" }]
     }
     ```
   - In `netlify.toml`:
     ```toml
     [[redirects]]
       from = "/*"
       to = "/index.html"
       status = 200
     ```

### B. Managed Database (Supabase, Neon, AWS RDS)
1. Provision a PostgreSQL 14+ instance.
2. Obtain the standard PostgreSQL URI:
   ```
   postgresql://user:password@ep-cool-db.us-east-2.aws.neon.tech/semantic_kg_diff?sslmode=require
   ```

### C. Backend (Render, Railway, Fly.io, or Hugging Face Spaces)
1. **Dockerfile Path**: `backend/Dockerfile` (or build from repository root).
2. **Build Context**: Root directory (`.`) to include core algorithm modules in `src/semantic_diff`.
3. **Port**: `8000`
4. **Environment Variables**:
   ```ini
   DATABASE_URL=postgresql://user:password@host/semantic_kg_diff?sslmode=require
   GROQ_API_KEY=gsk_your_key_here
   JWT_SECRET_KEY=production_random_secret_32_chars
   CORS_ORIGINS=https://your-frontend-app.vercel.app
   DISABLE_HEAVY_EMBEDDINGS=1
   ```

---

## 3. Cold Starts & Ephemeral Storage Strategy

### Fast Boot & Low-Memory Optimization (`DISABLE_HEAVY_EMBEDDINGS`)
- Heavy Transformer models (PyTorch, `all-MiniLM-L6-v2`) require ~500MB RAM and can introduce a 15–30 second cold-start latency on constrained PaaS tiers (Render 512MB, Railway hobby).
- Setting `DISABLE_HEAVY_EMBEDDINGS=1` activates the deterministic character 3-gram + Jaccard lexical cosine fallback in `EntityResolver`.
- This reduces cold boot time to **< 1.5 seconds** with **< 150MB RAM footprint**, while maintaining provenance-grounded rename precision.
- To enable full neural embeddings in production, allocate **>= 1.5 GB RAM** and set `DISABLE_HEAVY_EMBEDDINGS=0`.

### Ephemeral Storage Abstraction
- Cloud containers (Render, Heroku, HF Spaces) have ephemeral local file systems.
- Document uploads are managed via the abstract storage adapter in `backend/app/services/storage_adapter.py`.
- Configure `UPLOAD_DIR` (defaults to `/app/data/uploads` or `/tmp/uploads`).
- For persistent raw documents across restarts, mount a persistent volume at `/app/data` or configure an S3-compatible bucket via the storage adapter interface.

---

## 4. Environment Variables Reference

| Variable | Required | Default | Description |
| :--- | :---: | :--- | :--- |
| `DATABASE_URL` | Yes | `sqlite:///./data/local.db` | SQLAlchemy connection string (PostgreSQL or SQLite) |
| `GROQ_API_KEY` | Recommended | `""` | Groq API key for LLM graph extraction and summaries |
| `JWT_SECRET_KEY` | Yes (in prod) | *insecure default* | Minimum 32-character secret for signing JWT tokens |
| `JWT_ALGORITHM` | No | `HS256` | JWT signing algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | No | `60` | Lifespan of JWT access token |
| `REFRESH_TOKEN_EXPIRE_DAYS` | No | `7` | Lifespan of JWT refresh token |
| `CORS_ORIGINS` | Yes (in prod) | `*` | Comma-separated list of permitted origins |
| `DISABLE_HEAVY_EMBEDDINGS` | No | `0` | Set `1` for fast boot without loading PyTorch weights |
| `UPLOAD_DIR` | No | `./data/uploads` | Path for temporary document processing |
| `NEO4J_URI` | No | `bolt://neo4j:7687` | Optional Neo4j graph store URI |
| `NEO4J_USER` | No | `neo4j` | Neo4j username |
| `NEO4J_PASSWORD` | No | `password123` | Neo4j password |

---

## 5. Security & Production Checklist

- [ ] Changed `JWT_SECRET_KEY` to a cryptographically secure random token (`openssl rand -hex 32`).
- [ ] Set `POSTGRES_PASSWORD` and restricted database access to internal private network.
- [ ] Explicitly specified `CORS_ORIGINS` (never wildcard `*` with credentials in production).
- [ ] Enabled HTTPS via Let's Encrypt / Cloudflare SSL termination.
- [ ] Configured rate limiting (defaults to 60 req/min on public routes, 5 req/min on auth endpoints).
- [ ] Validated health checks (`/api/v1/health` and `/api/v1/ready`) on cloud load balancers.
