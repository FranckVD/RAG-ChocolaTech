from pydantic_settings import BaseSettings
from pathlib import Path

class Settings(BaseSettings):
    GEMINI_API_KEY: str
    SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_MIN: int

  # Rutas de carpetas y archivos
    CHROMA_PATH: Path = Path("./chroma_db")
    FILE_PATH: str = "ManualChocolatech.txt"
    SQLITE_PATH: str = "empleados.db"
    COLLECTION_NAME: str = "chocolatech_docs"

    class Config:
        env_file = ".ENV"   # indica que se leerá desde .env

settings = Settings() #type: ignore

