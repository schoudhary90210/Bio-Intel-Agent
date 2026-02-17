# Bio-Intelligence Automation Engine 🧬

A serverless data pipeline that monitors PubMed for health markers, utilizing FastAPI.

## 🏗 Architecture
[PubMed API] -> [FastAPI Backend] -> [GPT-4 Summarization] -> [Redis Cache] -> [Slack Webhook]

## 🚀 Usage
1. `docker-compose up --build`
2. `curl -X POST "http://localhost:8000/trigger-pipeline?keyword=longevity"`
