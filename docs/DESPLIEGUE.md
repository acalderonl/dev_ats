# Poner la aplicación en un servidor de Google Cloud

Guía para el **entorno de prueba**: una copia accesible por URL para que otra persona
siga el avance. No es producción de verdad y no debe tener datos de personas reales; lo
que falta para eso está al final.

Todo lo que hay aquí lo ejecutas tú. Yo preparé los ficheros; las claves de tu cuenta
de Google son tuyas y no las toco.

---

## Antes de empezar: lo que necesitas a mano

- Tu cuenta de Google Cloud con facturación activa (ya la tienes).
- **Un dominio o subdominio** donde puedas crear un registro DNS. Por ejemplo
  `ats.tudominio.com`.
- Unos 20 minutos.

Coste estimado: **13–15 USD al mes** con la máquina que recomiendo. Puedes apagarla
cuando no la necesites y solo pagas el disco (~1 USD/mes).

---

## Paso 1 · Crear el proyecto

En [console.cloud.google.com](https://console.cloud.google.com), arriba a la izquierda,
selector de proyectos → **Proyecto nuevo**. Llámalo `ats-anai`.

Anota el **ID del proyecto** (no el nombre: el ID suele llevar números detrás).

---

## Paso 2 · Reservar una IP fija

Este paso es el que más gente se salta y luego pasa factura: **sin IP fija, la dirección
cambia cada vez que la máquina se apaga y se enciende**, y tu DNS deja de apuntar a
ninguna parte.

**VPC network → IP addresses → Reserve external static address**

| Campo | Valor |
|---|---|
| Name | `ats-ip` |
| Type | Regional |
| Region | `southamerica-west1` (Santiago) — la más cercana a Ecuador |

Anota la IP que te da.

---

## Paso 3 · Crear la máquina

**Compute Engine → VM instances → Create instance**

| Campo | Valor | Por qué |
|---|---|---|
| Name | `ats-servidor` | |
| Region / Zone | `southamerica-west1` / `-a` | La misma que la IP reservada |
| Machine type | **e2-small** (2 vCPU, 2 GB) | La `e2-micro` de la capa gratuita se queda sin memoria al compilar el frontend |
| Boot disk | **Ubuntu 24.04 LTS**, 20 GB, Balanced | |
| Firewall | ✅ **Allow HTTP traffic**<br>✅ **Allow HTTPS traffic** | Sin esto nadie llega, ni siquiera Let's Encrypt |
| Network → External IP | **`ats-ip`** (la que reservaste) | |

> Si prefieres la línea de comandos, con `gcloud` instalado:
>
> ```bash
> gcloud compute instances create ats-servidor --project=TU_PROYECTO --zone=southamerica-west1-a --machine-type=e2-small --image-family=ubuntu-2404-lts-amd64 --image-project=ubuntu-os-cloud --boot-disk-size=20GB --boot-disk-type=pd-balanced --address=ats-ip --tags=http-server,https-server
> ```

---

## Paso 4 · Apuntar el dominio

En el panel de tu dominio, crea un registro **A**:

| Tipo | Nombre | Valor |
|---|---|---|
| A | `ats` (o el subdominio que quieras) | La IP del paso 2 |

**Comprueba que ya propagó antes de seguir.** Desde tu equipo:

```bash
nslookup ats.tudominio.com
```

Tiene que devolver la IP de tu máquina. Si no, espera: puede tardar de minutos a horas.
Levantar antes de que propague hace que Let's Encrypt falle y reintente con esperas cada
vez más largas.

---

## Paso 5 · Entrar a la máquina

En la lista de VMs, botón **SSH**. Se abre una terminal en el navegador, ya autenticada.

---

## Paso 6 · Instalar

Pega esto en la terminal SSH:

```bash
curl -fsSL https://raw.githubusercontent.com/acalderonl/dev_ats/main/scripts/instalar-servidor.sh | bash
```

Instala Docker, clona el repositorio en `~/dev_ats` y **genera solas** la clave de firma
y la contraseña de la base de datos.

Cuando termine, **cierra la sesión SSH y vuelve a entrar**. Hace falta para que tu
usuario quede en el grupo `docker` y no tengas que escribir `sudo` delante de todo.

---

## Paso 7 · Rellenar lo que solo tú sabes

```bash
nano ~/dev_ats/.env.produccion
```

Tres valores:

| Variable | Qué poner |
|---|---|
| `DOMINIO` | `ats.tudominio.com`, el del paso 4 |
| `ADMIN_INICIAL_EMAIL` | Tu correo. Será el super admin |
| `ADMIN_INICIAL_PASSWORD` | Una contraseña larga y **nueva**. No reutilices otra |

`SECRET_KEY` y `POSTGRES_PASSWORD` ya están puestas: las generó el script.

Guardar en nano: `Ctrl+O`, `Enter`, `Ctrl+X`.

---

## Paso 8 · Levantar

```bash
cd ~/dev_ats && bash scripts/actualizar.sh
```

La primera vez tarda **varios minutos**: tiene que construir las dos imágenes. Verás
cómo compila el frontend y cómo el backend aplica las migraciones.

Cuando termine, abre `https://ats.tudominio.com`. El candado del navegador debería
aparecer solo: Caddy pide el certificado al arrancar.

Entra con el correo y la contraseña del paso 7, y **cámbiala desde la pantalla de
usuarios**: la que pusiste quedó escrita en un fichero del servidor.

---

## El día a día: actualizar

Cada vez que quieras llevar los cambios al servidor:

```bash
cd ~/dev_ats && bash scripts/actualizar.sh
```

Eso hace, por orden:

1. Trae los cambios y te enseña qué commits entran
2. **Guarda una copia de la base** en `~/copias-ats` (conserva las 7 últimas)
3. Reconstruye solo lo que cambió
4. Aplica las migraciones al arrancar el backend
5. Comprueba que la API responde antes de dar por bueno el despliegue

Si algo falla, el script te lo dice y te deja el comando para ver los registros.

> **Antes de empujar desde tu equipo**, conviene:
> ```bash
> docker compose exec backend pytest -q
> ```

---

## Comandos que vas a necesitar

```bash
cd ~/dev_ats && docker compose -f docker-compose.prod.yml --env-file .env.produccion logs -f backend
```

```bash
cd ~/dev_ats && docker compose -f docker-compose.prod.yml --env-file .env.produccion ps
```

Reiniciar todo sin reconstruir:

```bash
cd ~/dev_ats && docker compose -f docker-compose.prod.yml --env-file .env.produccion restart
```

Volver a una versión anterior:

```bash
cd ~/dev_ats && git log --oneline -10
```
```bash
cd ~/dev_ats && git checkout COMMIT && bash scripts/actualizar.sh
```

---

## Cómo queda montado

```
internet  →  Caddy (80/443)  →  frontend (nginx)  →  backend  →  PostgreSQL
              HTTPS              estáticos +          API         datos
              automático         proxy /api
```

**Solo Caddy mira a internet.** La API, la base de datos y el frontend se hablan por la
red interna de Docker: no hay puertos publicados hacia fuera. Como el frontend hace de
proxy, el navegador siempre habla con un único origen y **no hay CORS** que configurar.

En el servidor, `ENTORNO=produccion` hace que el seed **no cree** las cuentas de demo.
Esto importa: la contraseña `Demo1234!` está en este repositorio público, y con una URL
en internet cualquiera que lo lea entraría como super admin.

---

## Lo que NO está resuelto

Dicho claro, porque un entorno que parece producción invita a tratarlo como tal:

- **Las copias de la base son locales a la máquina.** Si se borra la VM, se van con
  ella. Suficiente para datos inventados; para datos reales habría que sacarlas a
  Cloud Storage.
- **No se puede borrar a un candidato que lo pida** (fase S.5). Hace falta antes de que
  haya datos personales de verdad.
- **El límite de peticiones se cuenta en memoria**, así que se reinicia en cada
  despliegue.
- **La clave de la API de Claude cuesta dinero por CV leído.** El endpoint admite 5
  lecturas cada 10 minutos por IP, pero vigila el gasto en console.anthropic.com.
- **Si cambias `SECRET_KEY`**, hay que volver a introducir las credenciales de LinkedIn
  y del correo: de ella se deriva su cifrado.

---

## Si algo no arranca

| Síntoma | Causa casi segura |
|---|---|
| El navegador no carga nada | El DNS todavía no apunta a la IP, o faltan las reglas de firewall HTTP/HTTPS |
| Sale aviso de certificado | Caddy aún no lo consiguió. `logs caddy` lo dice. Casi siempre es el DNS |
| El backend no levanta y menciona `SECRET_KEY` | Falta en `.env.produccion` o tiene menos de 32 caracteres |
| Entras y no hay ningún usuario | Faltaron `ADMIN_INICIAL_*` en el primer arranque. Ponlas y vuelve a levantar: solo se usan si la base está vacía |
| La compilación del frontend se queda colgada | La máquina se quedó sin memoria. Sube a `e2-medium`, o añade intercambio:<br>`sudo fallocate -l 2G /swapfile && sudo chmod 600 /swapfile && sudo mkswap /swapfile && sudo swapon /swapfile` |
| `429` al subir un CV | El límite del portal público. Es lo esperado |

---

## Alternativa: Render

En el repositorio hay un `render.yaml` de una preparación anterior. Si algún día quieres
algo sin servidor que mantener, sirve: conectas el repo como Blueprint y cada push
despliega solo. La contrapartida de su plan gratuito es que **apaga los servicios** tras
un rato sin uso y **su base de datos caduca a los 90 días**.
