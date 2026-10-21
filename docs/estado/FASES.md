# Fases por módulo — el mapa de mejoras

Cada fase es un trozo de trabajo que cabe en **una sesión** y se puede dar por terminado sin ambigüedad.
Se trabaja **una fase a la vez**; cuál está activa lo dice `ESTADO.md`.

## Cómo está ordenado (decidido el 2026-10-01)

Tres decisiones del dueño mandan sobre el orden:

- **Destino: producción real.** Van a postular candidatos de verdad, con su cédula, su correo y su CV.
  Eso convierte la seguridad y el guardado de archivos en bloqueantes, no en mejoras.
- **Criterio: primero los cimientos.** Pruebas y CI antes que funcionalidad. Es más lento al principio
  y después cada cambio se verifica solo.
- **Alcance: importan los 7 módulos.** Ninguno se aparca; el orden lo deciden los dos puntos anteriores.

De ahí salen 6 etapas. **No se salta de etapa**: cada una existe porque la siguiente se apoya en ella.

## Nomenclatura

`M3.2` = módulo 3, fase 2. `T.x` = transversal. `S.x` = seguridad. `D.x` = despliegue.
Estados: `pendiente` · `en curso` · `hecha` · `descartada`.

## Qué significa "terminada"

Adaptado del kit de Keybidigital (`Skills/`), sin la maquinaria de turnos y ranuras que allí hace falta
por trabajar varias sesiones en paralelo. Aquí somos una persona y una sesión:

- **Validar** (lo normal, toda fase): las pruebas de lo que se tocó pasan en verde, **cada prueba nueva
  validada reintroduciendo el defecto** (si al romper el código a propósito la prueba no cae, la prueba no
  sirve), más lint y type check. Se restaura el código y se comprueba que quedó idéntico.
- **Certificar** (solo lo crítico: base de datos, seguridad, o lo que ve el candidato): además de lo
  anterior, e2e dos veces seguidas y que las pruebas no dejen basura en la base.

Una fase **no** está terminada porque la pantalla se vea bien. Ver la skill `testing-forense-maximo`.

---

# Etapa 1 — Terreno firme

Sin esto, ninguna fase posterior se puede dar por buena: no hay forma de saber si un cambio rompió algo.

| Fase | Qué | Terminada cuando | Estado |
|---|---|---|---|
| **T.1** | Correr la suite por primera vez | `pytest` en verde y el número de pruebas anotado en la bitácora | ✅ **hecha** (2026-10-01, 32 pruebas) |
| **T.1B** | Las pruebas no tocan la base de desarrollo | Corren contra `ats_test_db`, construida desde las migraciones; control positivo de fuga cero | ✅ **hecha** (2026-10-01) |
| **T.2** | Validar las pruebas por mutación | Cada prueba cae al reintroducir su defecto; el código queda idéntico (comprobado por hash) | pendiente |
| **T.3** | Lint y type check | `black`, `flake8` y `tsc --noEmit` salen con código 0 | 🟡 pasan hoy, falta dejarlo automático (ver T.4) |
| **T.4** | CI en GitHub Actions | Un push abre el workflow y sale verde en GitHub, no solo en local | pendiente |

# Etapa 2 — Bloqueantes de seguridad

**Verificado en el código el 2026-10-01.** Nada de esta etapa es una precaución teórica: eran cuatro
puertas abiertas que existían de verdad, y el repo es **público**. Mientras esta etapa no esté
cerrada, el sistema no puede salir a internet.

> **S.1 se cerró el 2026-10-12**, y no por disciplina: ese mismo día se construyó el guardado de
> credenciales de terceros (LinkedIn, correo) en la base. Hacerlo con una clave de firma publicada
> habría sido regalar esos secretos. De `SECRET_KEY` se deriva ahora su cifrado.

| Fase | Qué | Terminada cuando | Estado |
|---|---|---|---|
| **S.1** | Secretos fuera del código | `SECRET_KEY` no tiene valor por defecto: si falta, la app **no arranca**. El valor de producción se genera aparte y nunca se sube. | ✅ **hecha** (2026-10-12) |
| **S.2** | El seed no crea usuarios demo fuera de desarrollo | Con `ENTORNO=produccion` el arranque no crea ninguna cuenta de demo; con prueba de los dos casos. | ✅ **hecha** (2026-10-20). Verificado levantando la imagen de producción contra una base limpia: solo existe el admin de las variables, y `admin@atsdemo.com` / `Demo1234!` devuelve 401 |
| **S.3** | Validar los archivos que llegan | Tamaño máximo y tipo real comprobado (no solo la extensión); un archivo enorme o disfrazado se rechaza con 413/415. | ✅ **hecha**: la imagen del post el 2026-10-12 y el CV el 2026-10-14 (15 MB, comprobado antes de leerlo) |
| **S.4** | Límite de peticiones en el portal público | Postular y analizar CV tienen límite por IP; con prueba de que el límite se aplica. | ✅ **hecha** (2026-10-20). Por IP, leyendo `X-Forwarded-For`; 5 lecturas de CV cada 10 min, porque cada una cuesta dinero en la API de Claude |
| **S.5** | Datos personales: conservar y borrar | Se puede borrar por completo a un candidato que lo pida, y está escrito cuánto tiempo se guardan los datos. | pendiente |

