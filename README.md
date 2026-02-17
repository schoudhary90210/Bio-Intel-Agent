# Bio-Intelligence Automation Engine

![Python](https://img.shields.io/badge/Python-3.10-blue) ![FastAPI](https://img.shields.io/badge/FastAPI-0.109-green) ![Docker](https://img.shields.io/badge/Docker-Enabled-blue) ![Redis](https://img.shields.io/badge/Redis-Caching-red)

A high-throughput data pipeline designed to automate the ingestion, summarization, and distribution of medical research. This engine monitors PubMed for specific biological markers, processes abstracts using LLMs, and delivers actionable intelligence to communication channels like Slack.

## ⚡️ The Problem
Keeping up with the exponential growth of biomedical literature is impossible for human researchers. This tool bridges the gap between raw data and actionable insight by automating the "Search → Read → Summarize" loop.

## 🏗 System Architecture

The system follows a microservices-based event-driven architecture:

```mermaid
graph LR
    A[Trigger/Scheduler] -->|POST Request| B(FastAPI Gateway)
    B -->|Async Task| C{Redis Cache}
    C -->|Cache Miss| D[PubMed Entrez API]
    C -->|Cache Hit| E[Return Data]
    D -->|Raw Abstract| F[LLM Service]
    F -->|Structured Summary| G[Slack Webhook]