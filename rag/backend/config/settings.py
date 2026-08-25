import os
from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional
from dotenv import load_dotenv

# Get the absolute path to the backend directory
BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
env_path = os.path.join(BACKEND_DIR, ".env")

# Explicitly load dotenv
load_dotenv(env_path)

class Settings(BaseSettings):
    # App Settings
    PROJECT_NAME: str = "Police Case Intelligence Assistant"
    VERSION: str = "1.0.0"
    
    # MongoDB Settings
    MONGODB_URL: str = Field(default="mongodb://localhost:27017")
    DATABASE_NAME: str = Field(default="pcia_db")
    
    # ChromaDB Settings
    CHROMA_PERSIST_DIR: str = Field(default=os.path.join(BACKEND_DIR, "chroma_db"))
    
    # LLM Settings
    GROQ_API_KEY: Optional[str] = os.environ.get("GROQ_API_KEY")
    LLM_MODEL: str = Field(default="llama3-70b-8192")
    
    # Embeddings Settings
    EMBEDDING_MODEL: str = Field(default="BAAI/bge-small-en-v1.5")

settings = Settings()
