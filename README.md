# HR Buddy - ChocolaTech RAG System 🏢🤖

**HR Buddy** es un asistente virtual avanzado de Recursos Humanos diseñado específicamente para **ChocolaTech**. El sistema implementa una arquitectura **RAG (Retrieval-Augmented Generation)** profesional con un enfoque riguroso en la seguridad y la privacidad de los datos.

## 🌟 Propósito del Proyecto

El objetivo principal de HR Buddy es centralizar y automatizar el acceso a la información corporativa para los empleados, permitiéndoles consultar desde sus saldos de vacaciones y modalidades de trabajo hasta políticas detalladas en el manual de la empresa, todo a través de una interfaz de chat inteligente y segura.

## 🚀 Características Principales

*   **Seguridad de Nivel Producción**: Implementa autenticación basada en **Cookies HttpOnly**, eliminando la exposición de tokens JWT en el frontend y protegiendo al sistema contra ataques XSS.
*   **Privacidad Total (Zero-Storage)**: La identidad del usuario se gestiona exclusivamente mediante sesiones seguras del lado del servidor.
*   **Motor RAG Semántico**: Utiliza **ChromaDB** y **LangChain** (`RecursiveCharacterTextSplitter`) para realizar búsquedas vectoriales sobre el manual de la empresa (`ManualChocolatech.txt`). La fragmentación inteligente con solapamiento (overlap) garantiza que no se pierda contexto entre pasajes.
*   **Inteligencia Artificial de Vanguardia**: Integración con **Google Gemini 2.5 Flash** para una comprensión profunda y generación de respuestas naturales.
*   **Experiencia de Usuario (UX) Profesional**: Sistema de notificaciones moderno y elegante para alertas de sistema y expiración de sesiones, reemplazando los cuadros de diálogo estándar.
*   **Cierre de Sesión Proactivo**: El sistema detecta automáticamente la expiración del token y redirige al login tras un aviso de 3 segundos, sin necesidad de interacción del usuario.

## 🔒 Arquitectura de Seguridad

Este proyecto ha sido refactorizado para cumplir con estándares profesionales de seguridad:
1.  **JWT en Cookies HttpOnly**: Los tokens de acceso son invisibles para JavaScript, lo que impide el robo de sesiones.
2.  **Cero Fugas de Datos**: Información como el nombre del usuario se recupera bajo demanda mediante endpoints seguros (`/api/me`) en lugar de almacenarse localmente.
3.  **Gestión de Sesión Activa**: Cierre de sesión automático tanto en el servidor (invalidación de token) como en el cliente (limpieza de interfaz con timers sincronizados).
4.  **Manejo de Variables de Entorno**: Configuración estricta mediante archivos `.env` con validación en tiempo de ejecución para evitar el arranque con configuraciones inseguras.

## 🛠️ Stack Tecnológico

*   **Backend**: [FastAPI](https://fastapi.tiangolo.com/) - Con validación mediante Pydantic Settings.
*   **Seguridad**: JWT (PyJWT/python-jose) con Cookies Seguras.
*   **IA & NLP**: [Google Gemini SDK](https://ai.google.dev/).
*   **Base de Datos Vectorial**: [ChromaDB](https://www.trychroma.com/).
*   **Orquestación de Datos**: [LangChain](https://www.langchain.com/) (Text Splitters).
*   **Base de Datos Relacional**: [SQLite](https://www.sqlite.org/).
*   **Frontend**: Vanilla JavaScript (ES6+), Tailwind CSS, FontAwesome.

## 📂 Estructura del Proyecto

```text
MyRAG/
├── src/
│   ├── main.py              # Lógica de API y endpoints de seguridad.
│   ├── database.py          # Conexiones SQLite y ChromaDB.
│   ├── config.py            # Configuración profesional con BaseSettings.
│   ├── services/
│   │   ├── etl_service.py   # Ingesta de documentos y datos.
│   │   ├── auth_service.py  # Lógica de hashing y JWT.
│   │   └── rag_service.py   # Motor RAG y Gemini.
│   └── static/              # Frontend (index.html, script.js, style.css).
├── .env                     # Variables sensibles (no incluir en Git).
├── SystemPrompt.md          # Prompt, comportamiento del Asistente.
└── ManualChocolatech.txt    # Documento base para el RAG.
```

## ⚙️ Instalación y Configuración Local

Sigue estos pasos para ejecutar el proyecto en tu computadora:

### 1. Requisitos Previos
*   Python 3.10+
*   **uv** (recomendado para gestión de paquetes) o **pip**.
*   Una **API KEY de Google Gemini** (consíguela en [Google AI Studio](https://aistudio.google.com/)).

### 2. Clonar el Repositorio
```bash
git clone https://github.com/tu-usuario/nombre-del-repo.git
cd nombre-del-repo
```

### 3. Configuración del Entorno (`.env`)
**IMPORTANTE:** Por seguridad, el archivo `.env` no se incluye en el repositorio. Debes crearlo en la raíz del proyecto con el siguiente formato:

```env
GEMINI_API_KEY=tu_api_key_aqui
SECRET_KEY=una_clave_secreta_para_jwt
ALGORITHM=HS256
ACCESS_TOKEN_MIN=tiempo_de_duración_del_token
```

### 4. Instalación de Dependencias
Si usas **uv** (recomendado):
```bash
uv sync
```
Si usas **pip**:
```bash
python -m venv .venv
source .venv/Scripts/activate  # En Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 5. Ejecución
```bash
uv run python -m src.main
```
La aplicación estará disponible en `http://localhost:8000`.

<img src="./assets/HR%20BUDDY.gif" width="800" alt="HR BUDDY" />

## 👥 Credenciales de Prueba
Para probar el sistema, puedes usar los datos de los empleados registrados en la base de datos (Formato de contraseña: `Chocola![Año][Nombre]`), al iniciar la app por primera vez se generarán pero de igual forma aquí te los dejo:

| Empleado | Usuario (Email) | Contraseña |
| :--- | :--- | :--- |
| **Juan Silva** | `juan.silva@empresa.com` | `Chocola!2022juan` |
| **María Gonzalez** | `maria.gonzalez@empresa.com` | `Chocola!2021maría` |
| **Carlos Olivera** | `carlos.olivera@empresa.com` | `Chocola!2023carlos` |
| **Ana Lima** | `ana.lima@empresa.com` | `Chocola!2020ana` |
| **Pedro Santos** | `pedro.santos@empresa.com` | `Chocola!2022pedro` |
| **Fernanda Costa** | `fernanda.costa@empresa.com` | `Chocola!2019fernanda` |
| **Rafael Mendez** | `rafael.mendez@empresa.com` | `Chocola!2023rafael` |
| **Juliana García** | `juliana.garcía@empresa.com` | `Chocola!2021juliana` |
| **Bruno Alvarez** | `bruno.alvarez@empresa.com` | `Chocola!2022bruno` |
| **Camila Herrera** | `camila.herrera@empresa.com` | `Chocola!2024camila` |
| **Eric Monné** | `eric.monne@chocolatech.com` | `Chocola!2024eric` |


---
*Desarrollado para ChocolaTech IT Security Division - 2026*
