# CLAUDE.md - Guía de Desarrollo y Ejecución con Docker Compose para Claude Code

## 🚀 Instrucción de Inicio para Claude Code / Antigravity

> **INSTRUCCIÓN PRINCIPAL PARA CLAUDE**: Al recibir este proyecto, lee atentamente los 3 archivos de especificación (`objetivo_general.md`, `architecture_plan.md` y `CLAUDE.md`). Genera la estructura completa de carpetas, los Dockerfiles para Backend y Frontend, el archivo `docker-compose.yml`, y ejecuta la construcción de la aplicación completa paso a paso usando **Docker Compose**.

---

## 🛠️ Comandos de Orquestación con Docker Compose

Todo el desarrollo, ejecución y pruebas se maneja preferentemente dentro del entorno contenerizado:

### 1. Gestión del Entorno Completo
- **Levantar todo el proyecto (DB + Backend + Frontend)**: `docker compose up --build -d`
- **Verificar estado de los contenedores**: `docker compose ps`
- **Ver logs en tiempo real**: `docker compose logs -f`
- **Detener todos los servicios**: `docker compose down`
- **Detener y limpiar volúmenes (reiniciar DB desde cero)**: `docker compose down -v`

### 2. Backend (Python / FastAPI / DRF) en Docker
- **Ejecutar Pruebas Unitarias e Integración**: `docker compose exec backend pytest`
- **Ejecutar Pruebas con Cobertura**: `docker compose exec backend pytest --cov=app`
- **Generar Migración de DB (Alembic)**: `docker compose exec backend alembic revision --autogenerate -m "nombre_migracion"`
- **Aplicar Migraciones**: `docker compose exec backend alembic upgrade head`
- **Linter & Formateo**: `docker compose exec backend black app/` && `docker compose exec backend flake8 app/`

### 3. Frontend en Docker
- **Ejecutar Pruebas de Frontend**: `docker compose exec frontend npm run test`
- **Build de Producción**: `docker compose exec frontend npm run build`

---

## 🎨 Convenciones de Código y Estilo

1. **Python (PEP 8 & Clean Code)**:
   * Uso obligatorio de **Type Hints** en todos los parámetros y retornos de funciones.
   * Funciones cortas, responsabilidad única (SRP), máximo 25 líneas por función.
   * Nombrado: `snake_case` para variables y funciones; `PascalCase` para clases/modelos; `UPPER_CASE` para constantes.
   * Manejo de excepciones explícito: nunca usar `except Exception: pass`.

2. **API REST / JSON**:
   * Endpoints en minúsculas y plural (ej. `/api/v1/vacantes`, `/api/v1/cargos`).
   * Retornos estandarizados: `200 OK`, `201 Created`, `400 Bad Request`, `401 Unauthorized`, `403 Forbidden`, `404 Not Found`, `410 Gone` (para vacantes expiradas).

3. **Base de Datos (PostgreSQL en Docker)**:
   * Claves primarias de tipo `UUID` para seguridad y escalabilidad.
   * Campos `JSONB` para estructuras flexibles (detalles de CV, respuestas filtro).
   * Nombres de tablas en plural y minúsculas (`vacantes`, `postulantes`).

4. **Flujo de Trabajo Agéntico**:
   * Desarrollar en **Vertical Slices** (Base de Datos -> API Backend -> UI Frontend -> Tests).
   * Probar de manera autónoma ejecutando `docker compose exec backend pytest` después de cada cambio significativo.
