# Bitácora — día a día

Lo más reciente arriba. Una entrada por día trabajado. Para no inventar lo que se hizo:
`git log --since=midnight --format="%h %s"` y las fechas de los archivos.

Cada entrada separa **lo verificado** de **lo que solo se escribió**. Un archivo creado no es
una funcionalidad que funcione.

---

## 2026-10-01 — Día 3 · Organizar el trabajo

**Fase:** ninguna (trabajo de organización)

**Hecho**
- Sistema de seguimiento en `docs/estado/`: este archivo, `ESTADO.md` (dónde estamos) y `FASES.md`
  (el mapa de mejoras). `CLAUDE.md` ahora manda leer el estado al empezar cada sesión.
- Mapa de fases levantado desde los huecos **reales** del código, no desde una lista genérica:
  el campo de subir documento que no sube nada, `cv_documento_url` con un texto de relleno,
  `match_score` siempre vacío, `promedio_puntaje` que nadie llama, exportar y etiquetar que solo
  muestran un aviso.
- **El dueño fijó el orden**: destino *producción real*, *cimientos primero*, los 7 módulos importan.
  Con eso el mapa se reorganizó en **6 etapas y 37 fases**, y aparecieron 5 fases de seguridad (`S.x`)
  y 3 de despliegue (`D.x`) que antes ni figuraban.

**Verificado**
- Los 4 bloqueantes de seguridad se confirmaron **leyendo el código**, no de memoria:
  `config.py:10` tiene `SECRET_KEY` por defecto y publicado en GitHub (permite fabricar un token de
  super admin); `main.py:18` corre el seed en cada arranque sin mirar el entorno (crearía un admin con
  contraseña conocida en un servidor real); `cv_parser_service.py:127` lee el archivo subido sin límite
  de tamaño; el portal público no tiene límite de peticiones.
- Las 37 fases tienen identificador único, sin repetidos, y los conteos por etapa cuadran (4/5/3/6/4/15).

**Medido**
- 52 archivos Python (1.787 líneas), 35 TypeScript (2.394 líneas), 6 archivos de prueba.
- Archivos tocados por día: 152 el 28-sep, 2 el 29-sep, los de hoy el 1-oct.

**Pendiente / avisos**
- 🔴 La suite de pruebas **sigue sin ejecutarse nunca**. Es la fase activa (T.1).
- 🔴 La etapa 2 entera sigue abierta: el sistema no puede tocar internet hasta cerrarla.
- Docker Desktop está apagado desde el reinicio: hay que levantarlo antes de T.1.
- Quedan 3 decisiones del dueño anotadas al final de `FASES.md` (repo público o privado, dónde se
  despliega, dónde se guardan los CVs).

---

## 2026-09-29 — Día 2 · Levantar el stack, absorber skills y publicar

**Fase:** ninguna (todavía no existía este sistema)

**Hecho**
- Docker Desktop instalado y funcionando. El bloqueo real era WSL2 sin las características de
  Windows habilitadas; lo resolvió el usuario con permisos de administrador y dos reinicios.
- **Dos bugs reales corregidos**, ambos impedían arrancar el backend:
  - Faltaba `email-validator`, que Pydantic necesita para `EmailStr`.
  - `passlib` 1.7.4 es incompatible con `bcrypt` 5.x; se fijó `bcrypt==4.0.1`.
- Skills de testing de Keybidigital instaladas en `~/.claude/skills/` y **traducidas a Windows**
  (PowerShell 5.1, `shell: powershell`, permisos y hook adaptados).
- Repo git creado y publicado: https://github.com/acalderonl/dev_ats (111 archivos).

**Verificado**
- Los 3 contenedores arriba; `/health` responde.
- Login real contra la API (devuelve JWT) y desde el navegador.
- Crear una vacante desde la interfaz: se guardó en PostgreSQL.
- El commit en GitHub coincide con el local y no se subió `Skills/`, `.env` ni `node_modules`.

**No verificado**
- Todo lo demás. Se dijo que el stack "quedaba funcionando" apoyándose en dos comprobaciones
  manuales, sin correr las pruebas.

---

## 2026-09-28 — Día 1 · Construir el sistema completo

**Fase:** ninguna (todavía no existía este sistema)

**Hecho**
- Leídos los 3 documentos de especificación que llegaron ese día.
- Primera versión: solo frontend con datos simulados (7 módulos de interfaz).
- A petición del usuario, se amplió al **alcance completo**: backend FastAPI + SQLAlchemy 2.0 +
  Alembic sobre PostgreSQL, con autenticación JWT y RBAC, parser de CV, reglas del pipeline,
  LinkedIn simulado y WhatsApp.
- El frontend se reconectó a la API real y se eliminaron los datos simulados.
- 19 pruebas escritas cubriendo autenticación, expiración de vacantes, la regla de autorización
  del pipeline y sus transiciones.

**Medido**
- 152 archivos escritos.

**No verificado**
- Nada se ejecutó: no había Docker, ni Node, ni Python en el equipo. Todo el código de este día
  se escribió sin poder correrlo una sola vez.
