# Bitácora — día a día

Lo más reciente arriba. Una entrada por día trabajado. Para no inventar lo que se hizo:
`git log --since=midnight --format="%h %s"` y las fechas de los archivos.

Cada entrada separa **lo verificado** de **lo que solo se escribió**. Un archivo creado no es
una funcionalidad que funcione.

---

## 2026-10-26 — Sesión 10 · Publicar en LinkedIn sin OAuth

**Fase:** M1 — integraciones. No cierra ninguna fase del mapa: es el camino alternativo al
que ya existía (OAuth), pedido por el dueño porque no quiere depender de una aplicación
aprobada por LinkedIn.

**El encargo, literal:** «al conectarlo pueda ser capaz de disparar abrir el enlace del
linkedin conectado para presionar publicar desde la plataforma solo trasladamos la
información de mi sistema a linkedin».

**Lo primero fue medir, no suponer.** Pedí el portal con el agente del rastreador:

```
curl -A "LinkedInBot/1.0" http://localhost:3000/postular/<slug>
```

Devuelve `<title>ANAI | Selección de personal</title>`, un `<div id="root"></div>` vacío y
**cero** etiquetas Open Graph. Era de esperar —la aplicación es una SPA y el rastreador de
LinkedIn no ejecuta JavaScript—, pero sin esa comprobación habría sido una corazonada. Con
ese enlace, LinkedIn habría dibujado una tarjeta sin puesto, sin descripción y sin imagen.

**Lo construido**
- `GET /compartir/{slug}`: una página que **genera el servidor**, con las etiquetas Open
  Graph rellenas desde la base. Va montada fuera de `/api/v1` porque la URL se reparte a
  personas. Quien la abra no se queda ahí: `meta refresh` + `location.replace` lo llevan al
  formulario de verdad, así que no es una página paralela que haya que mantener.
- `POST /vacantes/{id}/compartir-linkedin`: arma el texto, devuelve el enlace a compartir y
  la URL del compositor (`share-offsite`).
- En la tarjeta de la vacante, el botón copia el texto al portapapeles y abre el compositor.
  La pestaña se abre **antes** del `await`: abrirla después la mata el bloqueador de
  ventanas emergentes.

**Tres decisiones que no son obvias**
- **`compartido` no es `publicado`.** Es el estado nuevo del post. El sistema entrega el
  contenido, pero quien pulsa Publicar es la persona y eso no se puede comprobar desde
  aquí. Marcarlo como publicado sería afirmar algo que no se sabe; la pantalla lo dice.
- **Sin imagen propia no se anuncia ninguna.** El escudo de la ANAI es un SVG y LinkedIn no
  los dibuja en las tarjetas: saldría un hueco. Sin `og:image` muestra una tarjeta de solo
  texto, que se ve bien.
- **No se montó SSR.** Cambiar la arquitectura entera del frontend por cuatro etiquetas no
  se sostiene cuando una ruta del backend lo resuelve.

**Verificado de punta a punta, no solo con pruebas**
- 164 pruebas en verde (eran 152). Las 12 nuevas cubren las etiquetas, la redirección, el
  escapado de comillas en el asunto, y que un borrador, una vacante interna y una vencida
  devuelvan 404 —también al rastreador: interna significa interna.
- En el navegador, con la aplicación levantada: el botón copia el texto, el navegador
  registra el intento de abrir `www.linkedin.com`, y aparece el aviso «Termina de publicar
  en LinkedIn» con el texto y el recordatorio de que queda como enviado, no publicado.
- En PostgreSQL, `post_estado` pasó a `compartido`.
- `curl` con el agente de LinkedIn contra `/compartir/<slug>` devuelve el título, la
  descripción con contrato, sueldo y horario, y el enlace canónico al formulario.
- `black`, `flake8` y `tsc --noEmit` limpios.

**Un hueco que se vio al verificar, y se tapó**
En producción nginx reenvía `/compartir/` al backend, pero **en desarrollo Vite no**: el
enlace que se reparte habría devuelto el `index.html` vacío de la SPA justo donde se quiere
probar el flujo. Añadido el proxy en `vite.config.ts` (`VITE_PROXY_TARGET`) y comprobado que
el puerto 3000 ya devuelve las etiquetas.

**La pantalla de Configuración engañaba, y eso era el verdadero fallo**

