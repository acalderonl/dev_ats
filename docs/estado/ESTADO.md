# Estado del proyecto — dónde estamos AHORA

> Última actualización: **2026-10-29** · Sesiones: **14** (en 11 días) · Pruebas: **201 en verde**
> Este archivo se lee al empezar cada sesión. Si algo aquí ya no es cierto, se corrige antes de seguir.

## En una línea

**La etapa 2 está cerrada**: las 4 puertas de seguridad confirmadas, cerradas y verificadas
levantando la imagen de producción. Los módulos de **Cargos (M1)**, **Vacantes** y **Usuarios y
roles (M7)** están rehechos, y la aplicación lleva la **marca de la ANAI**. Una vacante ya se
puede llevar a LinkedIn **sin aplicación aprobada**. Falta lo mismo que la semana pasada: que el
dueño cree la máquina en Google Cloud.

## Fase activa

| | |
|---|---|
| **Fase** | `D.1 — Desplegar el entorno de prueba` |
| **Etapa** | 5 de 6 — Salir a producción |
| **Por qué esta** | La etapa 2 está cerrada: S.1, S.2, S.3 y S.4 hechas. Solo queda S.5 (borrar datos de un candidato), que no aplica mientras el entorno no tenga personas reales. Todo lo técnico del despliegue está escrito y ensayado. |
| **Terminada cuando** | La aplicación responde en una URL pública y cada push la actualiza. |
| **Te toca a ti** | Crear la máquina en **Google Cloud** y apuntarle un dominio. El paso a paso está en `docs/DESPLIEGUE.md`. (Render quedó como alternativa al final de esa guía.) |

> ⚠️ **Si el entorno no levanta**: desde el día 6 hace falta un `.env` con `SECRET_KEY`. Copia
> `.env.example` a `.env` y genera una con
> `python -c "import secrets; print(secrets.token_urlsafe(48))"`.

## El camino (6 etapas, 37 fases)

Orden decidido el 2026-10-01 por tres criterios del dueño: **destino producción real**,
**cimientos primero** y **los 7 módulos importan**. El detalle está en `FASES.md`.

| | Etapa | Fases | Por qué va aquí |
|---|---|---|---|
| **1** | Terreno firme | 4 | Sin pruebas que corran no se sabe si un cambio rompió algo |
| **2** | Bloqueantes de seguridad | 5 | 4 puertas abiertas verificadas en el código; el repo es público |
| **3** | Lo que pierde información | 3 | Hoy el CV del candidato se analiza y **se tira** |
| **4** | Lo prometido que no cumple | 6 | Botones y reglas anunciadas que no hacen lo que dicen |
| **5** | Salir a producción | 4 | Despliegue, copias de seguridad, rastro de decisiones |
| **6** | Completar funcionalidad | 15 | El resto, ya sobre terreno firme |

## Los 7 módulos

Leyenda: 🟢 base funcionando · 🟡 base funcionando con huecos conocidos · ⚪ no empezado

| Módulo | Estado | Verificado | Siguiente fase | Etapa |
|---|---|---|---|---|
| **M1** Cargos, vacantes e integraciones | 🟢 | Cargos y vacantes: crear, editar y estados, **con pruebas**. Compartir en LinkedIn **sin OAuth**: medido que el rastreador no ve la SPA y que `/compartir` sí le da las etiquetas. Conectar pegando un token del portal. Publicación por API con la tarjeta completa (título, descripción y miniatura) y gestión del post (reescribir/borrar), **con pruebas**; ⚠️ nada probado todavía contra LinkedIn de verdad | M1.6 publicar a la hora programada | 4 |
| **M2** Portal público y perfil del candidato | 🟢 | Formulario de 3 pasos con el esquema entero: comprobado en el navegador que se envía y que cae en las cuatro tablas. Foto y CV guardados en carpeta privada, **con pruebas** de que `/media` no los sirve | M2.2 el robot de ETL | 3 |
| **M3** Pipeline de reclutamiento | 🟡 | Reglas de transición, **con pruebas** | M3.3 puntuación de coincidencia | 4 |
| **M4** Directorio de contactos | 🟡 | Búsqueda, **con pruebas** | M4.1 exportar de verdad | 4 |
| **M5** Evaluaciones | 🟡 | ❌ nada | M5.1 scorecard consolidado | 4 |
| **M6** Dashboard | 🟡 | Carga y dibuja (a mano) | M6.1 volumen en el tiempo | 6 |
| **M7** Usuarios y roles | 🟢 | CRUD de usuarios y roles, y permisos por módulo con ajuste por usuario, **con pruebas**. Comprobado en la base que una excepción guarda una fila, no una copia del rol | M7.2 el menú por permisos, no por rol | 4 |
| **S** Seguridad | 🟢 | **Los 4 fallos confirmados, cerrados.** S.2 verificado levantando la imagen de producción contra una base limpia: la cuenta publicada devuelve 401 | S.5 borrar los datos de un candidato | 6 |
| **T** Transversal | 🟢 | Suite corriendo, aislada y sin fuga | T.2 validar por mutación | 1 |

### Qué tiene hoy el módulo de Cargos (M1)

Un cargo ya no es un nombre y una descripción: es un **descriptivo de puesto** con siete bloques
—identificación, misión, actividades, educación formal, formación, habilidades blandas y
experiencia—. Los valores repetibles viven en catálogos con su propio CRUD (el engranaje junto a
cada selector), y las competencias se comparten entre cargos con detección de parecidos para que
no se dupliquen escritas de formas distintas.

La educación formal admite **hasta dos** niveles, títulos y áreas; cada nivel con su propio estado
(completa / en curso). La experiencia suma un checklist de tres exigencias. Al escribir una
competencia parecida a una existente, **no se puede crear**: hay que elegir la que ya está.

