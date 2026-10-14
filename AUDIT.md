# Repository Audit & Gap Analysis: Semantic Diffing for Evolving Knowledge Graphs

**Date of Audit**: October 2026  
**Auditor**: Antigravity Autonomous Agent  
**Repository**: `Semantic-Diffing-for-Evolving-Knowledge-Graphs`  

---

## 1. Executive Summary

This audit assesses the pre-existing codebase, compares documentation claims against actual code, inventories dead and orphaned code, and establishes a screen-by-screen feature parity checklist against the original Streamlit UI design.

The pre-existing repository consisted of a minimal prototype script set (`app.py`, `semantic_diff.py`, `graph_utils.py`, `doc_v1.txt`, `doc_v2.txt`), an incomplete README, and an orphaned package structure in `src/semantic_diff/` and `eval/` where compiled `.pyc` files existed but without the complete web application infrastructure (no database, no user authentication, no multi-file parser, no jobs queue, and no working frontend).

---

## 2. Inventory of Existing Files

| File / Path | Size / Lines | Status | Description |
| :--- | :--- | :--- | :--- |
| `README.md` | 391 lines | Incomplete / Inconsistent | Outlines system architecture and concepts, but has mismatched instructions, syntax truncation at the end (`ualization`), and references Streamlit rather than Flask. |
| `app.py` | 69 lines | Prototype | Minimal Flask application exposing `/api/diff`. References non-existent `../frontend/index.html` and `../frontend/static`. Insecurely passes API key in the request payload. |
| `semantic_diff.py` | 106 lines | Prototype | Basic Groq call for entity/relation extraction using `llama-3.3-70b-versatile`, naive Python set difference for diffing, and basic LLM summary. |
| `graph_utils.py` | 145 lines | Prototype | NetworkX DiGraph builder, Matplotlib-to-Base64 PNG visualizer with spring layout, and node/edge JSON export helper. |
| `doc_v1.txt` | 515 bytes | Test Data | Baseline text describing "Acme Corporation" (SF headquarters, CEO John Smith, AWS & Google Cloud partnerships). |
| `doc_v2.txt` | 644 bytes | Test Data | Updated text describing "Acme Corporation" (NY headquarters, CEO Jane Doe, AWS exclusivity, AI Research Division, DataSync rebranding to AcmeSync). |
| `requirements.txt` | 6 lines | Minimal | Lists `flask>=3.0.0`, `flask-cors>=4.0.0`, `groq>=0.37.0`, `networkx>=3.2.0`, `matplotlib>=3.7.0`. Missing database, async, validation, frontend, and embedding libraries. |
| `results/eval.json` | 78 lines | Artifact | Benchmark measurements evaluating 3 pairs (`synthetic_v1_v2`, `synthetic_v2_v3`, `real_policy_v1_v2`) with status `"needs human review"`. |
| `results/eval_table.md`| 19 lines | Artifact | Markdown table detailing ablation of False Add/Remove pairs with vs. without entity resolution. |
| `src/semantic_diff/` | Directory | Bytecode only | Contained `.pyc` compiled artifacts for advanced modules (`models`, `config`, `extraction`, `resolution`, `diff_engine`, `temporal`, `workflow`, `storage/`) without modern production web scaffolding. |
| `eval/` | Directory | Bytecode only | Contained compiled benchmark scripts for entity/relation metric computation. |
| `tests/` | Directory | Bytecode only | Contained compiled test runners. |

---

## 3. Discrepancy & Gap Analysis (README vs Code)

| Documented Feature | Code Reality | Discrepancy Severity |
| :--- | :--- | :--- |
| **Streamlit UI** (`streamlit run app.py`) | `app.py` is a Flask web server, not a Streamlit application. Running `streamlit run app.py` fails to launch any interactive UI. | **High** |
| **Frontend Templates** | `app.py` references `template_folder='../frontend'` and `static_folder='../frontend/static'`, but neither directory existed in the repository. | **High** |
| **Company Entity Names** | The README references "ABC Corporation" in its architectural examples, while sample files (`doc_v1.txt`, `doc_v2.txt`) use "Acme Corporation". | **Low** |
| **API Key Management** | The README advises setting `export GROQ_API_KEY=...`, yet `app.py` required client-side submission of `api_key` in the POST body (`request.get_json().get('api_key')`). | **High (Security)** |
| **Document Formats** | The README states support for `.txt` documents only. No parsing existed for `.pdf` or `.docx`. | **Medium** |
| **Multi-version Comparison** | Section "Limitations" noted "Currently supports two-version comparison only", although temporal validity was planned. | **Medium** |
| **README Truncation** | Lines 389–391 of `README.md` cut off abruptly with `ualization`. | **Low** |

---

## 4. Dead, Redundant, & Orphaned Code

