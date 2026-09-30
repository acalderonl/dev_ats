# Plan de Arquitectura Técnica y Especificación de Endpoints REST - Sistema ATS

## 1. Arquitectura de Software y Estructura del Proyecto

El proyecto sigue los principios de **Clean Architecture** (Arquitectura Limpia) y separación de responsabilidades para garantizar mantenibilidad, legibilidad (cumpliendo con Robert C. Martin - Clean Code y PEP 8) y facilitación del desarrollo agéntico con Claude Code / Antigravity. todo el sistema se encuentra completamente contenerizado mediante **Docker Compose**.

```
ats_project/
├── backend/
│   ├── app/
│   │   ├── api/                  # Controladores y Endpoints REST (FastAPI / DRF)
│   │   │   ├── v1/
│   │   │   │   ├── auth.py
│   │   │   │   ├── users.py
│   │   │   │   ├── cargos.py
│   │   │   │   ├── vacantes.py
│   │   │   │   ├── postulantes.py
│   │   │   │   ├── postulaciones.py
│   │   │   │   ├── evaluaciones.py
│   │   │   │   └── dashboard.py
│   │   ├── core/                 # Configuración global, seguridad (JWT), DB engine
│   │   │   ├── config.py
│   │   │   ├── database.py
│   │   │   └── security.py
│   │   ├── domain/               # Entidades de negocio y reglas puras
│   │   ├── models/               # Modelos relacionales ORM (SQLAlchemy / PostgreSQL)
│   │   ├── schemas/              # Esquemas DTO / Pydantic para validación de entrada/salida
│   │   ├── services/             # Capa de Lógica de Negocio
│   │   │   ├── cv_parser_service.py     # Motor de extracción PDF/DOCX
│   │   │   ├── linkedin_service.py      # Cliente HTTP para API de LinkedIn
│   │   │   ├── whatsapp_service.py      # Generador de enlaces y payload
│   │   │   ├── pipeline_service.py      # Reglas de transición de estados y autorizaciones
│   │   │   └── evaluation_service.py
│   │   └── repositories/         # Capa de Acceso a Datos (Queries PostgreSQL)
│   ├── tests/                    # Pruebas unitarias e integración (pytest)
│   ├── alembic/                  # Migraciones de base de datos PostgreSQL
│   ├── Dockerfile                # Configuración de contenedor Python 3.12
│   ├── requirements.txt
│   └── main.py
├── frontend/                     # Aplicación Web Responsive (SPA/SSR)
│   ├── src/
│   │   ├── components/           # Componentes UI reutilizables (Kanban, Tables, Modals)
│   │   ├── views/                # Páginas principales (Dashboard, Vacantes, Portal Público)
│   │   ├── services/             # Clientes API HTTP (Axios / Fetch)
│   │   ├── store/                # Manejo de estado global
│   │   └── styles/               # Tokens de diseño UX/UI (Tailwind / CSS Variables)
│   ├── public/
│   ├── Dockerfile                # Configuración de contenedor Frontend (Node / Nginx)
│   └── package.json
├── CLAUDE.md                     # Convenciones de desarrollo y comandos para Claude Code
├── docker-compose.yml            # Orquestador del ecosistema completo (DB + Backend + Frontend)
├── .env.example                  # Variables de entorno de muestra
└── objetivo_general.md           # Especificación funcional y de negocio
```

---

## 2. Configuración de Orquestación con Docker Compose

El archivo `docker-compose.yml` en la raíz del proyecto permite iniciar todo el ambiente con un solo comando: `docker compose up --build`.

### 2.1 Estructura Recomendada de `docker-compose.yml`

```yaml
version: '3.8'

services:
  db:
    image: postgres:16-alpine
    container_name: ats_postgres_db
    restart: always
    environment:
      POSTGRES_USER: ${POSTGRES_USER:-ats_user}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-ats_password}
      POSTGRES_DB: ${POSTGRES_DB:-ats_db}
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER:-ats_user} -d ${POSTGRES_DB:-ats_db}"]
      interval: 5s
      timeout: 5s
      retries: 5

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: ats_python_backend
    restart: always
    command: sh -c "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql://${POSTGRES_USER:-ats_user}:${POSTGRES_PASSWORD:-ats_password}@db:5432/${POSTGRES_DB:-ats_db}
      SECRET_KEY: ${SECRET_KEY:-supersecretkey_ats_2026}
      LINKEDIN_CLIENT_ID: ${LINKEDIN_CLIENT_ID:-mock_client_id}
      LINKEDIN_CLIENT_SECRET: ${LINKEDIN_CLIENT_SECRET:-mock_client_secret}
    volumes:
      - ./backend:/app
    depends_on:
      db:
        condition: service_healthy

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    container_name: ats_web_frontend
    restart: always
    ports:
      - "3000:3000"
    environment:
      VITE_API_BASE_URL: http://localhost:8000/api/v1
    volumes:
      - ./frontend:/app
      - /app/node_modules
    depends_on:
      - backend

volumes:
  postgres_data:
```

---