**Por qué cada una (lo que hoy pasa de verdad):**

- **S.1** — `backend/app/core/config.py:10` trae `secret_key = "supersecretkey_ats_2026"`, y ese valor
  está publicado en GitHub. Con él, cualquiera puede **fabricar un token válido de super admin** sin
  contraseña. Es la más grave de todas.
- **S.2** — `app/main.py:18` llama a `run_seed` en **cada arranque**, sin mirar el entorno. En un
  servidor real crearía `admin@atsdemo.com` con la contraseña `Demo1234!`, que además está escrita en
  el `CLAUDE.md` público: una cuenta de administrador con contraseña conocida.
- **S.3** — `cv_parser_service.py:127` hace `await file.read()` **sin límite de tamaño**. Un archivo de
  varios GB tumba el contenedor; el servidor solo tiene 3,7 GB para todo.
- **S.4** — El portal público no tiene ningún límite: se puede llamar en bucle a analizar CV, que es la
  operación más cara del sistema.
- **S.5** — Se van a guardar cédulas, correos y teléfonos de personas reales. Hoy no hay forma de
  borrar a un candidato ni está definido cuánto se conservan sus datos.

# Etapa 3 — Lo que pierde información

Funciones que hoy **tiran datos del candidato**. Con producción real, cada día que pase así es
información perdida que no se recupera.

| Fase | Qué | Terminada cuando | Estado |
|---|---|---|---|
| **M2.1** | Guardar el CV de verdad | El archivo queda guardado y se puede descargar desde la ficha del candidato. Hoy `cv_documento_url` guarda el texto `pendiente-de-almacenamiento`: **el CV se lee, se analiza y se tira**. Desde el 2026-10-12 hay camino hecho: `almacenamiento_service` y el volumen `media_data` ya guardan la imagen del post. | pendiente |
| **M1.1** | Subir el documento de la vacante | El `.pdf`/`.docx` se guarda y se puede volver a descargar (hoy el campo del formulario no sube nada). Mismo camino que M2.1. | pendiente |
| **M1.6** | Publicar el post a la hora programada | Llegada la fecha de `post_programado_para`, el post sale **solo**. Hoy la fecha se guarda y no la ejecuta nadie: hay que pulsar el botón, y la pantalla lo advierte. Necesita un proceso aparte (APScheduler en el propio backend es lo más barato; Docker tiene 3,7 GB para todo). | pendiente (nueva, 2026-10-12) |
| **T.6** | Build de producción verificado | La imagen construida desde cero arranca y responde, no el contenedor de desarrollo con recarga en caliente. | ✅ **hecha** (2026-10-20). Nunca se había ejecutado: faltaba `@types/node` y no existía `package-lock.json`. Ahora las dos imágenes se construyen, arrancan y responden, verificado con un ensayo completo en local  |

# Etapa 4 — Lo que el sistema promete y no cumple

Nada de esto pierde datos, pero son funciones anunciadas en la interfaz que no hacen lo que dicen.
Con candidatos reales, la peor es la primera: un candidato descartado podría seguir avanzando.

| Fase | Qué | Terminada cuando | Estado |
|---|---|---|---|
| **M2.2** | Preguntas eliminatorias que de verdad descartan | Una respuesta que incumple una pregunta *knockout* descarta la postulación; con prueba de los dos casos (cumple / no cumple). Hoy las respuestas se guardan pero no filtran nada. | pendiente |
| **M7.1** | Guardas de ruta en el frontend | Entrar por URL a una sección sin permiso redirige (hoy solo se oculta el menú; el backend sí protege). | pendiente |
| **M7.2** | El menú y los botones, por permisos | El menú lateral se pinta desde `/users/yo/permisos` y no desde el rol, y los botones de cada módulo se ocultan según el permiso. **Hoy las casillas de permisos de los otros módulos no se notan en la interfaz.** | pendiente (nueva, 2026-10-16) |
| **M7.3** | Migrar los 33 endpoints a `require_permission` | Ningún endpoint decide por nombre de rol. Hasta entonces los tres roles del sistema no se pueden renombrar, porque el código los nombra. Se hace módulo a módulo, a medida que se cierran. | pendiente (nueva, 2026-10-16) |
| **M4.1** | Exportar de verdad | Descarga un CSV con los contactos filtrados (hoy el botón solo muestra un aviso). | pendiente |
| **M4.2** | Etiquetas | Se pueden etiquetar candidatos y filtrar por etiqueta (hoy el botón solo muestra un aviso). | pendiente |
| **M5.1** | Scorecard consolidado | El promedio por candidato se ve en la interfaz (`evaluation_service.promedio_puntaje` ya existe y nadie lo llama). | pendiente |
| **M3.3** | Puntuación de coincidencia | `match_score` se calcula de verdad y se explica cómo (hoy siempre queda vacío). | pendiente |

