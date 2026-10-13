# Estado del proyecto — dónde estamos AHORA

> Última actualización: **2026-10-12** · Días trabajados: **6** · Pruebas: **88 en verde**
> Este archivo se lee al empezar cada sesión. Si algo aquí ya no es cierto, se corrige antes de seguir.

## En una línea

**S.1 está cerrada**: `SECRET_KEY` ya no tiene valor por defecto y la aplicación no arranca sin
ella. Los módulos de **Cargos (M1)** y **Vacantes** están rehechos: la vacante es ahora una
publicación con estados, alcance y post. Quedan **4 puertas de seguridad** de las 5.

## Fase activa

| | |
|---|---|
| **Fase** | `S.2 — El seed no debe correr en producción` |
| **Etapa** | 2 de 6 — Bloqueantes de seguridad |
| **Por qué esta** | `main.py:18` corre el seed en cada arranque sin mirar el entorno: en un servidor real crearía un super admin con contraseña conocida y publicada. Es la misma clase de fallo que S.1, que ya se cerró. |
| **Terminada cuando** | El seed solo corre si el entorno lo pide explícitamente, y nunca crea usuarios de demo fuera de desarrollo. |
| **Antes hay que** | Levantar el entorno: `docker compose up -d`. |

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
| **M1** Cargos, vacantes e integraciones | 🟢 | Cargos y vacantes: crear, editar y estados, **con pruebas**. Imagen del post y cifrado de secretos comprobados en la base | M1.6 publicar a la hora programada | 4 |
| **M2** Portal público y parsing de CV | 🟡 | ❌ nada | M2.1 guardar el CV de verdad | 3 |
| **M3** Pipeline de reclutamiento | 🟡 | Reglas de transición, **con pruebas** | M3.3 puntuación de coincidencia | 4 |
| **M4** Directorio de contactos | 🟡 | Búsqueda, **con pruebas** | M4.1 exportar de verdad | 4 |
| **M5** Evaluaciones | 🟡 | ❌ nada | M5.1 scorecard consolidado | 4 |
| **M6** Dashboard | 🟡 | Carga y dibuja (a mano) | M6.1 volumen en el tiempo | 6 |
| **M7** Usuarios y roles | 🟡 | Login y RBAC, **con pruebas** | M7.1 guardas de ruta | 4 |
| **S** Seguridad | 🟡 | S.1 cerrada y verificada con control positivo y negativo. Quedan 3 fallos confirmados | **S.2 el seed en producción** ⬅ activa | 2 |
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

La pantalla de **Configuración** guarda las credenciales de LinkedIn y Gmail **cifradas**, y no las
devuelve nunca: muestra si están puestas y sus últimos cuatro caracteres.

## Lo más urgente, en una frase

El seed corre en cada arranque sin mirar el entorno: en un servidor real **crearía un super admin con
una contraseña que está publicada en este repositorio** (fase S.2).

## Lo que necesita tu intervención

| Qué | Por qué está parado |
|---|---|
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
