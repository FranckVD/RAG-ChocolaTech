import sqlite3
import chromadb
from src.config import settings

def get_sqlite_conn() -> sqlite3.Connection:
    return sqlite3.connect(settings.SQLITE_PATH, check_same_thread=False)

# Cambiamos a una función de embedding por defecto de ChromaDB o una compatible con Gemini
# Para simplificar y no requerir más keys, usaremos la por defecto de Chroma (sentence-transformers)
chroma_client = chromadb.PersistentClient(path=settings.CHROMA_PATH)
collection = chroma_client.get_or_create_collection(
    name=settings.COLLECTION_NAME
)