El dueño dijo «la conexión sigue sin funcionar». Mirada la base: la tabla `configuracion`
está **vacía**, así que no es que falle, es que no hay nada que conectar. Pero la pantalla
mostraba «Sin conectar» y un botón apagado, que se lee como una aplicación rota.

La tarjeta de LinkedIn ahora dice lo que pasa: que **conectar es opcional**, que el botón de
la tarjeta de la vacante no necesita nada, y que esto otro —publicar solo— exige una
aplicación propia en LinkedIn porque no hay otra vía. El campo Redirect URI ofrece la URL
exacta de este sitio con un clic: tiene que coincidir carácter por carácter con la
registrada en LinkedIn, y es donde se rompen estas conexiones.

No se tocó el flujo OAuth: está entero y sin estrenar, a la espera de esa aplicación.

**Pendiente / avisos**
- La guía de despliegue (`docs/DESPLIEGUE.md`) es la de **Google Cloud** desde el 20 de
  octubre; la entrada de la sesión 9 todavía habla de Render, que quedó como alternativa al
  final del documento. El dueño aún no ha creado la máquina.
- El camino con OAuth sigue existiendo y sin estrenar: necesita la aplicación de LinkedIn
  del dueño. Este camino no la necesita.
- Para que LinkedIn pueda leer la tarjeta, `/compartir/<slug>` tiene que ser **alcanzable
  desde internet**. Mientras todo esté en `localhost`, la tarjeta saldrá vacía por mucho que
  la página sea correcta.

---


## 2026-10-20 — Sesión 9 · Preparar el despliegue: etapa 2 cerrada

**Fases:** **S.2, S.3 y S.4 cerradas** — con S.1, la etapa 2 entera. **T.6** hecha. **D.1**
preparada, a falta de que el dueño cree la cuenta.

**El encargo:** un entorno accesible por URL para que otra persona siga el avance. No es
producción real, va a tener solo datos inventados, y se actualizará constantemente.

**Lo que había, mirado antes de tocar nada**
- El seed creaba `admin@atsdemo.com` / `Demo1234!` **en cada arranque**. Esa contraseña está
  en este repositorio público: con una URL en internet, cualquiera entraba como super admin.
- El frontend corría `npm run dev` —el servidor de Vite— y el backend con `--reload`.
- `/leer-cv` no tenía límite **y llama a la API de Claude**: en internet es una factura
  abierta a quien escriba un bucle. Eso no estaba en el mapa de fases.

**S.2 — el seed**
- `ENTORNO` nuevo. En producción no se crean ni cuentas ni cargos de demo; sí los roles y
  los catálogos de educación, que no son "ejemplos" sino parte del sistema.
- El primer administrador sale de `ADMIN_INICIAL_EMAIL`/`PASSWORD`, y **solo si la base no
  tiene ningún usuario**. Sin esas variables no se crea nadie y se dice en el log: un sistema
  sin administrador es un problema visible; uno con un administrador adivinable, no.
- De paso se corrige lo del día 14: el seed ya no comprueba correo por correo, así que
  **no recrea una cuenta que alguien renombró**.

**S.4 — límite de peticiones**
- Por IP, leyendo `X-Forwarded-For` (sin eso, detrás de un proxy todas las peticiones
  parecen venir del mismo sitio). 5 lecturas de CV cada 10 minutos, 10 postulaciones, 60
  consultas por minuto.
- En memoria del proceso a propósito, con la contrapartida asumida y escrita: se olvida al
  reiniciar y no sirve con varias réplicas.

**Imágenes de producción**
- Backend en dos etapas, sin el compilador en la imagen final y con usuario sin
  privilegios: de **942 MB a 480**.
- Frontend compilado con Vite y servido por nginx, **haciendo de proxy** hacia el backend.
  Así la API no se expone a internet, no hay CORS, y la imagen no necesita saber en qué
  dominio vivirá: Vite incrusta las variables al compilar, no al arrancar.

**Verificado con un ensayo completo en local** — las dos imágenes de producción contra una
base vacía, con `ENTORNO=produccion`:
- En la base solo existe el admin de las variables, y **cero** cargos de demo.
- `admin@atsdemo.com` / `Demo1234!` devuelve **401**. Es la prueba de que S.2 está cerrada.
- A través del proxy: la página carga, `/cargos` devuelve 200 (no el 404 de nginx), el
  login del admin inicial da 200, y el límite corta a la sexta lectura de CV
  (`400 400 400 400 400 429 429`), lo que confirma que la IP real llega al backend.
