import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    GITHUB_TOKEN: str = os.getenv("GITHUB_TOKEN", "")
    GITHUB_WEBHOOK_SECRET: str = os.getenv("GITHUB_WEBHOOK_SECRET", "")
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    DEFAULT_GROQ_MODEL: str = "llama-3.3-70b-versatile"
    GROQ_MODEL: str = os.getenv("GROQ_MODEL", DEFAULT_GROQ_MODEL)
    PASS_SCORE_THRESHOLD: int = int(os.getenv("PASS_SCORE_THRESHOLD", "7"))
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")


settings = Settings()