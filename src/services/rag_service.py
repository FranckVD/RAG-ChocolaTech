import logging
import os
import time
from google import genai
from google.genai import types
from src.database import collection, get_sqlite_conn
from src.config import settings

# Configuración de logging
logger = logging.getLogger(__name__)

client = genai.Client(api_key=settings.GEMINI_API_KEY)
MODEL_ID = "gemini-2.5-flash"

# Memoria de conversación simple (en memoria para este ejemplo)
# En producción, esto debería persistirse en una DB (ej. Redis o SQLite)
chat_histories = {}

def get_system_prompt():
    if os.path.exists("SystemPrompt.md"):
        with open("SystemPrompt.md", "r", encoding="utf-8") as f:
            return f.read()
    return "Eres el HR Buddy, asistente virtual de RR. HH. de ChocolaTech."

def buscar_empleado_por_nombre(nombre_completo: str) -> dict | None:
    conn = get_sqlite_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT id, nombre, email, departamento, puesto, fecha_ingreso, saldo_vacaciones, banco_horas, modalidad, password_hash FROM empleados WHERE nombre = ? COLLATE NOCASE", (nombre_completo,))
    empleado = cursor.fetchone()
    conn.close()
    if empleado:
        return {
            "id": empleado[0],
            "nombre": empleado[1],
            "email": empleado[2],
            "departamento": empleado[3],
            "puesto": empleado[4],
            "fecha_ingreso": empleado[5],
            "saldo_vacaciones": empleado[6],
            "banco_horas": empleado[7],
            "modalidad": empleado[8],
            "password_hash": empleado[9]
        }
    return None

def buscar_empleado_por_email(email: str) -> dict | None:
    conn = get_sqlite_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT id, nombre, email, departamento, puesto, fecha_ingreso, saldo_vacaciones, banco_horas, modalidad, password_hash FROM empleados WHERE email = ?", (email,))
    empleado = cursor.fetchone()
    conn.close()
    if empleado:
        return {
            "id": empleado[0],
            "nombre": empleado[1],
            "email": empleado[2],
            "departamento": empleado[3],
            "puesto": empleado[4],
            "fecha_ingreso": empleado[5],
            "saldo_vacaciones": empleado[6],
            "banco_horas": empleado[7],
            "modalidad": empleado[8],
            "password_hash": empleado[9]
        }
    return None

def ejecutar_consulta_rag(pregunta: str, email_usuario: str) -> str:
    info_empleado = buscar_empleado_por_email(email_usuario)
    
    if not info_empleado:
        return "ERROR DE SEGURIDAD: Usuario no autorizado."

    # Obtener historial de chat
    history = chat_histories.get(email_usuario, [])
    
    try:
        # Aumentamos n_results a 5 para mayor contexto del manual
        resultados = collection.query(query_texts=[pregunta], n_results=5)
        contexto_manual = "\n\n".join(resultados['documents'][0]) if resultados['documents'] and resultados['documents'][0] else "Sin contexto adicional."
    except Exception as e:
        logger.error(f"Error consultando ChromaDB: {e}")
        contexto_manual = "No se pudo acceder al manual en este momento."

    contexto_personal = f"""
    ESTÁS HABLANDO ÚNICAMENTE CON: **{info_empleado['nombre']}**.
    DATOS DEL USUARIO:
    - Nombre: **{info_empleado['nombre']}**
    - Email: **{info_empleado['email']}**
    - Puesto: **{info_empleado['puesto']}**
    - Departamento: **{info_empleado['departamento']}**
    - Fecha Ingreso: **{info_empleado['fecha_ingreso']}**
    - Vacaciones: **{info_empleado['saldo_vacaciones']} días**
    - Banco de Horas: **{info_empleado['banco_horas']} horas**
    - Modalidad: **{info_empleado['modalidad']}**
    """

    system_instruction = get_system_prompt()
    
    # Construir el prompt incluyendo el historial
    historial_str = ""
    if history:
        historial_str = "\n--- HISTORIAL DE CONVERSACIÓN ---\n"
        for msg in history[-6:]: # Últimos 6 mensajes
            role = "Usuario" if msg["role"] == "user" else "HR Buddy"
            historial_str += f"{role}: {msg['content']}\n"
        historial_str += "--- FIN DEL HISTORIAL ---\n"

    prompt_usuario = f"{contexto_personal}\nManual: {contexto_manual}\n{historial_str}\nPregunta actual: {pregunta}"

    config = types.GenerateContentConfig(
        system_instruction=system_instruction,
        temperature=0.2,
        max_output_tokens=1000
    )

    for intento in range(2):
        try:
            response = client.models.generate_content(
                model=MODEL_ID,
                config=config,
                contents=prompt_usuario
            )
            
            if response and response.text:
                respuesta_texto = response.text
                # Guardar en historial
                if email_usuario not in chat_histories:
                    chat_histories[email_usuario] = []
                chat_histories[email_usuario].append({"role": "user", "content": pregunta})
                chat_histories[email_usuario].append({"role": "assistant", "content": respuesta_texto})
                
                return respuesta_texto
            
            if response.candidates and response.candidates[0].finish_reason:
                return f"⚠️ Lo siento, no puedo responder eso por políticas de seguridad (Motivo: {response.candidates[0].finish_reason})."
            
            return "⚠️ Recibí una respuesta inesperada. Por favor, intenta de nuevo."

        except Exception as e:
            error_str = str(e)
            if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str:
                if intento < 1:
                    logger.warning("Límite de cuota alcanzado, reintentando en 5s...")
                    time.sleep(5)
                    continue
                return "⚠️ El servidor de IA está saturado. Por favor, espera un minuto y vuelve a intentarlo."
            logger.error(f"Error en Gemini: {error_str}")
            return f"❌ Error técnico: {error_str}"
    
    return "Lo siento, no pude procesar tu solicitud. Por favor, intenta más tarde."