## 3. Especificación Completa de Endpoints REST API (v1)

### 3.1 Módulo de Autenticación y Administración de Usuarios (RBAC)

* **`POST /api/v1/auth/register`**
  * **Descripción**: Registra un nuevo usuario empleador/reclutador con correo.
  * **Body**: `{ "email": "str", "password": "str", "nombres": "str", "apellidos": "str" }`
  * **Respuesta**: `201 Created` - `{ "id": "uuid", "email": "str", "rol": "reclutador" }`

* **`POST /api/v1/auth/login`**
  * **Descripción**: Autenticación de usuario. Devuelve Token JWT de acceso.
  * **Body**: `{ "email": "str", "password": "str" }`
  * **Respuesta**: `200 OK` - `{ "access_token": "jwt_str", "token_type": "bearer", "user": {...} }`

* **`GET /api/v1/users`** *(Requiere Rol SuperAdmin/Admin)*
  * **Descripción**: Lista todos los usuarios registrados en PostgreSQL para su administración.

* **`PUT /api/v1/users/{user_id}/role`**
  * **Descripción**: Asigna o actualiza el rol de un usuario (Super Admin, Reclutador, Entrevistador).

---

### 3.2 Módulo de Gestión de Cargos y Preguntas Filtro

* **`GET /api/v1/cargos`**
  * **Descripción**: Obtiene el catálogo de cargos de la organización.
* **`POST /api/v1/cargos`**
  * **Descripción**: Crea un nuevo cargo.
  * **Body**: `{ "nombre": "Desarrollador Senior", "departamento": "Tecnología", "descripcion": "str" }`

* **`GET /api/v1/cargos/{cargo_id}/preguntas-filtro`**
  * **Descripción**: Lista las preguntas filtro vinculadas a un cargo específico.
* **`POST /api/v1/cargos/{cargo_id}/preguntas-filtro`**
  * **Descripción**: Agrega una pregunta filtro parametrizada al cargo.
  * **Body**:
    ```json
    {
      "pregunta": "¿Cuántos años de experiencia tiene en Python?",
      "tipo_respuesta": "numero",
      "opciones": null,
      "es_eliminatoria": true,
      "respuesta_correcta": ">= 3"
    }
    ```

---

### 3.3 Módulo de Creación y Publicación de Vacantes

* **`POST /api/v1/vacantes`**
  * **Descripción**: Permite al empleador crear una nueva vacante adjuntando el perfil técnico (`.pdf`, `.docx`, `.doc`).
  * **Form Data**:
    * `titulo`: String
    * `cargo_id`: Int
    * `descripcion`: String
    * `fecha_limite`: Datetime (ISO 8601)
    * `archivo_adjunto`: File Binary (`.pdf`, `.docx`, `.doc`)
  * **Respuesta**: `201 Created` - Incluye el `slug` generado y el `url_postulacion_publica`.

* **`POST /api/v1/vacantes/{vacante_id}/publish-linkedin`**
  * **Descripción**: Conecta con la API de LinkedIn Job Posting para publicar la oferta automáticamente.
  * **Payload hacia LinkedIn**: Cumple con los parámetros exigidos por LinkedIn API (`title`, `description`, `location`, `employmentStatus`, `listedAt`, `companyApplyUrl`).
  * **Respuesta**: `200 OK` - Regresa el `linkedin_post_id` para trazabilidad.

* **`GET /api/v1/vacantes/{vacante_id}/share-whatsapp`**
  * **Descripción**: Genera el enlace de WhatsApp (`https://api.whatsapp.com/send?text=...`) codificado con el texto promocional y el link directo a la vacante.

---

### 3.4 Módulo del Portal Público del Postulante (Parsing CV & Postulación)

* **`GET /api/v1/public/vacantes/{slug}`**
  * **Descripción**: Consulta pública de la vacante.
  * **Lógica de Caducidad**:
    * Si `fecha_limite < NOW()`, responde `410 Gone` con la directiva para renderizar la **Landing Page de Expiración** (mensaje de vacante expirada y foto enlazada al LinkedIn principal).
    * Si está activa, retorna el detalle de la vacante y la lista de preguntas filtro asociadas a su cargo.

* **`POST /api/v1/public/parse-cv`**
  * **Descripción**: Recibe el archivo de currículum subido por el postulante (`.pdf`, `.docx`, `.doc`), ejecuta el motor de *CV Parsing* en backend y devuelve los campos extraídos para auto-llenar el formulario.
  * **Respuesta**:
    ```json
    {
      "nombres": "Juan",
      "apellidos": "Pérez",
      "edad": 29,
      "cedula": "1712345678",
      "formacion_secundaria": { "institucion": "Colegio Central", "titulo": "Bachiller", "anio": 2013 },
      "formacion_superior": { "institucion": "Universidad Nacional", "titulo": "Ingeniero de Sistemas", "estado": "graduado" },
      "nivel_instruccion": "Tercer Nivel",
      "titulos": ["Ingeniero de Sistemas"],
      "experiencia_laboral": [
        {
          "cargo": "Backend Developer",
          "empresa": "Tech Solutions",
          "fecha_desde": "2021-01-15",
          "fecha_hasta": null,
          "actualmente": true
        }
      ]
    }
    ```

