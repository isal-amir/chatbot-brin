import os
from dotenv import load_dotenv
from pydantic_settings import BaseSettings

load_dotenv()

class Settings(BaseSettings):
    PROJECT_NAME: str = "Hermeneutic AI Tutor"
    
    QDRANT_HOST: str = os.getenv("QDRANT_HOST", "localhost")
    QDRANT_PORT: int = int(os.getenv("QDRANT_PORT", "6333"))
    COLLECTION_NAME: str = "knowledge_base"
    
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    OPENROUTER_API_KEY: str = os.getenv("OPENROUTER_API_KEY", "")
    
    # DB
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", 
        "postgresql://chatbot_user:chatbot_password@127.0.0.1:5433/chatbot_db"
    )

settings = Settings()