# Etapa 5 — Salir a producción

| Fase | Qué | Terminada cuando | Estado |
|---|---|---|---|
| **D.1** | Desplegar en un servidor | La aplicación responde por HTTPS en un dominio, con sus variables de entorno propias. | 🟡 **preparado** (2026-10-20): `render.yaml`, Dockerfiles de producción y `docs/DESPLIEGUE.md`. Falta que el dueño cree la cuenta y conecte el repositorio  |
| **D.2** | Copias de seguridad | Hay copia automática de la base y **se ha probado restaurar una** (una copia sin restaurar probada no es una copia). | pendiente |
| **D.3** | Registro y vigilancia | Los errores quedan registrados y se puede saber si el sistema está caído. | pendiente |
| **M3.1** | Auditoría de movimientos | Cada cambio de etapa guarda quién, cuándo y desde dónde. Con gente real decidiendo sobre candidatos reales, hace falta rastro. | pendiente |

# Etapa 6 — Completar funcionalidad

Ya con terreno firme, seguridad cerrada y el sistema desplegado. Dentro de esta etapa el orden es
flexible: se elige por lo que haga falta en ese momento.

| Fase | Qué | Módulo |
|---|---|---|
| **T.5** | E2E con Playwright (`/keybi-tests`): `@smoke` cubre login y postular, verde y bajo 3 minutos | Transversal |
| **M6.1** | Volumen de postulaciones por día, semana y mes | Dashboard |
| **M6.2** | Próximas entrevistas y actividades pendientes | Dashboard |
| **M6.3** | Tasa de conversión real LinkedIn vs WhatsApp | Dashboard |
| **M4.3** | Paginación del directorio | Contactos |
| **M4.4** | Búsqueda por título, habilidad y años de experiencia | Contactos |
| **M1.2** | Editar y cerrar vacantes sin que cambie el slug | Vacantes |
| **M1.3** | Definir las opciones de una pregunta de selección | Vacantes |
| **M1.4** | LinkedIn real con credenciales | Vacantes |
| **M1.5** | Devolver la gestión de preguntas filtro: se quitó de Cargos el 2026-10-02 y hoy **no hay forma de crearlas** desde la aplicación | Vacantes |
| **M2.5** | Traer los títulos verificados del candidato desde EcuadorAPI por cédula, en vez de fiarse del parser del CV. Necesita API key de pago y consentimiento del candidato | Portal |
| **M5.2** | Adjuntar documentos a una evaluación | Evaluaciones |
| **M5.3** | Confidencialidad por rol probada (403, no solo ocultar el botón) | Evaluaciones |
| **M2.3** | Medir el acierto del parser contra CVs reales y mejorarlo | Portal |
| **M2.4** | Formato `.doc`: soportarlo o probar el mensaje de error | Portal |
| **M7.2** | Registro de actividad y cambios de rol | Usuarios |
| **M7.3** | Recuperar contraseña, probado de punta a punta | Usuarios |

---

## Decisiones ya tomadas

- **2026-10-01 · Destino: producción real**, cimientos primero, los 7 módulos importan. De ahí salen
  las 6 etapas y su orden.
- **2026-10-02 · Educación formal con catálogos propios**, no con EcuadorAPI: esa API consulta los
  títulos de UNA persona por su cédula ("qué estudió y dónde"), no tiene catálogos de niveles ni
  áreas, cobra por consulta y puede pedir CAPTCHA. Su sitio real es el portal del candidato (M2.5).
- **2026-10-02 · Requerido y deseado son excluyentes** en las competencias de un cargo.

## Decisiones pendientes del dueño

- **¿El repo sigue público?** No es un problema en sí (el código abierto es legítimo), pero con
  producción real obliga a que la etapa 2 esté cerrada antes de desplegar. Si prefieres, se puede pasar
  a privado en cualquier momento.
- **¿Dónde se despliega?** ✅ Decidido el 2026-10-20: Render o Railway, como entorno de prueba para que otra persona siga el avance. Ver `docs/DESPLIEGUE.md`.
- **¿Dónde se guardan los CVs?** M2.1 cambia bastante según sea disco del servidor o almacenamiento
  de objetos tipo S3/MinIO.

## Deuda anotada, sin fase

- No hay capa `repositories/` separada: las consultas viven en los routers (decisión consciente, ver `CLAUDE.md`).