1. **`app.py` vs Production Backend**: The root `app.py` using Flask is superseded by the production FastAPI backend located at `/backend`.
2. **Missing Source vs Bytecode**: `.pyc` caches in `src/semantic_diff/` and `tests/` were orphaned without their corresponding `.py` files checked in. These modules need to be fully reconstituted, typed, tested, and integrated into `/backend/app/services/`.
3. **Unvalidated JSON Parsing in `semantic_diff.py`**: Extraction simply loaded raw strings with `json.loads` without Pydantic schemas, leading to fragile error handling if the LLM output deviated from expected triple formats.

---

## 5. UI Screen-by-Screen Parity & Migration Checklist

The original Streamlit/Flask concept had three conceptual screens/workflows. The new React 18 + Vite + TypeScript frontend will achieve 100% parity and expand beyond it:

| Feature / Screen | Original Streamlit/Flask Concept | New React + FastAPI Monorepo Equivalent | Status |
| :--- | :--- | :--- | :--- |
| **Document Input** | Dual textareas for v1 and v2 text pasting | Drag-and-drop file uploader supporting `.txt`, `.pdf`, `.docx`, plus version history list per project | **Expanded** |
| **Graph Visualization** | Static Matplotlib PNG rendered via base64 | Interactive Cytoscape.js canvas with drag/zoom/pan, physics layouts, side-by-side or overlay views | **Expanded** |
| **Color Coding** | Basic green (added) and red (removed) | Palette covering ADDED (emerald), REMOVED (rose), RENAMED (indigo), MODIFIED (amber), UNCHANGED (slate) | **Expanded** |
| **Diff Table** | None (only JSON dump) | Full tabular diff filterable by Severity (Critical, High, Medium, Low) and Type, with modal drawer showing verbatim source quote | **New** |
| **Change Summary** | Plain text LLM summary | Executive narrative with highlighted metrics, entity badges, and severity chips | **Expanded** |
| **Version History** | Only 2 versions at a time (v1 vs v2) | Temporal Knowledge Graph supporting $N$ versions with chronological timeline visualizer | **New** |
| **Export** | None | One-click export of Diff to structured JSON and CSV | **New** |
| **Evaluation View** | Not exposed in UI | Dedicated `/evaluation` page displaying precision/recall/F1, ablation tables, and benchmark runners | **New** |
| **User Authentication** | None (open / unsecured) | JWT Auth with httpOnly cookies / Bearer headers, refresh tokens, user isolation and ownership checks | **New** |
| **Long-Running Jobs** | Synchronous blocking HTTP request (hung on large docs) | Job pattern: POST returns job ID; live status polled or streamed via Server-Sent Events (SSE) | **New** |

---

## 6. Migration Plan & Priority Order

1. **Step 1: Core Algorithm Reconstitution & Enhancement**
   - Reconstruct all clean Python modules from `src/semantic_diff` with Pydantic v2 schemas.
   - Implement hybrid resolution (embeddings + fuzzy + LLM borderline verification).
   - Implement rich diff with domain severity scoring and temporal graph tracking.
   - Implement LangGraph workflow (`extract -> resolve -> build -> diff -> summarize -> verify`).
   - Implement GraphStore interface (NetworkX default + Neo4j adapter).
2. **Step 2: Backend Architecture (`/backend`)**
   - Build FastAPI layered architecture (`core/`, `models/`, `schemas/`, `services/`, `routers/`).
   - Implement SQLAlchemy 2.0 ORM models (`User`, `Project`, `Version`, `DiffResultModel`, `Job`).
   - Set up Alembic migrations and SQLite/PostgreSQL dynamic engine.
   - Implement JWT authentication with refresh, password hashing with bcrypt, slowapi rate limiting, request-ID middleware.
   - Implement asynchronous job runner with polling and SSE streams (`/api/jobs/{id}/stream`).
3. **Step 3: Frontend Architecture (`/frontend`)**
   - Initialize React 18 + Vite + TypeScript + Tailwind CSS application.
   - Build typed API client aligned with OpenAPI specifications.
   - Build UI components: Cytoscape graph visualizer, changes table, temporal timeline, source quote drawer, job progress tracker.
   - Build pages: Login, Register, Projects List, Project Detail, Diff Detail, Evaluation.
4. **Step 4: Data & Evaluation Pipeline (`data/` & `eval/`)**
   - Place synthetic documents in `data/synthetic/` and real documents in `data/real/`.
   - Implement `eval/evaluate.py` with precision, recall, F1, and ablation metrics.
   - Provide 3 gold labels marked "needs human review".
5. **Step 5: Testing, CI/CD, Containerization & Documentation**
   - Pytest test suite for backend; Vitest test suite for frontend; Playwright smoke test.
   - Dockerfile for backend, multi-stage Dockerfile + Nginx for frontend, `docker-compose.yml`.
   - Write `CHANGELOG.md`, `DEPLOY.md`, and update `README.md`.
