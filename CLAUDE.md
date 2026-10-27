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

## 🔴 Antes de levantar: hace falta un `.env`

`SECRET_KEY` **no tiene valor por defecto** (fase S.1, cerrada el 2026-10-12): firma los JWT y
antes traía un valor publicado en este repositorio. Si falta, la aplicación no arranca y
`docker compose` se niega a levantar.

```bash
cp .env.example .env
```

Dentro, una clave propia: `python -c "import secrets; print(secrets.token_urlsafe(48))"`.

De esa clave **se deriva el cifrado de los secretos** guardados desde la pantalla de Configuración
(LinkedIn, correo). Rotarla invalida las sesiones abiertas y obliga a reintroducir esos secretos.

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
  🔴 Corren contra `ats_test_db`, **nunca** contra la base de desarrollo, y la recrean desde las
  migraciones en cada ejecución (`tests/conftest.py`). Si alguna prueba deja datos en `ats_db`, hay
  una fuga y se arregla en la configuración, no borrando a mano.
- **Pruebas con cobertura**: `docker compose exec backend pytest --cov=app`
- **Generar una migración nueva**: `docker compose exec backend alembic revision --autogenerate -m "descripcion"`
- **Aplicar migraciones manualmente**: `docker compose exec backend alembic upgrade head`
  (ya se ejecuta automáticamente al iniciar el contenedor `backend`)
- **Linter y formateo**: `docker compose exec backend black app/` / `docker compose exec backend flake8 app/`
- **Abrir una shell dentro del contenedor**: `docker compose exec backend bash`

### Estructura

```
backend/app/
├── api/v1/        # Routers REST: auth, users, cargos, catalogos, competencias, vacantes,
│                  # public, postulaciones, evaluaciones (anidado bajo /postulaciones),
│                  # contactos, dashboard, configuracion, media, compartir (este último fuera de /api/v1)
├── core/          # config.py (Settings + clave de cifrado), database.py, security.py (JWT/RBAC), utils.py (slug)
├── models/        # Modelos SQLAlchemy 2.0, uno por tabla (roles, usuarios, cargos, ...)
├── schemas/       # Pydantic: *Create / *Out por recurso
├── services/      # Lógica de negocio: cv_parser_service, linkedin_service, correo_service,
│                  # whatsapp_service, almacenamiento_service (imágenes),
│                  # configuracion_service (secretos cifrados),
│                  # pipeline_service (reglas de transición), evaluation_service
├── seed.py        # Seed idempotente: roles, usuarios demo, cargos demo (corre en el startup)
└── main.py        # App FastAPI, CORS, lifespan (seed), monta /api/v1
```

**Nota de alcance**: por simplicidad, las consultas de acceso a datos viven directamente
en los routers en lugar de una capa `repositories/` separada (que sí se menciona en
`docs/architecture_plan-v2.md`). Es una decisión consciente para este tamaño de proyecto,
no una omisión.

### Módulo de Cargos (el más desarrollado)

Un cargo es un **descriptivo de puesto**: identificación, misión, actividades (con favoritas, que
suben al principio), educación formal, formación, habilidades blandas y experiencia requerida.

- Los valores repetibles viven en **catálogos** (`/api/v1/catalogos/{catalogo}`): nombres de cargo,
  clasificaciones, niveles de educación, títulos y áreas académicas. Un router genérico los sirve a
  todos; añadir uno nuevo es una entrada en el diccionario `CATALOGOS` más su tabla.
- Las **competencias** (`/api/v1/competencias`) se comparten entre cargos. Para que no se dupliquen
  escritas de formas distintas: `nombre_normalizado` (sin tildes ni mayúsculas) es único por tipo, y
  la búsqueda sugiere las parecidas con trigramas (`pg_trgm`).
- En la interfaz, la tarjeta de un cargo lo abre para editar; su estado es el botón de activar o
  desactivar, con confirmación.

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

### Módulo de Vacantes

Una vacante es **un cargo puesto en circulación**: no se escribe un título, se elige el cargo y el
título se copia de él. Es una copia y no un `join` a propósito: de ella sale el `slug`, que es la
URL pública, y si siguiera al catálogo, renombrar un cargo rompería enlaces ya repartidos.

Tres conceptos que se confunden y son columnas distintas:

- `estado`: borrador / abierta / cerrada (el proceso de selección).
- `post_estado`: borrador / programado / publicado / error (la publicación).
- `visibilidad`: publica / interna / mixta (a quién llega).

Una vacante **interna** no aparece en el portal público aunque esté abierta y alguien tenga el
enlace, y no se puede publicar en LinkedIn.

### Configuración (`/configuracion`, solo `super_admin`)