- 152 pruebas en verde (eran 137). Las 15 nuevas cubren el seed en los dos entornos, el
  CORS, y el límite con su cabecera `Retry-After`.

**Dos cosas que aparecieron al construir, y que nadie había visto**
- **No existía `package-lock.json`.** Cada build resolvía versiones distintas: dos
  despliegues del mismo commit podían no ser iguales. Generado y versionado.
- **El build de producción nunca se había ejecutado** (fase T.6). Fallaba por `@types/node`
  ausente: `vite.config.ts` importa `node:url` y `npm run dev` no pasa por `tsc`.

**Un error propio**
- Escribí el `render.yaml` dando por hechas dos cosas de Render que no había comprobado: que
  las variables llegan como argumentos de construcción, y que `property: host` trae el
  esquema. En vez de adivinar, cambié el diseño a que nginx haga de proxy, que elimina las
  dos preguntas y además quita el CORS. Ese camino sí lo pude ensayar entero en local.

**Pendiente / avisos**
- 🔴 **Sin copias de seguridad y sin poder borrar a un candidato** (S.5). Acordado, porque
  solo habrá datos inventados. El día que entren personas reales, eso cambia.
- El plan gratuito de Render **apaga los servicios** tras un rato sin uso y **su base
  caduca a los 90 días**. Está escrito en la guía; si molesta, Railway no se apaga.
- Si Render regenera `SECRET_KEY`, hay que volver a introducir las credenciales de
  Configuración: de ella se deriva su cifrado.

---

## 2026-10-16 — Sesión 8 · Usuarios, roles y permisos; pestañas en Cargos

**Fases:** M7 (usuarios y roles) muy ampliado. **S.2 sigue sin empezar**, y hoy dejó de ser
teórica (ver los avisos).

**Usuarios y roles: de media pantalla a módulo completo**
- Antes solo se podía listar usuarios, cambiarles el rol y activarlos. Ahora se **crean,
  editan, se les restablece la contraseña** y se les asignan permisos. De roles no había
  nada: eran tres nombres sembrados en `seed.py`.
- **Eliminar es desactivar.** Quien publicó una vacante o evaluó a un candidato es el autor
  de esos registros; borrarlo abriría huecos en el historial de un proceso de selección que
  luego hay que poder reconstruir. El aviso lo explica, que es la pregunta que se hace
  cualquiera al no encontrar el botón.
- Tres accidentes que el código impide, todos la misma variante de quedarse fuera del propio
  sistema: desactivarse a uno mismo, quitarse el propio super admin, y dejar la aplicación
  **sin ningún super admin activo**.

**Permisos: del código a la base**
- Estaban escritos a mano en cada endpoint (`require_roles("...")` × 33), así que no se
  podían administrar. Ahora son **27 entradas sacadas del menú lateral**: un permiso por
  cada acción real de cada pantalla. No se inventaron permisos para cosas que la aplicación
  todavía no hace.
- Dos niveles, como pidió el dueño: **el rol da la plantilla y cada usuario admite
  excepciones** en ambos sentidos. Sin el nivel de usuario no se podría recortar un permiso a
  una persona sin sacarla de su rol.
- `require_permission` **convive** con `require_roles`: ninguno de los 33 endpoints queda sin
  protección mientras se migran.
- Los tres roles iniciales quedan marcados `es_sistema` y protegidos contra renombrado y
  borrado: el código todavía los nombra, y renombrar `reclutador` dejaría 21 endpoints sin
  dejar pasar a nadie **y sin error visible**.

**Cargos**
- Las secciones 5 y 6 ganan **botones por clasificación** que despliegan lo que ya piden los
  cargos de esa misma clasificación. Dentro de cada grupo, primero las más usadas; la
  clasificación del cargo en edición va primera. Los grupos vacíos no se devuelven.
- Activos e inactivos **separados en pestañas**, igual que en Usuarios.
- El panel de categorías se cierra solo 2 s después de salir el cursor; si vuelve, se cancela.

