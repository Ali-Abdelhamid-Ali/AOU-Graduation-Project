# BioIntellect — AI-Powered Medical Platform

> **Graduation Project — Arab Open University**
> A full-stack, production-ready medical AI platform featuring 3D brain MRI segmentation, Retrieval-Augmented Generation (RAG) for medical Q&A, real-time patient dashboards, and multi-LLM support — all orchestrated with Docker.

---

## Table of Contents

1. [What Is BioIntellect?](#what-is-biointellect)
2. [High-Level Architecture](#high-level-architecture)
3. [Project Structure](#project-structure)
4. [Layer-by-Layer Breakdown](#layer-by-layer-breakdown)
   - [Reverse Proxy — Nginx](#1-reverse-proxy--nginx)
   - [Frontend — React + Vite](#2-frontend--react--vite)
   - [Backend — FastAPI](#3-backend--fastapi)
   - [MRI AI Service — Flask + TensorFlow](#4-mri-ai-service--flask--tensorflow)
   - [Cache — Redis](#5-cache--redis)
   - [Database — Supabase (PostgreSQL)](#6-database--supabase-postgresql)
   - [Vector Database — Qdrant](#7-vector-database--qdrant)
   - [LLM Providers](#8-llm-providers)
5. [How the Services Talk to Each Other](#how-the-services-talk-to-each-other)
6. [Request Flow Diagrams](#request-flow-diagrams)
7. [Tech Stack Summary](#tech-stack-summary)
8. [Environment Variables](#environment-variables)
9. [How to Run the Project](#how-to-run-the-project)
10. [Local Development (Without Docker)](#local-development-without-docker)
11. [Fine-Tuned AI Models](#fine-tuned-ai-models)
12. [Security Design](#security-design)
13. [Frequently Asked Questions](#frequently-asked-questions)

---

## What Is BioIntellect?

**BioIntellect** is a medical AI web platform built as a graduation project. It allows doctors and medical professionals to:

- Upload **brain MRI scans** in **NIfTI** format and get a 3D segmentation of tumor regions automatically.
- Ask medical questions and get answers powered by **Large Language Models (LLMs)** — either from the cloud (**OpenAI**, **Cohere**) or from locally fine-tuned models (**Phi-QA**, **MedMO-8B**).
- Use a **RAG (Retrieval-Augmented Generation)** system to search over medical documents and get context-aware answers.
- View patient data, history, and reports on a real-time dashboard.
- Generate clinical reports automatically.

The entire platform runs inside **Docker** containers and is served securely over **HTTPS**.

---

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                          User's Browser                         │
└───────────────────────────────┬─────────────────────────────────┘
                                │ HTTPS (port 443)
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Nginx  (Reverse Proxy)                       │
│         Routes /api/* → Backend   /  → Frontend                 │
└────────────────┬──────────────────────────┬─────────────────────┘
                 │                          │
                 ▼                          ▼
┌───────────────────────┐    ┌──────────────────────────────────┐
│  Frontend             │    │  Backend (FastAPI)  :8000        │
│  React + Vite         │    │                                  │
│  Three.js  VTK.js     │    │  ┌──────────┐  ┌─────────────┐   │
│  Framer Motion        │    │  │  Redis   │  │  Supabase   │   │
│  (Nginx-served SPA)   │    │  │  Cache   │  │  PostgreSQL │   │
└───────────────────────┘    │  └──────────┘  └─────────────┘   │
                             │                                  │
                             │  ┌──────────┐  ┌─────────────┐   │
                             │  │  Qdrant  │  │ LLM Factory │   │
                             │  │ VectorDB │  │ OpenAI /    │   │
                             │  └──────────┘  │ Cohere /    │   │
                             │                │ Phi-QA /    │   │
                             │                │ MedMO-8B    │   │
                             │                └─────────────┘   │
                             │                                  │
                             └──────────────┬───────────────────┘
                                            │ HTTP (internal)
                                            ▼
                             ┌──────────────────────────────────┐
                             │  MRI AI Service (Flask)    :7860   │
                             │  TensorFlow  Keras  Nibabel      │
                             │  3D Brain Tumor Segmentation     │
                             └──────────────────────────────────┘
```

---

## Project Structure

```
AOU-Graduation-Project/
└── BioIntellect/
    ├── .env                         ← Your local secrets (never commit this)
    ├── .env.example                 ← Template showing all required variables
    ├── docker-compose.yml           ← Defines and wires all services together
    ├── package.json                 ← Monorepo root (workspace config)
    │
    ├── nginx/
    │   └── nginx.conf               ← Reverse proxy rules, HTTPS, rate limiting
    │
    ├── certs/
    │   ├── server.crt               ← TLS certificate (self-signed for dev)
    │   └── server.key               ← TLS private key
    │
    ├── scripts/
    │   └── generate-certs.sh        ← Script to create self-signed TLS certs
    │
    ├── logs/                        ← Application log files
    │
    ├── backend/                     ← FastAPI Python API server
    │   ├── main.py                  ← App entry point (startup, config, server)
    │   ├── requirements.txt         ← All Python dependencies
    │   ├── Dockerfile               ← How to build the backend container
    │   └── src/
    │       ├── api/
    │       │   ├── routes/          ← 18 route modules (auth, clinical, nlp, rag…)
    │       │   └── controllers/     ← Business logic per feature
    │       ├── config/              ← Settings loaded from .env
    │       ├── db/                  ← Supabase database client
    │       ├── middleware/          ← Logging, CORS, rate-limit middleware
    │       ├── security/            ← JWT validation, auth handlers
    │       ├── services/            ← Domain logic (MRI, RAG, reports…)
    │       ├── stores/              ← LLM and Vector DB provider adapters
    │       ├── repositories/        ← Data access objects (DAOs)
    │       ├── validators/          ← Response schema validators (Pydantic)
    │       └── observability/       ← Structured logging, metrics
    │
    ├── frontend/                    ← React SPA
    │   ├── package.json             ← NPM dependencies
    │   ├── vite.config.js           ← Build config, dev-proxy to backend
    │   ├── nginx.conf               ← Serves built SPA inside container
    │   ├── Dockerfile               ← Multi-stage: build → serve with Nginx
    │   └── src/
    │       ├── main.jsx             ← React entry point
    │       ├── App.jsx              ← Root component + router
    │       ├── components/          ← Reusable UI components
    │       ├── pages/               ← Full page views (Dashboard, MRI, Chat…)
    │       ├── services/            ← Axios API client functions
    │       ├── store/               ← Global state management
    │       ├── hooks/               ← Custom React hooks
    │       ├── utils/               ← Helper functions
    │       └── assets/              ← Images, icons, static files
    │
    └── AI/
        └── brain 3D/
            ├── brain_seg_deploy/    ← MRI segmentation microservice
            │   ├── app.py           ← Flask app entry point
            │   ├── requirements.txt ← Python deps for this service
            │   ├── Dockerfile       ← Container image for AI service
            │   ├── models/          ← Keras model cached here after download
            │   └── outputs/         ← Temporary segmentation outputs (30 min TTL)
            │
            └── fintune/             ← Model training notebooks & artifacts
                ├── fine_tune_chat.ipynb         ← Chat model training
                ├── fine_tune_medical_QA.ipynb   ← QA model training
                ├── fintuned_QA_model/           ← Saved fine-tuned Phi QA model
                ├── fintuned_chating_model/      ← Saved fine-tuned chat model
                ├── medmo_8B/                    ← MedMO-8B model weights
                ├── data QA/                     ← Medical QA training data
                └── fine-tuning data/            ← Chat fine-tuning dataset
```

---

## Layer-by-Layer Breakdown

### 1. Reverse Proxy — Nginx

**What is it?**
**Nginx** is a high-performance web server used here as a **reverse proxy**. It sits in front of everything and decides where each incoming request goes.

**Why do we need it?**
- The user should access everything through one single address (`https://localhost`), not different ports for frontend and backend.
- It handles **HTTPS/TLS encryption** so the connection is secure.
- It protects the backend by adding **security headers** and enforcing **rate limits**.

**What does it do in this project?**

| Request Path | Goes To | Notes |
|---|---|---|
| `/` | **Frontend** (React SPA) | Serves the web app |
| `/api/*` | **Backend** (FastAPI) | General API calls (120s timeout) |
| `/api/v1/nlp/*` | **Backend** | LLM endpoints (300s timeout — AI takes time) |
| `/api/upload` | **Backend** | File uploads (500 MB limit) |
| `/api/v1/clinical/mri/segment` | **Backend → MRI AI** | MRI uploads (500 MB limit, 600s timeout) |
| `/health/ready` | **Backend** | Health check for monitoring |
| `/docs/` | **Backend** | Interactive API documentation |

**Security features enabled:**
- **HSTS** — Forces browser to always use HTTPS
- **X-Frame-Options: DENY** — Prevents embedding in iframes (clickjacking protection)
- **X-Content-Type-Options: nosniff** — Prevents MIME-type sniffing attacks
- **TLSv1.2 + TLSv1.3 only** — Blocks old insecure SSL versions
- **HTTP/2** — Faster multiplexed connections
- **HTTP → HTTPS redirect** — Port 80 always redirects to port 443

**Ports:** `80` (redirects) and `443` (HTTPS)

---

### 2. Frontend — React + Vite

**What is it?**
The **frontend** is the visual web interface that users interact with in their browser. It is a **Single Page Application (SPA)** — meaning the whole app loads once and navigates without full page reloads.

**Key Technologies:**

| Technology | What It Does |
|---|---|
| **React 18** | UI component framework |
| **Vite 6** | Lightning-fast build tool & dev server |
| **React Router 7** | Client-side navigation between pages |
| **Three.js + React Three Fiber** | 3D rendering in the browser (used for brain MRI visualization) |
| **VTK.js** | Medical imaging toolkit for volumetric rendering |
| **Framer Motion** | Smooth animations and transitions |
| **Anime.js** | Fine-grained JavaScript animations |
| **Axios** | HTTP client for calling the backend API |
| **Zod** | Runtime data validation (ensures API responses match expected shape) |
| **DOMPurify** | Sanitizes HTML to prevent XSS attacks |

**What pages/features does it have?**
- **Login / Register** — Supabase-powered authentication
- **Dashboard** — Real-time patient monitoring and stats
- **MRI Viewer** — Upload NIfTI MRI files, view 3D brain tumor segmentation
- **Medical Chat** — Ask medical questions, get LLM-powered answers
- **RAG Search** — Search over medical documents
- **Patient Records** — View and manage patient history
- **Clinical Reports** — Auto-generated reports

**How is it served?**
In production (Docker), Vite builds the app into static HTML/CSS/JS files (`/dist/`). An **Nginx** server inside the frontend container serves those files. Nginx is configured to redirect all routes back to `index.html` so React Router works correctly.

**Port:** `80` inside the container (accessed via the Nginx reverse proxy, not directly)

---

### 3. Backend — FastAPI

**What is it?**
The **backend** is the brain of the application. It is a **REST API** server that handles all the logic: authentication, database access, LLM calls, MRI processing, and more.

**Why FastAPI?**
**FastAPI** is a modern Python web framework that is:
- Very fast (runs on **Uvicorn**, an async server)
- Automatically generates interactive **API documentation** (Swagger UI / Scalar)
- Uses **Pydantic** for automatic data validation
- Natively supports **async/await** for handling many requests at once

**How is it started?**
The backend uses **Gunicorn** (a production-grade process manager) with **4 Uvicorn worker processes**. This means 4 copies of the app run in parallel to handle concurrent requests. Models are loaded once and shared across workers using `preload_app = True`.

**API Routes (18 modules):**

| Route Prefix | Purpose |
|---|---|
| `/v1/auth/` | Login, register, token validation (via Supabase) |
| `/v1/user/` | User profiles and settings |
| `/v1/clinical/` | Patient records, MRI segmentation trigger |
| `/v1/nlp/` | LLM text generation, chat |
| `/v1/rag/` | RAG document search and Q&A |
| `/v1/dashboard/` | Analytics data for the dashboard |
| `/v1/analytics/` | Statistics and reporting |
| `/health/` | Health and readiness probes |
| `/docs/` | Interactive API documentation (Scalar) |

**What happens at startup?**
1. Load all settings from the `.env` file
2. Validate security configuration (fail if insecure)
3. Verify Supabase connection and user profiles
4. Initialize the **LLM Provider Factory** (decides which AI model to use)
5. Initialize **Qdrant** vector database connection
6. Apply Swagger/OpenAPI customizations
7. Hand off to **Gunicorn** which spawns 4 workers

**Port:** `8000` (internal, accessed via Nginx)

**Resource limits (in Docker):**
- CPU: up to 4 cores
- Memory: up to 6 GB

---

### 4. MRI AI Service — fastAPI + TensorFlow

**What is it?**
A separate **microservice** dedicated to 3D brain MRI tumor segmentation. It is isolated from the main backend so that its heavy ML models don't affect API responsiveness.

**Why a separate service?**
Loading a large **Keras/TensorFlow** model takes significant memory (up to 8 GB). Keeping it separate means:
- The backend stays fast and light
- The MRI service can be restarted or scaled independently
- Resource limits can be applied separately

**What does it do step by step?**
1. Receives multimodal MRI files: **T1**, **T1CE**, **T2**, **FLAIR** (NIfTI `.nii.gz` format)
2. Loads the **Keras segmentation model** (downloaded once from HuggingFace on first run)
3. Pre-processes the volumetric image (normalize, resize, stack channels)
4. Runs 3D **U-Net** inference to produce a segmentation mask
5. Outputs class probabilities for 3 tumor regions:
   - **Necrotic / Non-Enhancing Tumor Core**
   - **Peritumoral Edema** (swelling around the tumor)
   - **Enhancing Tumor** (active tumor, visible with contrast agent)
6. Returns the result to the backend
7. Automatically deletes output files after **30 minutes**

**The AI Model:**
- **Source:** HuggingFace — `Ali-Abdelhamid-Ali/The_Best_3D_Brain_Tumor_Segmentation_BraTS_2021`
- **File:** `The Best 3D Brain MRI Segmentation.keras`
- **Training Dataset:** **BraTS 2021** — a standard benchmark dataset for brain tumor segmentation
- **Architecture:** 3D **U-Net** (convolutional encoder-decoder network)
- **Auto-download:** Downloaded on first run, cached in `/app/models/` to avoid re-downloading

**Key Technologies:**

| Technology | Purpose |
|---|---|
| **fastAPI 3.1** | Lightweight web framework for the AI endpoint |
| **TensorFlow 2.13 (CPU)** | Deep learning inference |
| **Keras** | High-level model loading and prediction |
| **Nibabel** | Reading/writing NIfTI brain scan files |
| **NumPy + SciPy** | Numerical operations and image processing |
| **HuggingFace Hub** | Downloading the pre-trained model |

**Port:** `7860` (internal only, backend calls it directly)

**Resource limits (in Docker):**
- CPU: up to 4 cores
- Memory: up to 8 GB

---

### 5. Cache — Redis

**What is it?**
**Redis** is an in-memory data store used for caching and rate limiting.

**Why do we need it?**
- LLM and database calls are slow and expensive. Caching means repeated identical requests are answered instantly from memory.
- **Rate limiting** prevents a single user from overwhelming the API with too many requests.

**Configuration:**
- **Image:** `redis:7-alpine` (lightweight Redis 7)
- **Max memory:** 256 MB with **LRU eviction** (removes least-recently-used data when full)
- **Password protected** via `REDIS_PASSWORD` environment variable
- **Persistence:** **AOF (Append-Only File)** — logs every write to disk so data survives restarts
- **Health check:** Redis CLI `ping` command

**Port:** `6379` (internal only, never exposed to the internet)

---

### 6. Database — Supabase (PostgreSQL)

**What is it?**
**Supabase** is a cloud service that provides a **PostgreSQL** database, built-in **authentication**, and a REST API. Think of it as "Firebase but with a real SQL database."

**Why Supabase?**
- Provides **JWT-based authentication** out of the box — no need to build login/register from scratch
- Full **PostgreSQL** power: joins, transactions, views, triggers
- Built-in **Row Level Security (RLS)** — database-level access control
- Free tier sufficient for a graduation project

**What is stored there?**
- User accounts and profiles
- Patient records and clinical data
- MRI scan metadata
- Clinical reports
- Application settings

**How does the backend connect?**
- Uses the **Supabase Python SDK** with two keys:
  - **Anon key** — public key for read operations (what logged-in users can see)
  - **Service role key** — admin key for write operations (used only by the backend, never exposed to the frontend)
- All communication is over **HTTPS** to the Supabase cloud

**Port:** Not exposed locally — it's a cloud service accessed over the internet.

---

### 7. Vector Database — Qdrant

**What is it?**
**Qdrant** is a specialized database for storing and searching **vector embeddings** — numerical representations of text meaning.

**Why do we need it?**
For the **RAG (Retrieval-Augmented Generation)** feature:
1. Medical documents are split into chunks and converted into **embedding vectors** (numbers that represent meaning)
2. These vectors are stored in Qdrant
3. When a user asks a question, the question is also converted to a vector
4. Qdrant finds the most **semantically similar** document chunks (nearest neighbor search)
5. Those chunks are sent to the LLM as context → the LLM gives a grounded, accurate answer

**Storage:** Local volume at `/app/storage/vector_db` inside the backend container.

---

### 8. LLM Providers

The backend uses a **Factory Pattern** to support multiple LLM providers. You configure which one to use via environment variables — no code changes needed.

**Available Generation Providers:**

| Provider | Config Value | Type | Notes |
|---|---|---|---|
| **OpenAI GPT** | `openai` | Cloud API | Requires `OPENAI_API_KEY` |
| **Cohere** | `cohere` | Cloud API | Requires `COHERE_API_KEY` |
| **Phi-QA** | `phi_qa` | Local model | Fine-tuned for medical Q&A |
| **MedMO-8B** | `medmo` | Local model | Fine-tuned for medical chat |

**Available Embedding Providers:**

| Provider | Config Value | Notes |
|---|---|---|
| **Cohere** | `cohere` | `embed-multilingual-v3.0`, 1024 dimensions |
| **OpenAI** | `openai` | Standard OpenAI embeddings |
| **Local** | `phi_qa` | Local embedding model |

**What are embeddings?**
Embeddings are numerical vectors (lists of numbers) that represent the meaning of text. Texts with similar meanings have vectors that are mathematically close to each other. This is what powers semantic search in RAG.

---

## How the Services Talk to Each Other

```
                    ┌─────────────┐
                    │   Browser   │
                    └──────┬──────┘
                           │ HTTPS :443
                    ┌──────▼──────┐
                    │    Nginx    │
                    └──┬──────┬───┘
           static /    │      │  /api/*
                  ┌────▼──┐ ┌─▼────────────────────────────┐
                  │ React │ │         FastAPI :8000        │
                  │  SPA  │ │                              │
                  └───────┘ │   ┌─────────┐ ┌───────────┐  │
                            │   │  Redis  │ │ Supabase  │  │
                            │   │ :6379   │ │ (cloud)   │  │
                            │   └─────────┘ └───────────┘  │
                            │                              │
                            │   ┌─────────┐ ┌───────────┐  │
                            │   │ Qdrant  │ │ OpenAI /  │  │
                            │   │(local)  │ │ Cohere /  │  │
                            │   └─────────┘ │ Phi-QA /  │  │
                            │               │ MedMO     │  │
                            │               └───────────┘  │
                            └──────────────┬───────────────┘
                                           │ HTTP :7860
                                    ┌──────▼──────┐
                                    │  fastAPI MRI│
                                    │  AI Service │
                                    └─────────────┘
```

**Communication protocols:**
- **Browser ↔ Nginx:** HTTPS (TLS 1.2/1.3)
- **Nginx ↔ Frontend container:** HTTP (internal Docker network)
- **Nginx ↔ Backend:** HTTP (internal Docker network)
- **Backend ↔ Redis:** Redis protocol (TCP, password-auth)
- **Backend ↔ Supabase:** HTTPS (external cloud)
- **Backend ↔ Qdrant:** HTTP REST API (internal)
- **Backend ↔ MRI AI Service:** HTTP REST API (internal Docker network)
- **Backend ↔ OpenAI/Cohere:** HTTPS (external cloud APIs)
- **MRI AI ↔ HuggingFace:** HTTPS (one-time model download)

---

## Request Flow Diagrams

### Flow 1 — User Login

```
Browser → POST /api/v1/auth/login
       → Nginx → Backend
       → Backend validates credentials with Supabase
       → Supabase returns JWT token
       → Backend returns token to browser
       → Browser stores token in localStorage
       → All future requests include "Authorization: Bearer <token>"
```

### Flow 2 — Medical Q&A (RAG)

```
Browser → POST /api/v1/rag/query  { "question": "What are symptoms of glioblastoma?" }
       → Nginx → Backend
       → Backend checks Redis cache (if cached, return immediately)
       → Backend converts question → embedding vector (via Cohere/OpenAI)
       → Backend queries Qdrant → finds top-5 similar document chunks
       → Backend builds prompt: "Context: [chunks]\n\nQuestion: [question]"
       → Backend calls LLM (OpenAI / local MedMO) with prompt
       → LLM returns grounded answer
       → Backend caches result in Redis
       → Returns answer to browser
```

### Flow 3 — Brain MRI Segmentation

```
Browser → POST /api/v1/clinical/mri/segment  (multipart: T1.nii.gz, T2.nii.gz, …)
       → Nginx (500MB limit, 600s timeout)
       → Backend receives files, validates format
       → Backend saves files temporarily
       → Backend → POST http://mri-ai:7860/segment (internal HTTP)
       → MRI AI Service:
           1. Loads Keras model (from cache or downloads first time)
           2. Reads NIfTI files with Nibabel
           3. Pre-processes: normalize → resize → stack channels
           4. Runs 3D U-Net inference → segmentation mask
           5. Returns mask + class probabilities as JSON
       → Backend stores result metadata in Supabase
       → Backend returns segmentation data to browser
       → Frontend renders 3D visualization with Three.js / VTK.js
       → MRI AI Service deletes temporary output files after 30 minutes
```

---

## Tech Stack Summary

| Layer | Technology | Version | Role |
|---|---|---|---|
| **Reverse Proxy** | **Nginx** | 1.27-alpine | HTTPS termination, routing, security headers |
| **Frontend Framework** | **React** | 18.3.1 | Component-based UI |
| **Build Tool** | **Vite** | 6.3.5 | Fast dev server and production bundler |
| **Routing** | **React Router** | 7.11.0 | Client-side navigation |
| **3D Visualization** | **Three.js** | 0.182.0 | WebGL-based 3D rendering |
| **3D React Bridge** | **React Three Fiber** | 8.18.0 | React bindings for Three.js |
| **Medical 3D** | **VTK.js** | 35.5.0 | Volumetric medical image rendering |
| **Animations** | **Framer Motion** | 11.0.3 | Declarative UI animations |
| **HTTP Client** | **Axios** | 1.13.2 | API calls from frontend |
| **Validation** | **Zod** | 4.3.2 | Runtime type checking |
| **XSS Protection** | **DOMPurify** | 3.3.1 | HTML sanitization |
| **Backend Framework** | **FastAPI** | 0.115.2 | REST API framework |
| **ASGI Server** | **Uvicorn** | 0.32.0 | Async Python HTTP server |
| **Process Manager** | **Gunicorn** | 23.0.0 | Multi-worker production server |
| **Deep Learning (GPU-free)** | **TensorFlow CPU** | 2.18.0 | ML inference (backend) |
| **Deep Learning (GPU-free)** | **PyTorch CPU** | 2.5.1 | Transformer model inference |
| **LLM Library** | **Transformers** | 4.46.3 | Load and run HuggingFace models |
| **LLM Orchestration** | **LangChain** | 0.3.7 | RAG pipeline and chains |
| **Cloud LLM** | **OpenAI API** | via SDK | GPT models for generation |
| **Cloud LLM / Embeddings** | **Cohere API** | via SDK | Embeddings + generation |
| **Local LLM (QA)** | **Phi-QA** | fine-tuned | Medical question answering |
| **Local LLM (Chat)** | **MedMO-8B** | fine-tuned | Medical conversation |
| **Primary Database** | **Supabase (PostgreSQL)** | cloud | User data, patient records |
| **Vector Database** | **Qdrant** | 1.12.1 | Semantic search for RAG |
| **Cache / Rate-limiting** | **Redis** | 7-alpine | Request caching, rate limits |
| **Medical Imaging** | **Nibabel** | 5.3.2 | NIfTI file reading/writing |
| **AI Microservice** | **fastAPI** | 3.1.0 | MRI segmentation endpoint |
| **MRI Deep Learning** | **TensorFlow CPU** | 2.13.1 | 3D U-Net inference |
| **Data Validation** | **Pydantic** | via FastAPI | Request/response schemas |
| **Containerization** | **Docker + Compose** | v3 | Service orchestration |

---

## Environment Variables

All secrets and configuration live in a single `.env` file inside the `BioIntellect/` folder. **Never commit this file to git** — it is in `.gitignore`.

Copy the template first:

```bash
cp BioIntellect/.env.example BioIntellect/.env
```

Then fill in the values:

```ini
# ── Ports (what the outside world sees) ────────────────────────────────────
PUBLIC_HTTP_PORT=80
PUBLIC_HTTPS_PORT=443

# ── Supabase (your cloud database & auth) ──────────────────────────────────
# Get these from: https://supabase.com → Project Settings → API
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

# ── Redis cache ─────────────────────────────────────────────────────────────
REDIS_PASSWORD=choose-a-strong-password-here
REDIS_SSL=false

# ── CORS & Security ─────────────────────────────────────────────────────────
# Comma-separated list of allowed origins
CORS_ORIGINS=http://localhost:5173,https://yourdomain.com
TRUSTED_HOSTS=localhost,127.0.0.1,yourdomain.com

# ── LLM Generation Provider ─────────────────────────────────────────────────
# Options: phi_qa | openai | cohere | medmo
GENERATION_BACKEND=phi_qa

# ── Cloud LLM API Keys (only needed if using cloud providers) ───────────────
OPENAI_API_KEY=sk-proj-...
COHERE_API_KEY=...

# ── Embedding Provider ───────────────────────────────────────────────────────
# Options: cohere | openai | phi_qa
EMBEDDING_BACKEND=cohere
EMBEDDING_MODEL_ID=embed-multilingual-v3.0
EMBEDDING_MODEL_SIZE=1024

# ── Vector Database (Qdrant) ─────────────────────────────────────────────────
VECTOR_DB_BACKEND=qdrant
VECTOR_DB_PATH=/app/storage/vector_db

# ── Local AI Model Paths (only needed for local LLMs) ───────────────────────
PHI_QA_MODEL_PATH=/app/models/phi-qa
MEDMO_MODEL_PATH=/app/models/MedMO-8B-Next

# ── MRI Segmentation Service ─────────────────────────────────────────────────
MRI_SEGMENTATION_SERVICE_URL=http://mri-ai:7860
MRI_SEGMENTATION_TIMEOUT_SECONDS=300
```

---

## How to Run the Project

### Prerequisites — Install These First

| Tool | Why You Need It | Download |
|---|---|---|
| **Docker Desktop** | Runs all services in containers | https://www.docker.com/products/docker-desktop |
| **Git** | To clone this repository | https://git-scm.com |
| A text editor | To edit the `.env` file | VS Code recommended |

**System Requirements:**
- **OS:** Windows 10/11, macOS, or Linux
- **RAM:** 16 GB minimum (the MRI AI model alone uses up to 8 GB)
- **Disk Space:** 20 GB free (Docker images + AI models)
- **CPU:** 4 cores minimum

---

### Step 1 — Clone the Repository

```bash
git clone https://github.com/your-username/AOU-Graduation-Project.git
cd AOU-Graduation-Project/BioIntellect
```

---

### Step 2 — Generate TLS Certificates

This creates the **self-signed HTTPS certificate** for local development. You only do this once.

```bash
bash scripts/generate-certs.sh
```

This creates `certs/server.crt` and `certs/server.key`.

> **Note:** Your browser will show a security warning ("Your connection is not private") because the certificate is self-signed, not issued by a trusted authority. This is normal for local development. Click "Advanced" → "Proceed to localhost (unsafe)" to continue.

---

### Step 3 — Configure Environment Variables

```bash
cp .env.example .env
```

Open `.env` in a text editor and fill in:
1. Your **Supabase URL and API keys** (create a free project at [supabase.com](https://supabase.com))
2. A strong **REDIS_PASSWORD** (any random string, e.g. `my-secret-redis-pass-123`)
3. Your **LLM provider** choice and API keys (or use local models)

---

### Step 4 — Start All Services

```bash
docker-compose up -d
```

**What `-d` means:** Runs in "detached" mode (background). Your terminal is freed up.

**What happens:**
- Docker downloads all required images (first time takes 10–30 minutes depending on internet speed)
- Services start in dependency order:
  1. **Redis** starts first
  2. **MRI AI service** starts (downloads Keras model from HuggingFace on first run — ~2 GB)
  3. **Backend** starts (waits for Redis to be healthy)
  4. **Frontend** starts (builds React app)
  5. **Nginx** starts last (waits for all others to be healthy)

**Watch the startup logs:**

```bash
docker-compose logs -f
```

Wait until you see all services showing as healthy before opening the browser.

---

### Step 5 — Open the Application

| URL | What You See |
|---|---|
| `https://localhost/` | The main web application |
| `https://localhost/docs/` | Interactive API documentation |
| `https://localhost/health/ready` | Health check (should return `{"status": "ok"}`) |

---

### Useful Commands

```bash
# See status of all running services
docker-compose ps

# See logs for a specific service (replace 'backend' with any service name)
docker-compose logs -f backend
docker-compose logs -f mri-ai
docker-compose logs -f frontend
docker-compose logs -f redis
docker-compose logs -f reverse-proxy

# Restart a single service (useful after code changes)
docker-compose restart backend

# Stop all services (keeps data volumes)
docker-compose down

# Stop all services AND delete all data (full reset)
docker-compose down -v

# Rebuild images after code changes
docker-compose build
docker-compose up -d
```

---

## Local Development (Without Docker)

If you want to run individual services during development (faster iteration, no need to rebuild Docker images):

### Backend

```bash
cd BioIntellect/backend

# Create a Python virtual environment
python -m venv venv

# Activate it
# On Windows:
venv\Scripts\activate
# On Mac/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy and configure .env (one level up, or set env vars directly)
# Make sure SUPABASE_URL, REDIS_PASSWORD, etc. are set

# Run the development server
python main.py
# API available at: http://localhost:8000
# Docs at: http://localhost:8000/docs
```

### Frontend

```bash
cd BioIntellect/frontend

# Install Node.js dependencies
npm install

# Start development server
npm run dev
# App available at: http://localhost:5173
# API calls are automatically proxied to http://localhost:8000 (configured in vite.config.js)
```

### MRI AI Service

```bash
cd "BioIntellect/AI/brain 3D/brain_seg_deploy"

# Create virtual environment
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Install dependencies
pip install -r requirements.txt

# Start the fastAPI service
python app.py
# Available at: http://localhost:7860
```

---

## Fine-Tuned AI Models

Two custom medical LLMs were fine-tuned specifically for this project:

### Phi-QA — Medical Question Answering

- **Base Model:** Microsoft **Phi** (small, efficient language model)
- **Fine-tuning Method:** Supervised fine-tuning on medical QA datasets
- **Training Notebook:** `AI/fintune/fine_tune_medical_QA.ipynb`
- **Saved Model:** `AI/fintune/fintuned_QA_model/`
- **Use Case:** Answering structured medical questions accurately

### MedMO-8B — Medical Conversation

- **Base Model:** 8 billion parameter model
- **Fine-tuning Method:** Supervised fine-tuning on medical dialogue data
- **Training Notebook:** `AI/fintune/fine_tune_chat.ipynb`
- **Saved Model:** `AI/fintune/medmo_8B/`
- **Use Case:** Natural medical conversation, follow-up questions, explanations

### Fine-Tuning Training Stack

The training environment (only needed if you want to retrain models) requires:
- **Unsloth** — Efficient fine-tuning (uses 60% less memory)
- **Accelerate** — Distributed training
- **PEFT** — Parameter-Efficient Fine-Tuning (**LoRA** adapters)
- **TRL** — Transformer Reinforcement Learning (SFT Trainer)
- **BitsAndBytes** — 4-bit quantization for low-memory training
- **Datasets** — HuggingFace dataset library

> **Note:** Training these models requires a **GPU**. Inference (using the models) works on **CPU only**, which is what the deployed application uses.

---

## Security Design

| Threat | Protection Mechanism |
|---|---|
| **Unencrypted traffic** | All traffic forced to **HTTPS** via Nginx redirect |
| **Man-in-the-middle attacks** | **TLS 1.2/1.3** only, strong cipher suites |
| **Clickjacking** | `X-Frame-Options: DENY` header |
| **Cross-Site Scripting (XSS)** | `DOMPurify` on frontend, `X-XSS-Protection` header |
| **MIME sniffing attacks** | `X-Content-Type-Options: nosniff` header |
| **Cross-Site Request Forgery** | **CORS** validation — only allowed origins accepted |
| **API abuse / DDoS** | **Rate limiting** via `SlowAPI` + Redis |
| **Unauthorized API access** | **JWT tokens** validated via Supabase on every request |
| **SQL injection** | **Supabase SDK** uses parameterized queries, never raw SQL from user input |
| **Secret exposure** | All secrets in `.env` (gitignored), never hardcoded |
| **Camera/mic/location abuse** | `Permissions-Policy` header disables all browser APIs |
| **Sensitive browser history** | `Referrer-Policy: strict-origin-when-cross-origin` |

---

## Frequently Asked Questions

**Q: Do I need a GPU to run this?**
No. The project uses CPU-only versions of **TensorFlow** and **PyTorch** on purpose. The trade-off is that MRI segmentation is slower (minutes instead of seconds), but it runs on any standard laptop or server.

**Q: Why does the MRI segmentation take so long?**
3D brain MRI segmentation involves processing a volumetric scan (hundreds of 2D slices stacked into a 3D volume) through a deep learning model. On CPU, this takes 2–10 minutes. On a GPU, it would take 10–30 seconds.

**Q: What is NIfTI format?**
**NIfTI** (`.nii` or `.nii.gz`) is the standard file format for medical brain scan data. MRI machines can export in this format. It stores 3D volumetric image data along with spatial metadata (voxel size, orientation).

**Q: What is RAG?**
**Retrieval-Augmented Generation** is a technique where instead of relying solely on the LLM's training knowledge, you first retrieve relevant documents from a database, then give those documents to the LLM as context. This makes answers more accurate and grounded in actual medical literature.

**Q: Can I use this without Supabase?**
Not easily — Supabase handles authentication and the primary database. You would need to replace it with a local PostgreSQL instance and implement your own JWT auth system.

**Q: What is Docker Compose?**
**Docker Compose** is a tool that lets you define multiple services (backend, frontend, database, etc.) in a single `docker-compose.yml` file and start/stop them all with one command. Each service runs in an isolated **container** — a lightweight virtual environment.

**Q: Why are there 4 backend workers?**
**Gunicorn** starts 4 parallel **Uvicorn** worker processes. This means the server can handle 4 requests simultaneously without one slow request blocking others. The number 4 matches the CPU core limit assigned to the backend container.

---

## Authors

Built by the **BioIntellect Team** — Arab Open University Graduation Project, 2025/2026.

---

*This README was written to be accessible to readers with no prior technology background. Technical terms are bolded and explained in context.*
