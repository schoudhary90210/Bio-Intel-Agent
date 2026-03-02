from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "Bio-Intelligence Automation Engine"
    MOCK_MODE: bool = True
    OPENAI_API_KEY: str = "sk-placeholder"
    SLACK_WEBHOOK_URL: str = ""
    REDIS_URL: str = "redis://localhost:6379/0"
    PUBMED_EMAIL: str = "csiddhant12@gmail.com"
    LLM_BACKEND: str = "auto"  # auto, ollama, extractive, mock

    class Config:
        env_file = ".env"


settings = Settings()