* **`POST /api/v1/public/postular`**
  * **Descripción**: Registra formalmente la postulación con los datos confirmados/editados por el postulante y las respuestas a las preguntas filtro.
  * **Estado Inicial**: `pendiente_autorizacion`.

---

### 3.5 Módulo de Pipeline de Reclutamiento y Autorizaciones

* **`POST /api/v1/postulaciones/{id}/autorizar`**
  * **Descripción**: Ejecuta el pre-chequeo obligatorio. Un reclutador/autorizador aprueba que la solicitud ingrese al Pipeline de tratamiento.
  * **Respuesta**: Transiciona el estado a `postulacion_revisada` y registra el `autorizado_por` y `fecha_autorizacion`.

* **`PATCH /api/v1/postulaciones/{id}/pipeline-status`**
  * **Descripción**: Cambia el estado del candidato en el tablero Kanban.
  * **Restricción**: Solo permitido si la postulación ya fue **autorizada previamente**.
  * **Estados permitidos**: `postulacion_revisada` -> `en_revision` -> `preseleccionado` -> `evaluaciones` -> `entrevista` -> `contratado` / `descartado`.

---

### 3.6 Módulo de Directorio de Contactos (Talent Pool)

* **`GET /api/v1/contactos`**
  * **Descripción**: Listado tabular global de todos los candidatos registrados históricamente.
  * **Parámetros de Búsqueda**: `?q=python&nivel_instruccion=Tercer+Nivel&cargo=Developer`
  * **Soporta**: Paginación, ordenamiento por experiencia y exportación de datos.

---

### 3.7 Módulo de Evaluaciones y Calificaciones

* **`GET /api/v1/postulaciones/{id}/evaluaciones`**
  * **Descripción**: Obtiene el expediente de evaluaciones confidenciales reservadas del candidato.
* **`POST /api/v1/postulaciones/{id}/evaluaciones`**
  * **Descripción**: Registra observaciones, puntajes psicométricos o técnicos por parte de los entrevistadores.

---

### 3.8 Módulo de Dashboard Central (Home)

* **`GET /api/v1/dashboard/metrics`**
  * **Descripción**: Proporciona los KPIs clave para la pantalla inicial (Home):
    * Vacantes Activas vs Expiradas.
    * Postulaciones totales y tasa de conversión por origen (LinkedIn / WhatsApp).
    * Embudo de candidatos por etapa del pipeline.

---

## 4. Guía de Diseño UX/UI e Interfaz Multiplataforma

### 4.1 Principios Visuales y Componentes Clave
1. **Diseño Responsive Primario**: Layout fluido basado en *CSS Grid* y *Flexbox*, asegurando una usabilidad limpia tanto en móviles (para postulantes) como en escritorios (para reclutadores).
2. **Tablero Kanban Interactivo**:
   * Drag-and-drop con retroalimentación visual clara.
   * Tarjetas con foto/iniciales, coincidencia de experiencia, etiquetas de preguntas filtro y botón de acción rápida para autorizar/aprobar.
3. **Formulario Inteligente de Postulación (Wizard UX)**:
   * **Paso 1**: Upload drag-and-drop de CV (`.pdf`, `.docx`). Spinner interactivo de "Analizando CV...".
   * **Paso 2**: Auto-completado visual de campos con resaltado de confianza para revisión fácil por parte del candidato.
   * **Paso 3**: Bloque dinámico de preguntas filtro con validación inmediata.
4. **Landing Page de Caducidad de Vacante**:
   * Diseño sobrio, limpio, libre de distracciones.
   * Foto/Logo institucional con enlace claro: *"Esta vacante ha expirado. Revisa nuestro perfil principal de LinkedIn para ver ofertas disponibles."*

---

## 5. Instrucciones para la Ejecución Autónoma en Claude Code con Docker Compose

Para garantizar que el desarrollo con Claude Code sea 100% fluido mediante contenedores:

1. **Uso de `CLAUDE.md`**: Colocar en la raíz del proyecto las instrucciones de comando para Docker Compose (`docker compose up --build`, `docker compose exec backend pytest`).
2. **Construcción Incremental (Vertical Slices)**:
   * **Fase 1**: Generar `docker-compose.yml`, Dockerfiles, modelos PostgreSQL (Alembic) y autenticación JWT.
   * **Fase 2**: Módulo de Cargos y Preguntas Filtro.
   * **Fase 3**: Creación de Vacantes + Parser CV + Landing de Postulación.
   * **Fase 4**: Pipeline Kanban de Reclutamiento + Regla de Autorización.
   * **Fase 5**: Integraciones externas (LinkedIn API Mock/Real + WhatsApp Sharing).
   * **Fase 6**: Directorio de Contactos, Evaluaciones y Dashboard.
3. **Pruebas de Integración Continuas**: Ejecutar `docker compose exec backend pytest` en cada *Vertical Slice* antes de dar por cerrada la tarea.
