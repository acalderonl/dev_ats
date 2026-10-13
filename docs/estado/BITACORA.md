# Bitácora — día a día

Lo más reciente arriba. Una entrada por día trabajado. Para no inventar lo que se hizo:
`git log --since=midnight --format="%h %s"` y las fechas de los archivos.

Cada entrada separa **lo verificado** de **lo que solo se escribió**. Un archivo creado no es
una funcionalidad que funcione.

---

## 2026-10-12 — Día 5 · Afinar el formulario de Cargos

**Fase:** M1 otra vez, a petición del dueño. **S.1 sigue sin empezar**: la etapa 2 no se ha tocado.

**Hecho**
- **Sección 4 admite hasta dos** niveles, títulos y áreas. Cada nivel lleva su propio estado
  (completa / en curso), así que pasan de cuatro columnas sueltas a tres tablas (migración 0005).
  El botón de añadir se deshabilita al llegar a dos, y **el engranaje se movió a la cabecera** del
  campo para que no baje al añadir una fila.
- Un valor ya elegido deja de ofrecerse en la otra fila: no tiene sentido exigir dos veces el mismo
  nivel, y la clave primaria de la tabla puente lo rechazaría igualmente.
- **El Enter ya no crea competencias parecidas.** Antes, con el aviso delante, Enter creaba igual.
  Ahora bloquea y explica; el botón "Crear" también queda deshabilitado en ese caso.
- **Checklist en el paso 7**: experiencia en empresas similares, en cargos similares e interna en
  otros cargos.

**Verificado**
- **53 pruebas en verde** (eran 48). Nuevas: tope de dos, nivel repetido, estado inválido, checklist
  y que editar reemplaza la educación en vez de acumularla.
- En PostgreSQL: dos niveles guardados con SU estado (`Tercer Nivel`/completa y `Maestría`/en_curso)
  y el checklist con los tres valores correctos.
- El Enter con los **dos controles**: "Trabajo en equipos" no creó nada (solo sigue existiendo
  "Trabajo en equipo"), y "Negociacion bajo presion" sí se creó. El bloqueo no rompió la creación.
- La migración 0005 conservó la educación del cargo que ya la tenía.
- Fuga cero: 5 cargos antes de la suite, 5 después.

**Pendiente / avisos**
- 🔴 La etapa 2 (seguridad) sigue entera sin empezar. Ya van dos sesiones seguidas en M1.
- El bloqueo por parecido usa un umbral de 0,55: dos competencias legítimamente distintas pero
  parecidas no se pueden crear. Si molesta, hay que subir el umbral o añadir una confirmación.

---

## 2026-10-02 — Día 4 · Rehacer el módulo de Cargos

**Fases:** T.1 y T.1B cerradas. M1 reconstruido (fuera del mapa original: lo pidió el dueño en caliente).

**Hecho**
- **El cargo pasa a ser un descriptivo de puesto** con 7 bloques: identificación, misión, actividades,
  educación formal, formación, habilidades blandas y experiencia.
- Los valores repetibles salen de **catálogos con CRUD propio** (el engranaje junto a cada selector):
  nombres de cargo, clasificaciones, niveles de educación, títulos y áreas académicas. Un solo router
  genérico los sirve a los cinco; añadir los tres últimos fueron tres líneas.
- **Competencias compartidas entre cargos**, con dos defensas contra duplicados: el nombre normalizado
  (sin tildes ni mayúsculas) es único, y el buscador sugiere los parecidos con trigramas de PostgreSQL.
  "Trabajo en equipos" encuentra "Trabajo en equipo" con 0,84 de parecido y avisa antes de crear otro.
- Actividades con **estrella de favorita**, que sube la actividad al principio; el orden se aplica
  también al guardar.
- Se quitaron de las tarjetas los botones *Preguntas* y *Desactivar*. Ahora **el estado es el botón**,
  con confirmación de Sí/Cancelar, y **la tarjeta entera abre el modal para editar**.
- 4 migraciones (0002 a 0004) sin perder datos; `black`/`flake8` configurados al ancho real (120).

**Verificado**
- **48 pruebas en verde** (eran 19 escritas y sin correr el día 1).
- Cada cambio comprobado **en PostgreSQL**, no en pantalla: orden de favoritas, competencias con su
  exigencia, educación, experiencia, y que editar no duplica ni el cargo ni sus competencias.
- Activar/desactivar con **los dos controles**: Cancelar no cambia nada; Sí sí.
- Fuga cero: 4 cargos en desarrollo antes de la suite, 4 después.

**Corregido de días anteriores**
- Un `as const` sobre un ternario en `VacantesView.tsx` que era TypeScript inválido y venía del commit
  inicial: bloqueaba la verificación de tipos.
- `CLAUDE.md` documentaba `black app/`, que sin configuración habría reformateado 35 archivos de golpe.
- La base de pruebas se construía con `create_all` (desde los modelos), así que lo que vive solo en una
  migración —como la extensión `pg_trgm`— no existía al probar. Ahora aplica las migraciones reales.

**Errores propios que conviene recordar**
- Al borrar un bloque con PowerShell leí sin especificar codificación y destrocé todos los acentos del
  archivo; al repararlo me precipité con un reemplazo de bytes a ciegas y lo empeoré. Es la trampa que
  documenta la skill `testing-forense-maximo`, escrita dos días antes. **Leer siempre con `-Encoding`.**
- Una comprobación de fuga cero dio un resultado vacío por comparar cadenas con espacios finales en vez
  de números. El instrumento mentía, no el sistema.

**Pendiente / avisos**
- 🔴 La etapa 2 (seguridad) sigue entera abierta: el sistema no puede tocar internet.
- 🔴 **Ya no hay forma de crear preguntas filtro** desde la aplicación (fase M1.5). El portal del
  candidato solo verá las que creó el seed.
- Las listas de niveles y áreas se sembraron de memoria: conviene contrastarlas con la fuente oficial.

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
