import logging
import os
from fastapi import FastAPI, Depends, HTTPException, status, Form, Request, Response
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from contextlib import asynccontextmanager

from src.services.rag_service import ejecutar_consulta_rag, buscar_empleado_por_email, buscar_empleado_por_nombre
from src.services.etl_service import initialize_database, load_manual_to_chroma
from src.services.auth_service import verify_password, create_access_token, decode_access_token
from src.config import settings

# Configuración de logging profesional
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("app.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("HRBuddy")

class ConsultaRequest(BaseModel):
    pregunta: str

class UserResponse(BaseModel):
    nombre: str
    email: str
    expires_at: int

class LoginResponse(BaseModel):
    message: str
    expires_in: int

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Inicialización de bases de datos
    logger.info("Iniciando aplicación HR Buddy...")
    initialize_database()
    if os.path.exists(settings.FILE_PATH):
        load_manual_to_chroma(settings.FILE_PATH)
    logger.info("Sistema listo para operar.")
    yield
    logger.info("Cerrando aplicación...")

app = FastAPI(title="HR Buddy - ChocolaTech", lifespan=lifespan)

# --- MIDDLEWARE PARA CACHÉ ---
# Evita que los navegadores guarden versiones viejas de los scripts/estilos
@app.middleware("http")
async def add_cache_control_header(request: Request, call_next):
    response = await call_next(request)
    if request.url.path.startswith("/static"):
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
    return response

# --- SEGURIDAD ---

async def get_current_user(request: Request):
    token = request.cookies.get("access_token")
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudo validar la sesión o el token ha expirado",
        headers={"WWW-Authenticate": "Cookie"},
    )
    
    if not token:
        raise credentials_exception
        
    payload = decode_access_token(token)
    if payload is None:
        raise credentials_exception
        
    email: None | str = payload.get("sub")
    if email is None:
        raise credentials_exception
        
    user = buscar_empleado_por_email(email)
    if user is None:
        raise credentials_exception
    return user, payload

# --- ENDPOINTS ---

@app.get("/api/me", response_model=UserResponse)
async def get_me(user_and_payload: tuple = Depends(get_current_user)):
    user, payload = user_and_payload
    expires_at = payload.get("exp")
    logger.info(f"Sesión verificada para {user['email']}. Expira en: {expires_at}")
    return {
        "nombre": user["nombre"],
        "email": user["email"],
        "expires_at": expires_at
    }

@app.post("/api/login", response_model=LoginResponse)
async def login(response: Response, form_data: OAuth2PasswordRequestForm = Depends()):
    user = buscar_empleado_por_nombre(form_data.username)
    if not user:
        user = buscar_empleado_por_email(form_data.username)
        
    if not user or not verify_password(form_data.password, user["password_hash"]):
        logger.warning(f"Intento de login fallido para: {form_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario o contraseña incorrectos",
        )
    
    access_token = create_access_token(data={"sub": user["email"]})
    
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        max_age=settings.ACCESS_TOKEN_MIN * 60,
        expires=settings.ACCESS_TOKEN_MIN * 60,
        samesite="lax",
        secure=False
    )
    
    logger.info(f"Usuario autenticado: {user['nombre']}")
    return {"message": "Login exitoso", "expires_in": settings.ACCESS_TOKEN_MIN}

@app.post("/api/logout")
async def logout(response: Response):
    response.delete_cookie("access_token")
    return {"message": "Sesión cerrada correctamente"}

@app.post("/api/consultar")
async def consultar(request: ConsultaRequest, user_and_payload: tuple = Depends(get_current_user)):
    user, _ = user_and_payload
    try:
        logger.info(f"Consulta recibida de {user['nombre']}: {request.pregunta[:50]}...")
        respuesta = ejecutar_consulta_rag(request.pregunta, user["email"])
        return {"respuesta": respuesta}
    except Exception as e:
        logger.error(f"Error procesando consulta RAG: {str(e)}")
        return {"respuesta": f"Lo siento, hubo un error procesando tu solicitud."}

# --- ESTÁTICOS ---

app.mount("/static", StaticFiles(directory="src/static"), name="static")

@app.get("/")
async def leer_raiz():
    return FileResponse("src/static/index.html")
