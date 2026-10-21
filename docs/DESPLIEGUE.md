# Poner la aplicación en internet

Esta guía es para el **entorno de prueba**: una copia accesible por URL para que otra
persona siga el avance. No es producción de verdad y no debe tener datos de personas
reales; si algún día los tiene, hay cosas que faltan y están listadas al final.

---

## Lo que cambia respecto a tu equipo

| | En tu equipo | Desplegado |
|---|---|---|
| `ENTORNO` | `desarrollo` (por defecto) | **`produccion`** |
| Cuentas | Las tres de demo con `Demo1234!` | **Ninguna.** Solo el admin que tú definas |
| Backend | `--reload`, vigila el disco | Sin recarga, usuario sin privilegios |
| Frontend | Servidor de Vite | Compilado y servido con nginx |
| La API | `localhost:8000`, pública | **Privada.** Solo la alcanza el frontend |

El cambio que más importa: **en producción el seed no crea las cuentas de demo**. La
contraseña `Demo1234!` está en este repositorio público; con una URL en internet,
cualquiera que lo lea entraría como super admin.

---

## Desplegar en Render

### 1. Antes de empezar

Necesitas una cuenta en [render.com](https://render.com) y que el repositorio esté en
GitHub (ya lo está).

### 2. Crear el Blueprint

1. En Render: **New → Blueprint**
2. Elige el repositorio `acalderonl/dev_ats`
3. Elige la rama que quieres desplegar
4. Render lee `render.yaml` y propone tres cosas: la base de datos, `ats-api` y `ats-web`

### 3. Los dos valores que te va a pedir

Son los únicos que no están en el fichero, porque son secretos:

| Variable | Qué poner |
|---|---|
| `ADMIN_INICIAL_EMAIL` | Tu correo. Será el super admin |
| `ADMIN_INICIAL_PASSWORD` | Una contraseña larga. **No la reutilices de otro sitio** |

`SECRET_KEY` la genera Render sola.

### 4. Listo

La URL que te dé `ats-web` es la aplicación. Entra con el correo y la contraseña de
arriba y **cámbiala desde la pantalla de usuarios**: la que pusiste queda guardada en
el panel de Render.

---

## Actualizar

**Cada push a la rama desplegada actualiza el entorno solo.** No hay nada más que hacer.

Las migraciones de base de datos se aplican al arrancar el backend (`alembic upgrade
head` va en el comando de la imagen), así que un cambio de esquema viaja con su código.

Lo que conviene antes de empujar:

```bash
docker compose exec backend pytest -q
```

```bash
docker compose exec frontend npx tsc --noEmit
```

Si algo se rompe al desplegar, Render guarda las versiones anteriores: **Deploys →
Rollback** vuelve a la última que funcionaba.

---

## Railway, si lo prefieres

Los mismos `Dockerfile` sirven. Lo que cambia es que allí los servicios se crean desde
la interfaz, no desde un fichero:

1. **New Project → Deploy from GitHub repo**
2. Añade un servicio **PostgreSQL**
3. Añade dos servicios desde el repo, con *Root Directory* `backend` y `frontend`
4. Variables del backend: `ENTORNO=produccion`, `DATABASE_URL` (Railway la ofrece como
   referencia a la base), `SECRET_KEY`, `ADMIN_INICIAL_EMAIL`, `ADMIN_INICIAL_PASSWORD`
5. Variable del frontend: `API_URL` apuntando al backend por su dirección interna
6. Expón **solo** el frontend

**Diferencia que importa para elegir:** el plan gratuito de Render **apaga los servicios
tras un rato sin uso** (la primera visita tarda unos segundos en despertar) y **su base
de datos gratuita caduca a los 90 días**. Railway no se apaga, pero no tiene plan
gratuito permanente: va por consumo, unos pocos dólares al mes.

Para que otra persona entre a mirar de vez en cuando, el apagado de Render se nota.
Si eso molesta, Railway sale mejor.

---

## Lo que NO está resuelto

Dicho claro, porque un entorno que parece producción invita a tratarlo como tal:

- **No hay copias de seguridad.** Se acordó así porque solo va a tener datos inventados.
  Si algún día entran candidatos reales, esto es lo primero que hay que añadir.
- **No se puede borrar a un candidato que lo pida.** Hace falta antes de que haya datos
  personales de verdad (fase S.5).
- **El límite de peticiones se cuenta en memoria del proceso.** Se reinicia al
  desplegar, y con varias réplicas cada una lleva su cuenta. Suficiente para esto; con
  tráfico real habría que moverlo a un almacén compartido.
- **Las credenciales de LinkedIn y del correo se configuran desde la aplicación** y se
  guardan cifradas con una clave derivada de `SECRET_KEY`. Si Render regenera
  `SECRET_KEY`, hay que volver a introducirlas.
- **La clave de la API de Claude cuesta dinero por CV leído.** El endpoint está
  limitado a 5 lecturas cada 10 minutos por IP, pero si lo dejas configurado en un
  entorno público, vigila el gasto en console.anthropic.com.

---

## Si algo no arranca

| Síntoma | Causa casi segura |
|---|---|
| El backend no levanta y el log dice `SECRET_KEY` | Falta la variable, o tiene menos de 32 caracteres |
| Entras y no hay ningún usuario | Faltaron `ADMIN_INICIAL_EMAIL`/`PASSWORD` en el primer arranque. Ponlas y reinicia: solo se usan si la base está vacía |
| La aplicación carga pero ninguna acción funciona | `API_URL` del frontend mal puesta. Mira el log de nginx |
| `429` al subir un CV | El límite del portal público. Es lo esperado; espera los minutos que diga la respuesta |
