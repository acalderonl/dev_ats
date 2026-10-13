# Bitácora — día a día

Lo más reciente arriba. Una entrada por día trabajado. Para no inventar lo que se hizo:
`git log --since=midnight --format="%h %s"` y las fechas de los archivos.

Cada entrada separa **lo verificado** de **lo que solo se escribió**. Un archivo creado no es
una funcionalidad que funcione.

---

## 2026-10-12 — Día 6 · Vacantes como publicación, S.1 cerrada y marca ANAI

> Sesión de tarde. Comparte fecha con el día 5: son **dos sesiones del mismo día**, no dos
> días. El contador de "días trabajados" cuenta sesiones, y se corrigió en `ESTADO.md`.

**Fases:** **S.1 CERRADA** (por fin), M1 ampliado al módulo de Vacantes, y la aplicación
pasa a llevar la marca de la institución.

**S.1 primero, y esta vez no por disciplina sino por necesidad:** este trabajo guarda el
secreto de LinkedIn y una contraseña de aplicación de Gmail en la base. Hacerlo con un
`SECRET_KEY` publicado en GitHub habría sido regalar esos secretos.

- `SECRET_KEY` ya no tiene valor por defecto: si falta, la aplicación **no arranca** y
  `docker compose` se niega a levantar. Además rechaza los valores de ejemplo publicados.
- De esa clave se deriva el cifrado (Fernet) de los secretos guardados. Contrapartida
  explícita: **al rotar la clave hay que volver a introducirlos**.
- El valor por defecto estaba en tres sitios (`config.py`, `docker-compose.yml`,
  `.env.example`). Los tres limpios; `.env` real generado y fuera de git.

**La vacante**
- **El título deja de escribirse**: se elige el cargo y el título se copia de él. Es una
  copia y no un `join` a propósito: de ahí sale el `slug`, que es la URL pública, y si
  siguiera al catálogo, renombrar un cargo rompería los enlaces ya repartidos.
- Tres conceptos que estaban mezclados en una columna ahora son tres: `estado`
  (borrador/abierta/cerrada), `post_estado` (borrador/programado/publicado/error) y
  `visibilidad` (pública/interna/mixta). Una vacante puede estar abierta con el post en
  borrador, o publicada y ya cerrada.
- Suma remuneración, jornada con entrada y salida, tipo de contrato (catálogo nuevo),
  campos personalizados, asunto, imagen, programación y destinatarios internos.
- **Primera subida real de archivos del proyecto** (migración 0006 + volumen `media_data`):
  se valida el tipo por los bytes y no por la extensión, el tamaño leyendo a trozos, y el
  nombre lo genera el servidor.

**LinkedIn: lo que se puede y lo que no** (investigado, no supuesto)
- El servicio anterior llamaba a `/v2/jobPostings`, que exige ser partner de Talent
  Solutions: **nunca habría funcionado** con credenciales normales.
- Reescrito a la única vía de autoservicio: productos *Sign In with LinkedIn (OIDC)* y
  *Share on LinkedIn*, scope `w_member_social` → publica en **el muro del reclutador**.
- Página de empresa y tablón de empleos siguen exigiendo aprobación de partner.
- El token dura ~60 días y **no hay refresh token** fuera del programa de partners: la
  pantalla avisa antes de que caduque y hay que reconectar.

**Verificado**
- **88 pruebas en verde** (eran 53). La creación de vacantes se centralizó en una fixture,
  como se hizo con los cargos: cuando cambió aquel contrato el arreglo fue un archivo en
  vez de cuatro.
- `SECRET_KEY` con los dos controles: acepta la clave nueva (health 200) y rechaza tanto el
  valor publicado como el vacío.
- Migración 0006: conservó la vacante existente y tradujo `activa` → `abierta`.
- En el navegador: jornada de 8 h con entrada 09:00 da salida 17:00, y al cambiar a 4 h
  recalcula a 13:00. La etiqueta repetida avisa junto a la fila y deja de avisar al
  corregirla.
- En PostgreSQL: la vacante guardó título copiado del cargo, 1250.50, horario y los dos
  campos adicionales con los acentos intactos.