Credenciales de LinkedIn y de correo, dominios corporativos y jornadas laborales. Los valores
marcados como secretos **se guardan cifrados** (Fernet, clave derivada de `SECRET_KEY`) y la API
**nunca los devuelve**: informa de si están puestos y de sus últimos cuatro caracteres.

Un campo ausente en el `PUT` no se toca. Importa: la pantalla manda los secretos vacíos porque no
los recibe; si vacío significara "borrar", guardar cualquier otra cosa mataría la integración.

### LinkedIn / correo / WhatsApp

Hay **dos caminos para llevar una vacante a LinkedIn**, y conviene no confundirlos:

**1. Sin credenciales — el botón «LinkedIn» de la tarjeta.** El sistema arma el texto, lo copia
al portapapeles y abre el compositor de LinkedIn (`sharing/share-offsite`) con el enlace de la
vacante. Quien pulsa Publicar es la persona. Por eso el post queda en estado **`compartido`, que
no es `publicado`**: desde aquí no se puede saber si llegó a publicarse, y afirmarlo sería mentir.

  El enlace que recibe LinkedIn **no** es el del formulario sino `/compartir/{slug}`
  (`api/v1/compartir.py`, montado fuera de `/api/v1`), una página que **genera el servidor** con
  las etiquetas Open Graph rellenas. Hace falta porque la aplicación es una SPA y el rastreador de
  LinkedIn no ejecuta JavaScript: con el enlace del formulario, la tarjeta saldría vacía. Quien
  abra esa página acaba en el formulario por la redirección. Solo se anuncia `og:image` si la
  vacante tiene imagen propia subida —el escudo es SVG y LinkedIn no los dibuja—.
  En producción la reenvía nginx; en desarrollo, el proxy de `vite.config.ts`.
  ⚠️ Para que la tarjeta se vea, esa URL tiene que ser **alcanzable desde internet**.

**2. Con credenciales — `linkedin_service.py`.** Publica en **el muro del reclutador** que conecta
su cuenta, que es la única vía automática sin aprobación de partner (productos *Sign In with
LinkedIn (OIDC)* + *Share on LinkedIn*, scope `w_member_social`). La página de empresa (Community
Management API) y el tablón de empleos (Talent Solutions) **exigen ser partner aprobado**. Sin
credenciales queda en **modo simulado** y lo declara, en vez de aparentar que algo salió a
internet.
  ⚠️ El token de autoservicio dura ~60 días y **no hay refresh token** fuera del programa de
  partners: hay que volver a conectar.

- `correo_service.py`: dos conexiones a elegir, **Gmail/Workspace** (servidor y puerto fijos,
  contraseña de aplicación) o **cualquier servidor SMTP** (servidor, puerto, cifrado, usuario).
  Hay un endpoint que prueba la conexión sin enviar nada.
- `whatsapp_service.py`: genera un enlace `https://api.whatsapp.com/send?text=...`
  (no requiere credenciales, es solo construcción de URL).

### Archivos subidos

`almacenamiento_service.py` guarda la imagen del post en el volumen `media_data` (sobrevive a
`docker compose down`, **no** a `down -v`) y la sirve `/api/v1/media`. Se valida **el tipo real por
los bytes, no la extensión**, el tamaño leyendo a trozos, y el nombre lo genera el servidor: el del
archivo subido no se usa nunca para construir la ruta.

## Marca

La aplicación es de la **Academia Naval Almirante Illingworth (ANAI)**. El escudo está en
`frontend/public/escudo-anai.svg` y los colores reales de la institución viven en
`tailwind.config.js`: `#0064b4` institucional (en `brand-600`, que es lo que ya usaba toda la
interfaz), `#003462` para franjas, `#1ea7fd` de acento y `#20395f` el azul del escudo.

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

## Próximos pasos no implementados

- **Publicar a la hora programada.** La fecha se guarda, pero nada la ejecuta: hoy hay que pulsar
  el botón. Falta un proceso que lo haga (fase M1.6). La pantalla lo advierte.
- **El seed corre en cada arranque sin mirar el entorno** (`main.py:18`): en un servidor real
  crearía un super admin con una contraseña publicada. Es la fase activa (S.2).
- **El CV del candidato se sigue analizando en memoria y tirando** (`cv_documento_url` es un
  relleno). La imagen del post ya va a un volumen: el CV puede seguir el mismo camino (M2.1).
- Crear preguntas filtro desde la aplicación (M1.5): hoy solo existen las del seed.
- Capa `repositories/` separada de los routers.
- Guardas de ruta en el frontend por rol (hoy solo se oculta la navegación; el backend
  sí aplica RBAC en cada endpoint).