El modal mantiene la cabecera fija al hacer scroll y **pregunta antes de cerrarse** —con la X o
con un clic fuera—, para que un descuido no borre las siete secciones. La pregunta es opcional
en el componente: los modales que ya son una confirmación cierran al primer clic.

La columna **Verificado** solo dice lo que se comprobó de verdad. "A mano" significa que una persona lo
usó en el navegador: no es una prueba automática y no protege contra regresiones.

### Qué tiene hoy el módulo de Vacantes

Una vacante es **un cargo puesto en circulación**: se elige el cargo y el título sale de él. Lleva
remuneración, horario (jornada + entrada, con la salida calculada), tipo de contrato y los campos
adicionales que haga falta inventar.

Tres cosas que se confunden y aquí son distintas: **estado** (borrador/abierta/cerrada), **estado del
post** (borrador/programado/publicado/error) y **visibilidad** (pública/interna/mixta). Una vacante
interna no aparece en el portal público aunque esté abierta y alguien tenga el enlace.

La pantalla de **Configuración** guarda las credenciales **cifradas** y no las devuelve nunca:
muestra si están puestas y sus últimos cuatro caracteres. El correo admite **Gmail/Workspace o
cualquier servidor SMTP institucional**, con un botón que prueba la conexión sin enviar nada.

### Usuarios, roles y permisos

Los usuarios se crean, editan y desactivan —**nunca se borran**: son los autores de las
vacantes que publicaron y las evaluaciones que pusieron—. Los roles se crean y se editan,
salvo los tres del sistema, cuyo nombre el código todavía referencia.

Los permisos son **27, sacados del menú lateral**: uno por cada acción real de cada pantalla.
Se resuelven en dos niveles: el rol da la plantilla y cada usuario admite excepciones en
ambos sentidos. Se guarda solo la diferencia, así que cambiar la plantilla de un rol la
heredan sus usuarios en vez de quedarse con una copia congelada.

⚠️ `require_permission` convive con `require_roles`: los 33 endpoints antiguos siguen
protegidos por rol. **Hasta migrarlos, lo que se marca en los otros módulos no gobierna el
backend**, y el menú lateral sigue ocultándose por rol.

### La marca

La aplicación es de la **Academia Naval Almirante Illingworth**: escudo, nombre y colores reales
del sitio de la institución (`#0064b4` institucional, `#003462` franjas, `#20395f` escudo). El
azul institucional vive en `brand-600` de Tailwind, que es lo que ya usaba toda la interfaz.

### Desplegar

Todo lo técnico está hecho y ensayado en local: imágenes de producción, `render.yaml`,
el seed que no crea cuentas de demo, y límite de peticiones en el portal público. La guía
paso a paso está en **`docs/DESPLIEGUE.md`**.

El frontend hace de **proxy** hacia el backend, así que la API no se expone a internet y
no hay CORS que configurar. Cada push a la rama desplegada actualiza el entorno solo, y
las migraciones se aplican al arrancar.

⚠️ Es un **entorno de prueba**, no producción real: sin copias de seguridad y sin forma de
borrar a un candidato que lo pida. Mientras solo tenga datos inventados, está bien; el día
que entren personas reales, eso cambia.

## Lo más urgente, en una frase

Ya no hay nada urgente en el código: las cuatro puertas de seguridad están cerradas. Lo que queda
es **tuyo**: crear la cuenta en Render y conectar el repositorio (`docs/DESPLIEGUE.md`).

## Lo que necesita tu intervención

| Qué | Por qué está parado |
| **App de LinkedIn** | Ya creada (*ATS FICHAR*). Para publicar automáticamente basta **pegar un token** del *Token generator* en Configuración; caduca a los ~60 días. Client ID, Secret y Redirect URI solo hacen falta para el camino con OAuth, que no se renueva a mano pero exige la Redirect URI registrada. |
| **App de LinkedIn** | Hay que crearla en developer.linkedin.com y pegar Client ID, Secret y Redirect URI en Configuración. Hasta entonces, publicar queda en **modo simulado** y lo dice. |
| **Contraseña de aplicación de Gmail** | Con verificación en dos pasos activada, generarla en la cuenta de Google. Sin eso no hay envío interno. |
| **Publicar a la hora programada** | La fecha se guarda, pero **nada la ejecuta todavía**: hoy hay que pulsar el botón. Necesita un proceso aparte (fase M1.6). |

## Entorno

- **Las pruebas no tocan la base de desarrollo**: corren contra `ats_test_db`, que se recrea desde
  las migraciones en cada ejecución. Comprobado con control positivo (contar filas antes y después).
- Código real en `C:\Users\abdon\OneDrive\Documentos\DEV\dev_ats` (OneDrive, **no** en `Documents`).
- Repo: https://github.com/acalderonl/dev_ats (**público**, rama `main`).
- En el host hay Git y GitHub CLI; **no** hay Node ni Python: todo se compila y prueba dentro de los contenedores.
- Docker tiene 3,7 GB para todos los contenedores: levantar y medir antes de añadir servicios.

## Cómo se usa este sistema

1. **Al empezar** una sesión: leer este archivo. Dice la fase activa y qué está sin verificar.
2. **Durante**: si cambia el estado de un módulo o se termina una fase, se actualiza aquí y en `FASES.md`.
3. **Al terminar**: anotar el día en `BITACORA.md`. Para no inventar lo que se hizo:
   `git log --since=midnight --format="%h %s"`

Las reglas de qué significa "terminado" están en `FASES.md`. El arranque concreto de la próxima
sesión está en `PROXIMA_SESION.md`.