**Verificado**
- **137 pruebas en verde** (eran 112).
- Contra PostgreSQL: el rol creado desde la pantalla guardó los 4 permisos marcados con el
  nombre normalizado a identificador; quitarle un permiso a un reclutador guardó **una sola
  fila** de excepción, no diecinueve, y sus efectivos pasaron de 19 a 18 con el resto intacto.
- En Cargos, ida y vuelta completa sobre un cargo sin vacantes: desactivar movió los
  contadores de 3/2 a 2/3 y reactivar los devolvió. Los cinco cargos quedaron como estaban.
- El cierre automático, con los dos controles: sigue abierto a 1,2 s y cerrado a 2,6 s; y si
  el cursor vuelve al segundo, sigue abierto 2,5 s después.
- Datos de prueba creados y borrados en cada caso.

**Un fallo encontrado por las pruebas**
- La migración marca `es_sistema` en los roles **que ya existen**, pero en una instalación
  nueva los crea el seed después, con el valor por defecto en falso. **Una instalación desde
  cero habría tenido los tres roles base desprotegidos.** Corregido en `seed.py`.

**Errores propios que conviene recordar**
- Dos mediciones malas seguidas al probar el cierre automático: un `mouseleave` sintético no
  dispara el handler de React, y después apunté el ratón a y=638 cuando el contenedor estaba
  en y=497..527 —el frame de la captura va a 0,625 del viewport—, así que nunca llegué a
  entrar. Las dos veces "no cerraba" porque nunca le dije que saliera: **fallaba la prueba,
  no el código.**
- Volví a romper archivos con sustituciones multilínea de `perl` (`schemas/configuracion.py`,
  por el `|` de los tipos `str | None`). Es la tercera sesión seguida. **Para ediciones
  estructurales, edición exacta.**

**Pendiente / avisos**
- 🔴 **S.2 dejó de ser teórica.** El dueño renombró `admin@atsdemo.com` y el seed **volvió a
  crearlo** en el siguiente arranque, con `Demo1234!`, que está publicada en el repo. Ahora
  hay 5 usuarios, dos de ellos cuentas de demo recreadas.
- 🔴 **El menú lateral todavía se oculta por rol, no por permisos.** Hasta conectarlo a
  `/users/yo/permisos`, lo que se marca en los otros módulos no se nota en la interfaz.
- La barra superior guarda el nombre de quien entró y no se refresca al editarse a uno mismo.
- Hay dos cargos llamados "Analista de Reclutamiento" (uno activo, otro inactivo). No es un
  fallo —el nombre sale de un catálogo— pero confunde en las pestañas.

---

## 2026-10-14 — Sesión 7 · LinkedIn conectable, marca ANAI y perfil del postulante

> Anotada el 16 de octubre: la sesión se cerró sin documentar. Se reconstruye desde
> `git log` y el código, no de memoria.

**Hecho**
- **El flujo de OAuth de LinkedIn estaba a medias** y apareció al ir a explicar cómo conectar
  la app: `canjear_codigo()` existía pero no lo llamaba nadie, no había página de retorno, y
  el `state` se generaba sin comprobarse. Se llegaba a la pantalla de permisos y de ahí a un
  404. Cerrado: página de retorno en el frontend, endpoint que canjea el código y guarda el
  token cifrado, y `state` firmado (JWT de 10 minutos) en vez de guardado en una tabla.
- **Menú lateral con los colores de la institución** (`#003462`), con el escudo pasado a
  blanco por filtro: es monocromo y sobre azul oscuro habría desaparecido.
- **Perfil completo del postulante**: de 12 campos a ~40, con educación, idiomas y experiencia
  en tablas propias. La lectura del CV pasa de expresiones regulares a la **API de Claude**,
  mandando el PDF tal cual —no el texto aplanado— para que el modelo vea la página.

**Verificado**
- 112 pruebas en verde (eran 102). El `state` de otra persona se rechaza, el inventado y el
  caducado también, y el propio sí pasa la comprobación.
- Contraste del menú medido: 12,6:1 en el título y 10,2:1 en los enlaces.

**Dos fallos encontrados por las pruebas**
- **El consentimiento de privacidad no se validaba**: con `acepta_privacidad: bool = False`,
  Pydantic no valida los valores por defecto, así que el validador no llegaba a correr y una
  postulación sin aceptar nada entraba igual.
- Un `.docx` o PDF corrupto daba 500 en vez de decir que el archivo está dañado.

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