- **El secreto guardado desde la pantalla está cifrado en la columna** (`gAAAAA...`) y el
  valor en claro aparece **0 veces** en la tabla. Las pruebas comprueban eso y no una ida
  y vuelta, que pasaría igual con el secreto en texto plano.
- Fuga cero y limpieza: la base quedó en 5 cargos, 1 vacante y 0 filas de configuración.

**Correo: de solo Gmail a cualquier servidor**
- Gmail era el único camino y no sirve para el correo institucional, que suele tener
  servidor propio. Ahora se **elige el tipo de conexión**: Gmail/Workspace (servidor y
  puerto fijos) o servidor propio (servidor, puerto, cifrado, remitente, usuario y clave).
- Gmail es, por dentro, el caso particular del segundo con los valores ya puestos. Se
  mantienen separados en pantalla porque lo que hay que pedirle a una persona es muy
  distinto: una contraseña de aplicación frente a cinco datos de sistemas.
- El **usuario se pregunta aparte del remitente**: hay servidores donde se entra con
  `dominio\usuario` o con una cuenta de servicio.
- Añadido **"Probar conexión"**: se conecta y autentica sin enviar nada. Sin eso, la única
  forma de descubrir que la configuración estaba mal era mandar una vacante real a una
  lista de correos de verdad.

**La aplicación pasa a ser de la ANAI**
- Escudo, nombre y colores de la Academia Naval Almirante Illingworth en lugar de "Sistema
  ATS", también en el acceso y en las dos pantallas que ve el candidato.
- **Los colores no se estimaron de una captura**: se leyeron los valores calculados del
  propio anai.edu.ec. Institucional `#0064b4`, franjas `#003462`, acento `#1ea7fd`, claros
  `#aad6ff` y `#ebf5ff`. El `#20395f` del escudo sale del propio SVG.
- El institucional se colocó en `brand-600` a propósito: la interfaz ya usaba `brand-600`
  para botones y acentos, así que **toda la aplicación cambió de color sin tocar clase por
  clase**.

**Corregido de esta misma sesión**
- `Card` no trae padding propio —lo pone quien lo usa— y en las dos vistas nuevas se me
  pasó: el contenido iba pegado al borde. Arreglado en Vacantes y Configuración, y
  revisado el resto (el Dashboard lo usaba bien, con `CardHeader`/`CardBody`).
- La tarjeta de vacante se reordenó: condiciones como etiquetas con icono, punto de color
  para el estado del post y los botones en una barra inferior propia.

**Verificado (segunda mitad de la sesión)**
- **97 pruebas en verde** (de 88). Las nuevas cubren que la contraseña SMTP tampoco se
  guarda en claro ni se devuelve, el puerto fuera de rango, y el tipo y cifrado inválidos.
- Que **cambiar de tipo no borra las credenciales del otro**: probar el servidor propio y
  volver a Gmail no puede costar reconfigurar Gmail.
- Con los dos controles: puerto vacío + elegir SSL propone 465; con `2525` escrito a mano
  **no lo pisa**. Probar contra un servidor inexistente informa del fallo sin romperse.
- La marca, **midiendo y no mirando**: el botón principal calcula `#0064b4`, el título
  `#20395f` y el fondo del acceso el degradado con los tres azules; el escudo carga en las
  cuatro pantallas.

**Errores propios que conviene recordar**
- Tres veces seguidas rompí archivos con sustituciones multilínea de `perl`: corrompió
  `types/index.ts`, `schemas/vacante.py` (dejó un campo obligatorio y tumbó 11 pruebas) y
  la cabecera de `ESTADO.md`. Las tres se vieron enseguida porque `tsc` y `pytest` corren
  después de cada cambio. **Para ediciones estructurales, edición exacta, no regex.**
- Pulsé "Guardar" y "Probar conexión" a la vez y la prueba llegó antes del guardado: la
  respuesta decía "Gmail" cuando ya había elegido SMTP. No era un fallo del producto sino
  de cómo lo medí; se repitió la prueba en orden.

