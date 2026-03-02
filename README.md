<div align="center">

# Bio-Intel Agent

**Automated biomedical literature monitoring pipeline.**

PubMed → LLM Summarization → Slack Alerts

<br/>

<img src="https://img.shields.io/badge/python-3.10+-3776AB?style=flat-square&logo=python&logoColor=white" />
<img src="https://img.shields.io/badge/FastAPI-0.109-009688?style=flat-square&logo=fastapi&logoColor=white" />
<img src="https://img.shields.io/badge/Redis-5.0-DC382D?style=flat-square&logo=redis&logoColor=white" />
<img src="https://img.shields.io/badge/Docker-Compose-2496ED?style=flat-square&logo=docker&logoColor=white" />
<img src="https://img.shields.io/badge/PubMed-Entrez_API-326599?style=flat-square" />

</div>

---

## What It Does

Biomedical research publishes over 3,000 papers per day. No human can keep up. Bio-Intel Agent automates the **Search → Read → Summarize → Alert** loop so researchers get actionable intelligence without reading every abstract.

Give it a keyword (e.g., "CRISPR", "mRNA vaccine", "intermittent fasting"). The pipeline queries PubMed for recent papers, summarizes each abstract into 3 bullet points using a local LLM or extractive algorithm, and delivers the results to Slack or console. Redis caching prevents redundant fetches. The entire system runs locally with zero paid API keys.

---

## Architecture

```
POST /trigger-pipeline?keyword=CRISPR
  → FastAPI (returns 200 immediately)
  → Background task:
      ┌─────────────┐    ┌──────────────┐    ┌───────────┐
      │ Redis Cache  │───▶│  PubMed API  │───▶│ Summarize │
      │  (1hr TTL)   │    │  (Biopython) │    │ (LLM/ext) │
      └─────────────┘    └──────────────┘    └─────┬─────┘
                                                    ▼
                                             ┌───────────────┐
                                             │ Slack / stdout │
                                             └───────────────┘
```

**Cache hit** → skip PubMed + LLM, serve cached results directly.

---

## Endpoints

| Method | Path | Description |
|:------:|:-----|:------------|
| `GET` | `/` | Root status check |
| `GET` | `/health` | Full system health (mode, LLM backend, Redis, Slack, uptime) |
| `POST` | `/trigger-pipeline?keyword=X` | Run full pipeline in background |
| `GET` | `/articles/search?keyword=X&limit=5` | Search PubMed directly (no summarization) |
| `POST` | `/pipeline/batch` | Run pipeline for multiple keywords |
| `GET` | `/pipeline/history` | Last 10 pipeline runs |
| `GET` | `/demo` | Run full pipeline with "CRISPR" in mock mode — always works |

Interactive API docs at `/docs` (Swagger UI).

---

## Setup

### Zero Config (demo mode)

```bash
git clone https://github.com/schoudhary90210/Bio-Intel-Agent.git
cd Bio-Intel-Agent
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Then test:
```bash
curl http://localhost:8000/demo | python3 -m json.tool
```

### With Docker

```bash
docker-compose up --build
```

This starts the API on port 8000 and Redis on port 6379.

### With Local LLM (Ollama)

```bash
# Install ollama: https://ollama.com
ollama pull llama3.2
pip install ollama

MOCK_MODE=false LLM_BACKEND=ollama uvicorn app.main:app --reload
```

### With Slack Alerts

Add your webhook URL to `.env`:
```
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/T.../B.../xxx
```

Without a webhook URL, results print to console.

---

## LLM Backends

| Backend | Config | Requirements | Description |
|:--------|:-------|:-------------|:------------|
| `auto` | `LLM_BACKEND=auto` | — | Tries ollama → extractive (default) |
| `ollama` | `LLM_BACKEND=ollama` | Local ollama install | Local LLM summarization via llama3.2 |
| `extractive` | `LLM_BACKEND=extractive` | None | Sentence scoring algorithm, zero dependencies |
| `mock` | `MOCK_MODE=true` | None | Static responses for testing |

The extractive backend scores sentences by biomedical term density, position weighting, and numeric data detection (p-values, percentages), then returns the top 3 as bullet points.

---

## Configuration

| Variable | Default | Description |
|:---------|:--------|:------------|
| `MOCK_MODE` | `true` | Bypass all real API calls |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis connection string |
| `PUBMED_EMAIL` | `csiddhant12@gmail.com` | Required by NCBI Entrez API |
| `LLM_BACKEND` | `auto` | LLM strategy: auto, ollama, extractive, mock |
| `SLACK_WEBHOOK_URL` | — | Slack incoming webhook (console fallback if empty) |
| `OPENAI_API_KEY` | — | Optional: OpenAI key for GPT-4 backend |

Set via `.env` file or environment variables. Copy `.env.example` to get started.

---

## Running Tests

```bash
pip install -r requirements.txt
pytest tests/ -v
```

Tests cover all services (PubMed, LLM, Slack, Redis) and all API endpoints. All tests run in mock mode with no external dependencies.

---

## Project Structure

```
Bio-Intel-Agent/
├── app/
│   ├── main.py              # FastAPI routes + pipeline orchestration
│   ├── config.py             # Pydantic Settings configuration
│   ├── services/
│   │   ├── pubmed.py         # PubMed/Entrez abstract fetching
│   │   ├── llm.py            # LLM summarization (ollama/extractive/mock)
│   │   └── slack.py          # Slack Block Kit delivery + console fallback
│   └── utils/
│       └── redis_client.py   # Redis cache wrapper with graceful degradation
├── tests/
│   ├── test_api.py           # FastAPI endpoint tests
│   ├── test_pubmed.py        # PubMed service tests
│   ├── test_llm.py           # LLM summarization tests
│   ├── test_slack.py         # Slack delivery tests
│   └── test_redis.py         # Redis caching tests
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── .env.example
└── README.md
```

---

## Troubleshooting

| Issue | Fix |
|:------|:----|
| `ModuleNotFoundError` | Run `pip install -r requirements.txt` |
| Redis connection refused | Start Redis: `docker run -p 6379:6379 redis:alpine` or skip — app works without it |
| Ollama not found | Install from [ollama.com](https://ollama.com), then `ollama pull llama3.2` |
| PubMed returns 0 results | Try a broader keyword or check NCBI status. Mock mode returns sample data. |
| Slack not sending | Check `SLACK_WEBHOOK_URL` in `.env`. Without it, output goes to console. |
| Port 8000 in use | `lsof -ti:8000 \| xargs kill -9` then restart |
