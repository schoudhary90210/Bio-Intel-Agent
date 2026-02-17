from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Bio-Intelligence Automation Engine"
    MOCK_MODE: bool = True 
    OPENAI_API_KEY: str = "sk-placeholder"
    SLACK_WEBHOOK_URL: str = "https://hooks.slack.com/services/placeholder"
    REDIS_URL: str = "redis://redis:6379/0"

settings = Settings()
