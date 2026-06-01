import logging
import time
from langchain_text_splitters import RecursiveCharacterTextSplitter
from src.config import settings
from src.database import collection, get_sqlite_conn
from src.services.auth_service import get_password_hash

# Configuración de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def initialize_database():
    logger.info("Inicializando base de datos SQLite con seguridad mejorada...")
    conn = get_sqlite_conn()
    cursor = conn.cursor()
    
    # 1. Crear tabla con la estructura completa
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS empleados (  
            id INTEGER PRIMARY KEY AUTOINCREMENT,  
            nombre VARCHAR(100) NOT NULL,  
            email VARCHAR(150) NOT NULL UNIQUE,  
            departamento VARCHAR(100) NOT NULL,  
            puesto VARCHAR(100) NOT NULL,  
            fecha_ingreso DATE NOT NULL,  
            saldo_vacaciones INT NOT NULL DEFAULT 0,  
            banco_horas DECIMAL(5,1) NOT NULL DEFAULT 0,  
            modalidad VARCHAR(20) NOT NULL DEFAULT 'hibrido',
            password_hash VARCHAR(255) NOT NULL DEFAULT ''
        );
    ''')
    
    # 2. Insertar datos iniciales si la tabla está vacía
    cursor.execute("SELECT COUNT(*) FROM empleados")
    count = cursor.fetchone()[0]
    
    if count == 0:
        logger.info("Base de datos limpia detectada. Generando credenciales únicas...")
        
        # Lista de datos base
        empleados_data = [
            ('Juan Silva', 'juan.silva@empresa.com', 'Ingeniería', 'Ingeniero de Software', '2022-03-10', 20, 0.0, 'hibrido'),  
            ('María Gonzalez', 'maria.gonzalez@empresa.com', 'Recursos Humanos', 'Analista de RR. HH.', '2021-05-15', 5, 12.5, 'hibrido'),  
            ('Carlos Olivera', 'carlos.olivera@empresa.com', 'Finanzas', 'Analista Financiero', '2023-01-20', 0, 0.0, 'presencial'),  
            ('Ana Lima', 'ana.lima@empresa.com', 'Marketing', 'Especialista en Marketing', '2020-11-05', 15, -4.0, 'remoto'),  
            ('Pedro Santos', 'pedro.santos@empresa.com', 'Ventas', 'Ejecutivo de Ventas', '2022-08-01', 10, 8.0, 'hibrido'),  
            ('Fernanda Costa', 'fernanda.costa@empresa.com', 'Operaciones', 'Gerente de Operaciones', '2019-02-12', 30, 0.0, 'presencial'),  
            ('Rafael Mendez', 'rafael.mendez@empresa.com', 'TI', 'Analista de Soporte', '2023-06-10', 0, 15.5, 'hibrido'),  
            ('Juliana García', 'juliana.garcía@empresa.com', 'Ingeniería', 'Desarrolladora Front-end', '2021-09-25', 12, 0.0, 'remoto'),  
            ('Bruno Alvarez', 'bruno.alvarez@empresa.com', 'Diseño', 'Diseñador UX/UI', '2022-04-18', 8, 3.5, 'hibrido'),  
            ('Camila Herrera', 'camila.herrera@empresa.com', 'Atención al Cliente', 'Analista de Atención al Cliente', '2024-01-05', 0, 0.0, 'hibrido'),  
            ('Eric Monné', 'eric.monne@chocolatech.com', 'Producto', 'Instructor de Cursos', '2024-01-15', 25, 8.0, 'hibrido')
        ]
        
        empleados_final = []
        for emp in empleados_data:
            nombre = emp[0]
            fecha_ingreso = emp[4] # 'YYYY-MM-DD'
            anio = fecha_ingreso.split('-')[0]
            primer_nombre = nombre.split(' ')[0].lower()
            
            # Lógica de contraseña única: Chocola![Año][Nombre en minúsculas]
            # Ej: Chocola!2022juan
            password_plana = f"Chocola!{anio}{primer_nombre}"
            pwd_hash = get_password_hash(password_plana)
            
            # Añadimos el hash al final de la tupla para la inserción
            empleados_final.append(emp + (pwd_hash,))
            logger.info(f"Creada credencial para {nombre}: {password_plana}")

        try:
            cursor.executemany('''
                INSERT INTO empleados (nombre, email, departamento, puesto, fecha_ingreso, saldo_vacaciones, banco_horas, modalidad, password_hash) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', empleados_final)
            conn.commit()
            logger.info("Base de datos poblada exitosamente con contraseñas individuales.")
        except Exception as e:
            logger.error(f"Error crítico en la inserción: {e}")
            conn.rollback()
    else:
        logger.info(f"La base de datos ya contiene {count} empleados. No se requiere reinicialización.")

    conn.close()

def load_manual_to_chroma(file_path: str):
    logger.info(f"Iniciando ingesta vectorial desde {file_path}...")
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except FileNotFoundError:
        logger.error(f"Error: No se encontró el archivo {file_path}")
        return

    # Configuración del divisor de texto de LangChain
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=150,
        length_function=len,
        is_separator_regex=False,
        separators=["\n\n", "\n", ".", " ", ""]
    )
    
    chunks = text_splitter.split_text(content)
    
    documents = []
    ids = []
    metadatas = []
    
    for i, chunk in enumerate(chunks):
        documents.append(chunk.strip())
        ids.append(f"chunk_{i}_{int(time.time())}") # ID único para evitar colisiones
        metadatas.append({
            "source": file_path,
            "chunk_index": i
        })
    
    if documents:
        collection.upsert(documents=documents, ids=ids, metadatas=metadatas)
        logger.info(f"Éxito: {len(documents)} fragmentos (chunks) procesados con LangChain en ChromaDB.")

if __name__ == "__main__":

    initialize_database()
    load_manual_to_chroma(settings.FILE_PATH)