**Pendiente / avisos**
- 🔴 **La fecha programada se guarda pero nada publica solo a esa hora.** Falta el proceso
  que lo ejecute; hoy hay que pulsar el botón. Está dicho en la propia pantalla.
- 🔴 El envío interno necesita que configures el correo; sin eso el botón explica qué falta.
- LinkedIn queda en **modo simulado** hasta que crees la app y pegues las credenciales. El
  resultado dice "simulado" en vez de fingir que salió a internet.
- Rotar `SECRET_KEY` obliga a reintroducir los secretos guardados. Es la contrapartida de
  no tener una segunda clave que administrar.
- Los correos de demo siguen siendo `@atsdemo.com`: están en las pruebas y en `CLAUDE.md`,
  y no se ven en la interfaz.

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

**También hoy — el modal deja de perder trabajo**
- **La cabecera del modal ya no se va con el scroll.** El panel pasa a ser una columna: la
  cabecera (título y X) queda fuera del área que hace scroll, en vez de desplazarse con el
  contenido. En un formulario de siete secciones la salida estaba desapareciendo de la vista.
- **Cerrar el formulario de cargo pregunta antes**, tanto con la X como haciendo clic fuera.
  Antes, un clic fuera por accidente borraba las siete secciones sin aviso.
- La pregunta es **opcional por diseño** (prop `confirmarCierre`): un modal que ya es él mismo
  una confirmación —desactivar un cargo, gestionar un catálogo— no debe pedir confirmación para
  cerrarse. Solo la activa el formulario de cargo.

- **El modal se monta en `document.body`**, con un portal, en vez de donde se escribe. Vivía dentro
  de `<main>`, un contenedor con scroll: bastaba que un ancestro usara `transform` o `filter` para
  que dejara de cubrir la pantalla y quedara recortado dentro de la columna. Colgándolo del body
  eso ya no puede pasar.
- El fondo oscuro se quitó y se volvió a poner a petición del dueño: con tanto texto detrás, el
  formulario no se distinguía. Se queda en `bg-slate-900/40`.

**Verificado (en el navegador, con los dos controles)**
- Con el cuerpo scrolleado hasta la sección 7, la cabecera "Nuevo Cargo" y la X seguían en su sitio.
- El modal cuelga de `<body>` (`parentElement === document.body`, fuera de `<main>`), y
  `elementFromPoint` sobre el menú lateral, la barra superior, el contenido y la esquina inferior
  devuelve el modal: **nada de la aplicación queda por encima** en ningún punto de la pantalla.
- Con el gestor de catálogo abierto encima, las dos capas cuelgan del body y la de arriba es la
  correcta; cerrarla **no se cuela** al fondo del modal de abajo (que habría abierto la pregunta).
- Al cerrar no queda ningún nodo suelto en el body.
- **Control positivo**: la X abre la pregunta y el modal no se cierra; el clic fuera, igual;
  "Cancelar" vuelve al formulario intacto; "Sí, cerrar" cierra de verdad y no deja la pregunta
  en pie para la próxima apertura.
- **Control negativo**: la confirmación de desactivar un cargo sigue cerrándose al primer clic
  fuera, sin preguntar. El cambio no se desbordó a los demás modales.
- 5 cargos activos de 5 antes y después de la prueba: abrir y cerrar modales no tocó datos.
- 53 pruebas en verde y `tsc --noEmit` limpio (el cambio es solo de frontend).

**Pendiente / avisos**
- 🔴 La etapa 2 (seguridad) sigue entera sin empezar. Ya van dos sesiones seguidas en M1.
- El bloqueo por parecido usa un umbral de 0,55: dos competencias legítimamente distintas pero
  parecidas no se pueden crear. Si molesta, hay que subir el umbral o añadir una confirmación.
- La pregunta de cierre salta **siempre**, aunque no se haya escrito nada. Si estorba, el paso
  siguiente es comparar el formulario con su estado inicial y preguntar solo si hay cambios.
- Los modales de Vacantes y Evaluaciones también son formularios y **siguen sin preguntar**:
  basta añadirles la misma prop cuando se quiera.

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
