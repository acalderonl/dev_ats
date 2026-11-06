# Arranque de la próxima sesión

> Escrito al cerrar el **2026-10-20** (sesión 9). Si al leerlo ya no cuadra con el código, manda el
> código: se corrige este archivo antes de seguir.

## 0. Antes de nada: hace falta un `.env`

Desde esta sesión **el entorno no levanta sin `SECRET_KEY`**, y es a propósito: ese valor firma los
JWT y antes venía con un valor por defecto publicado en GitHub.

Ya existe un `.env` generado en tu equipo (está en `.gitignore`, no se sube). Si lo pierdes o
trabajas en otra máquina:

```bash
cp .env.example .env
```

y pon dentro una clave propia:

```bash
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

⚠️ Cambiar esa clave **invalida las sesiones abiertas** (habrá que volver a entrar) y **obliga a
reintroducir los secretos guardados** en Configuración, porque de ella se deriva su cifrado.

## 1. Situarse (5 minutos)

```bash
docker compose up -d
```

```bash
docker compose exec backend pytest -q
```

Deben salir **152 en verde**. Si no, **eso es la sesión**: no se empieza nada nuevo sobre terreno
que ya se movió.

Luego leer `ESTADO.md` y, de `FASES.md`, la etapa 2.

## 2. La fase que toca: S.2 — El seed no debe correr en producción

**El problema, medido:** `backend/app/main.py:18` ejecuta el seed en **cada arranque, sin mirar el
entorno**. En un servidor real crearía los tres usuarios de demo —incluido un `super_admin`— con la
contraseña `Demo1234!`, que está publicada en este repositorio y en `CLAUDE.md`.

🔴 **Ya pasó, y en esta misma máquina.** El 14 de octubre el dueño renombró `admin@atsdemo.com`
desde la pantalla de usuarios; en el siguiente arranque el seed **volvió a crearlo**, porque busca
por correo y ya no lo encontraba. Hoy hay 5 usuarios, dos de ellos cuentas de demo recreadas con la
contraseña publicada. Dejó de ser un riesgo teórico.

Es la **misma clase de fallo que S.1**: una credencial conocida que llega a producción sola.

**Terminada cuando:**
- El seed solo corre si el entorno lo pide explícitamente (una variable, no una suposición).
- Fuera de desarrollo **no crea usuarios de demo**, y si no hay ningún administrador lo dice en vez
  de inventarse uno.
- Hay una prueba que lo comprueba con los dos controles: que en desarrollo sí siembra y que con la
  variable apagada no.

**Cuidado con:** las pruebas dependen de los usuarios de demo (`DEMO_USERS` en `conftest.py`). Lo
que se apaga es el seed en producción, no el de las pruebas.

**Añadir al cerrarla:** que el seed **no recree** una cuenta de demo que alguien renombró a
propósito. Buscar por correo no basta; hace falta una marca de "esta cuenta vino del seed".

**Después, en la misma etapa:** `S.3` (límite de peticiones en el portal público) y `S.4`
(revisar el resto de entradas sin límite). Nota: el límite de tamaño y de tipo real en archivos
subidos ya se hizo el 12 de octubre, al construir la subida de la imagen del post, y el 14 se
aplicó también al CV.

## 2B. Lo más visible que quedó a medias

- **El menú lateral se oculta por rol, no por permisos** (fase M7.2). Los permisos ya se
  administran y se guardan, pero hasta pintar el menú desde `/users/yo/permisos` lo que marques en
  los otros módulos no se nota. Es lo que más se echa en falta tras lo de la sesión 8.
- **El formulario de postulación sigue siendo el antiguo**, de 12 campos. El backend devuelve ya
  los ~40 (`POST /api/v1/public/leer-cv`), así que falta solo la pantalla de 3 pasos.

## 3. Lo que necesita que el dueño actúe

Nada de esto lo puede resolver Claude solo.

| Qué | Para qué |
|---|---|
| **App de LinkedIn** | Crearla en developer.linkedin.com (requiere una Página de empresa), añadir los productos *Sign In with LinkedIn (OIDC)* y *Share on LinkedIn*, y pegar Client ID, Secret y Redirect URI en Configuración. Hasta entonces publicar queda en **modo simulado**, y lo dice. |
| **Correo** | O una contraseña de aplicación de Gmail, o los datos del servidor SMTP institucional. Sin eso no hay envío interno. El botón "Probar conexión" valida sin enviar nada. |

## 4. Trabajo pendiente conocido

Ninguno bloquea la etapa 2; se recogen para que no se pierdan.

- **M1.6 — Publicar a la hora programada.** La fecha se guarda, pero **nada la ejecuta**: hoy hay
  que pulsar el botón. Necesita un proceso aparte (APScheduler en el propio backend es lo más
  barato; ojo a que Docker tiene 3,7 GB para todo).
- **M1.5 — Devolver la gestión de preguntas filtro.** Sigue sin haber forma de crearlas desde la
  aplicación; el portal solo muestra las del seed.
- **Contrastar las taxonomías.** Niveles de educación (LOES) y áreas académicas (CINE-UNESCO) se
  sembraron de memoria en `backend/app/seed.py`.
- **Correos de demo.** Siguen siendo `@atsdemo.com`. No se ven en la interfaz, pero chirrían ahora
  que la aplicación es de la ANAI.
- **Escudo a color.** El SVG actual es monocromo (`#20395f`), que es como lo dio el dueño. Una
  versión a color mejoraría el acceso, que tiene fondo azul.

## 5. Decisiones que siguen pendientes del dueño

1. ¿El repo sigue público? Ya no hay secretos dentro, pero la contraseña de demo sí está.
2. ¿Dónde se despliega? Sin eso no se puede detallar `D.1`.
3. ¿Dónde se guardan los CVs? La imagen del post ya va a un volumen de Docker; lo natural es que
   el CV siga el mismo camino, pero en un servidor real eso obliga a pensar en copias de seguridad.

## 6. Cómo se cierra la sesión

1. Actualizar `ESTADO.md` si cambió la fase activa o el estado de algún módulo.
2. Anotar el día en `BITACORA.md`, separando **lo verificado** de lo que solo se escribió.
   Para no inventar: `git log --since=midnight --format="%h %s"`.
3. Borrar los datos de prueba que se hayan creado y comprobar el recuento en PostgreSQL.
4. Reescribir este archivo para la sesión siguiente.
5. Commit y push **a la rama de trabajo, nunca a `main`**.
