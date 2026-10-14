# Changelog

All notable changes to the **Semantic Diffing for Evolving Knowledge Graphs** project are documented here.

## [2.0.0] - 2026-10-13

### Architecture & Monorepo Transformation
- **Production Monorepo Restructuring**: Reorganized repository into a clean monorepo architecture with `/frontend` (React 18 + Vite + TypeScript + Tailwind CSS), `/backend` (Python FastAPI + SQLAlchemy 2.0 + Alembic), `/src/semantic_diff` (core ML/KG extraction & diff algorithms), `/data` (synthetic & real corpora), `/eval` (empirical benchmarking suite), and `/results`.
- **Dockerized Multi-Container Infrastructure**: Added `docker-compose.yml` orchestrating PostgreSQL 16, FastAPI backend, Nginx-served static React frontend, and an optional Neo4j graph database profile.
- **CI/CD Pipeline**: Added GitHub Actions workflow (`.github/workflows/ci.yml`) validating backend Ruff linting, Pytest test suite, benchmark script execution, and frontend Vitest & Vite builds.

### Backend & API
- **FastAPI Layered Architecture**: Structured backend into `routers/`, `services/`, `models/`, `schemas/`, and `core/` modules.
- **Authentication & Security**: Implemented JWT access and refresh token authentication, bcrypt password hashing, CORS whitelist protection, SlowAPI rate limiting, and request ID middleware.
- **Asynchronous Job Streaming**: Integrated background job processing with both Server-Sent Events (`/api/v1/jobs/{job_id}/events`) and polling endpoints (`/api/v1/jobs/{job_id}`) for long-running document ingestion and graph diffs.
- **Database Persistence**: Implemented SQLAlchemy 2.0 ORM models (`User`, `Project`, `Version`, `DiffResultModel`, `Job`) with Alembic migration versioning supporting PostgreSQL in production and SQLite for local development and testing.
- **Health & Readiness Endpoints**: Added standardized `/api/v1/health` and `/api/v1/ready` endpoints with database liveness checks.

### Core Algorithms & KG Diff Engine
- **LangGraph State Graph Workflow**: Implemented 6-node state machine (`extract` → `resolve` → `build` → `diff` → `summarize` → `verify`) with strict type validation.
- **Provenance-Grounded Chunking**: Implemented sentence-aware text chunker tracking exact character offsets (`start_offset`, `end_offset`) and SHA-256 chunk hashes across `.txt`, `.pdf`, and `.docx` documents.
- **Hybrid Entity Resolution**: Unified fuzzy string metrics, semantic embedding similarity, borderline LLM disambiguation, and provenance-cued rename detection (detecting phrases such as `rebranded as`, `formerly`, and `merged into`).
- **Temporal Knowledge Graph Engine**: Extended graph representations with discrete validity intervals (`valid_from`, `valid_to`, `is_active`) tracking ontological persistence across $N$ versions.
- **Configurable Domain Severity**: Added rule-based severity categorizer (CRITICAL, HIGH, MEDIUM, LOW) mapping high-impact corporate transitions (acquisitions, leadership changes, regulatory shifts).
- **Pluggable Graph Storage**: Built abstract `GraphStore` supporting in-memory `NetworkXGraphStore` and enterprise `Neo4jGraphStore` with automatic offline graceful degradation.

### Data & Evaluation Suite
- **Empirical Benchmarking (`eval/evaluate.py`)**: Built automated evaluation script measuring Precision, Recall, F1 for entities and relations, rename accuracy, and false add/remove pairs against gold labels.
- **Reproducible Metrics**: Evaluated against real ground-truth pairs in `eval/gold_labels/` marked *needs human review*:
  - Entity Diff F1: **89.91%** (vs 87.32% for naive diff)
  - Edge Diff F1: **100.00%**
  - False Add/Remove Pairs: **0** in hybrid resolution (down from **2** in naive diff)
  - Rename Accuracy: **100.00%** (up from **0.00%** in naive diff)
- **Data Segregation**: Preserved legacy ABC Corp/Acme datasets in `data/synthetic/` marked synthetic, and added real policy documentation in `data/real/`.

### Frontend Application
- **Modern React 18 SPA**: Replaced legacy single-page UI with a responsive dark-themed dashboard using React Router, TanStack Query, and Tailwind CSS.
- **Interactive Cytoscape Visualizer**: Added dynamic canvas highlighting added (green), removed (red), renamed (amber), and modified (blue) graph entities and relations.
- **Sliding Provenance Drawer**: Clickable evidence inspection displaying exact source text quotes and document character offsets.
- **Evolution Timeline & Diff Launcher**: Visual version timeline allowing pairwise diff selection and real-time SSE progress tracking.
- **Benchmark Dashboard**: Live empirical evaluation dashboard with ablation comparisons and on-demand benchmark execution.
