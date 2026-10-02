# CLAUDE.md - Guía de Desarrollo del Sistema ATS

## 🔴 Lo primero en cada sesión

Leer **`docs/estado/ESTADO.md`**: dice la fase activa, qué módulo se está tocando y qué sigue
sin verificar. El mapa de fases está en `docs/estado/FASES.md` y el día a día en `docs/estado/BITACORA.md`.
Al terminar la sesión se anota el día en la bitácora y se actualiza el estado si cambió.

## Estado del proyecto

Los 7 módulos están **construidos en su versión base**: PostgreSQL + Backend (FastAPI) +
Frontend (React/Vite) con Docker Compose, siguiendo `docs/objetivo_general-v2.md` y
`docs/architecture_plan-v2.md`. "Construido" no es "verificado": lo comprobado de verdad, módulo
por módulo, está en `docs/estado/ESTADO.md`.

## Comandos de Docker Compose

- **Levantar todo el entorno**: `docker compose up --build`
- **Levantar en segundo plano**: `docker compose up --build -d`
- **Ver logs**: `docker compose logs -f` (o `-f backend` / `-f frontend` / `-f db`)
- **Detener**: `docker compose down`
- **Detener y reiniciar la base de datos desde cero**: `docker compose down -v`
- **Estado de contenedores**: `docker compose ps`

Servicios expuestos:
- Frontend: [http://localhost:3000](http://localhost:3000)
- Backend (API + docs interactivos): [http://localhost:8000/docs](http://localhost:8000/docs)
- PostgreSQL: `localhost:5432`

Ambos `backend/` y `frontend/` se montan como volumen: los cambios en el código
recargan en caliente (uvicorn `--reload` / Vite HMR) sin necesidad de reconstruir
la imagen, salvo que cambien las dependencias (`requirements.txt` / `package.json`).

## Backend (Python 3.12 / FastAPI / SQLAlchemy / Alembic)

- **Ejecutar pruebas**: `docker compose exec backend pytest`
- **Pruebas con cobertura**: `docker compose exec backend pytest --cov=app`
- **Generar una migración nueva**: `docker compose exec backend alembic revision --autogenerate -m "descripcion"`
- **Aplicar migraciones manualmente**: `docker compose exec backend alembic upgrade head`
  (ya se ejecuta automáticamente al iniciar el contenedor `backend`)
- **Linter y formateo**: `docker compose exec backend black app/` / `docker compose exec backend flake8 app/`
- **Abrir una shell dentro del contenedor**: `docker compose exec backend bash`

### Estructura

```
backend/app/
├── api/v1/        # Routers REST: auth, users, cargos, vacantes, public, postulaciones,
│                  # evaluaciones (anidado bajo /postulaciones), contactos, dashboard
├── core/          # config.py (Settings), database.py (engine/session), security.py (JWT/RBAC), utils.py (slug)
├── models/        # Modelos SQLAlchemy 2.0, uno por tabla (roles, usuarios, cargos, ...)
├── schemas/       # Pydantic: *Create / *Out por recurso
├── services/      # Lógica de negocio: cv_parser_service, linkedin_service, whatsapp_service,
│                  # pipeline_service (reglas de transición), evaluation_service
├── seed.py        # Seed idempotente: roles, usuarios demo, cargos demo (corre en el startup)
└── main.py        # App FastAPI, CORS, lifespan (seed), monta /api/v1
```

**Nota de alcance**: por simplicidad, las consultas de acceso a datos viven directamente
en los routers en lugar de una capa `repositories/` separada (que sí se menciona en
`docs/architecture_plan-v2.md`). Es una decisión consciente para este tamaño de proyecto,
no una omisión.

### Autenticación y roles

JWT (`python-jose`) + bcrypt (`passlib`). Roles: `super_admin`, `reclutador`,
`entrevistador`. El registro público (`POST /api/v1/auth/register`) siempre crea un
usuario `reclutador`; solo un `super_admin` puede cambiar roles (`PUT /users/{id}/role`).

### Usuarios de demo (creados por el seed automático)

Contraseña para los tres: `Demo1234!`

- `admin@atsdemo.com` → Super Admin
- `reclutador@atsdemo.com` → Reclutador / Empleador
- `entrevistador@atsdemo.com` → Entrevistador / Evaluador

### Parser de CV

`app/services/cv_parser_service.py` extrae texto de `.pdf` (pdfplumber) y `.docx`
(docx2txt) y aplica **heurísticas con expresiones regulares** (no IA/NLP) para
adivinar nombre, email, teléfono, cédula, nivel de instrucción y experiencia laboral.
El formato `.doc` binario legado no es soportado (se pide convertir a `.docx`/`.pdf`).
Es un punto de partida funcional, no un extractor de precisión garantizada.

### LinkedIn / WhatsApp

- `linkedin_service.py`: en modo mock (credenciales por defecto) genera un
  `linkedin_post_id` determinístico sin llamar a ninguna API externa real. El código
  para la integración real está documentado en comentarios dentro del archivo.
- `whatsapp_service.py`: genera un enlace `https://api.whatsapp.com/send?text=...`
  (no requiere credenciales, es solo construcción de URL).

## Frontend (React 18 / Vite / TypeScript / Tailwind)

```
frontend/src/
├── components/    # layout (Sidebar, Topbar), kanban, comunes (Modal, Badge, Card...)
├── views/         # Una vista por módulo + públicas (Postular, VacanteExpirada)
├── store/         # Zustand: authStore (JWT + user) y dataStore (cache de la API)
├── services/      # Un archivo por recurso: llamadas fetch tipadas a /api/v1/...
├── lib/           # apiClient.ts (fetch wrapper + auth header + manejo 401), pipelineStages.ts
└── types/         # Interfaces TS que reflejan los schemas Pydantic del backend
```

- El estado global vive en `store/` (Zustand); cada acción async llama a un `services/*Service`
  y actualiza el store con la respuesta. Los componentes nunca llaman `fetch` directamente.
- `VITE_API_BASE_URL` (por defecto `http://localhost:8000/api/v1`) apunta al backend.
- Sin backend real: el login fallará (ya no hay modo mock). Levanta siempre los 3 servicios.

## Convenciones de código

- **Python**: Type hints obligatorios, funciones cortas (SRP), `snake_case`/`PascalCase`/`UPPER_CASE`,
  nunca `except Exception: pass`. Endpoints REST en plural y minúsculas.
- **TypeScript**: estricto, componentes funcionales con hooks, Tailwind para estilos.
- **Flujo de trabajo agéntico**: Vertical Slices (DB → API → UI → Tests) por módulo.

## Próximos pasos no implementados (fuera de alcance de esta fase)

- Subida real de archivos (CVs, documentos de vacante) a almacenamiento persistente
  (hoy el CV se analiza en memoria y `cv_documento_url` queda como placeholder).
- Integración real con LinkedIn Job Posting API (hoy en modo mock).
- Capa `repositories/` separada de los routers.
- Guardas de ruta en el frontend por rol (hoy solo se oculta la navegación; el backend
  sí aplica RBAC en cada endpoint).
