# Estado del proyecto — dónde estamos AHORA

> Última actualización: **2026-10-01** · Días trabajados: **3** · Commits: **1**
> Este archivo se lee al empezar cada sesión. Si algo aquí ya no es cierto, se corrige antes de seguir.

## En una línea

Los 7 módulos del ATS están **construidos en su versión base** y el stack corre con Docker Compose,
pero **la suite de pruebas nunca se ha ejecutado** y hay **4 puertas de seguridad abiertas** que impiden
salir a internet. El destino es producción real, así que ambas cosas van antes que cualquier mejora.

## Fase activa

| | |
|---|---|
| **Fase** | `T.1 — Correr la suite por primera vez` |
| **Etapa** | 1 de 6 — Terreno firme |
| **Por qué esta** | Hay 19 pruebas escritas que nunca corrieron. Mientras no estén en verde, ninguna afirmación sobre los otros módulos está respaldada. |
| **Terminada cuando** | `docker compose exec backend pytest` pasa en verde y el resultado queda anotado en la bitácora. |
| **Antes hay que** | Levantar Docker Desktop: está apagado desde el reinicio del 29-sep. |

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
| **M1** Cargos, vacantes e integraciones | 🟡 | Crear vacante (a mano, en el navegador) | M1.1 subir el documento | 3 |
| **M2** Portal público y parsing de CV | 🟡 | ❌ nada | M2.1 guardar el CV de verdad | 3 |
| **M3** Pipeline de reclutamiento | 🟡 | ❌ nada | M3.3 puntuación de coincidencia | 4 |
| **M4** Directorio de contactos | 🟡 | ❌ nada | M4.1 exportar de verdad | 4 |
| **M5** Evaluaciones | 🟡 | ❌ nada | M5.1 scorecard consolidado | 4 |
| **M6** Dashboard | 🟡 | Carga y dibuja (a mano) | M6.1 volumen en el tiempo | 6 |
| **M7** Usuarios y roles | 🟡 | Login con los 3 roles (a mano) | M7.1 guardas de ruta | 4 |
| **S** Seguridad | 🔴 | 4 fallos **confirmados** en el código | S.1 secretos fuera del código | 2 |
| **T** Transversal | 🟡 | Stack arriba, 2 bugs corregidos | **T.1 correr la suite** ⬅ activa | 1 |

La columna **Verificado** solo dice lo que se comprobó de verdad. "A mano" significa que una persona lo
usó en el navegador: no es una prueba automática y no protege contra regresiones.

## Lo más urgente, en una frase

`SECRET_KEY` tiene un valor por defecto que está publicado en GitHub. Con él se puede **fabricar un
token de super admin sin contraseña**. Mientras el sistema solo corra en tu equipo no hay riesgo, pero
es lo primero que hay que cerrar antes de que esto toque internet (fase S.1).

## Entorno

- Código real en `C:\Users\abdon\OneDrive\Documentos\DEV\dev_ats` (OneDrive, **no** en `Documents`).
- Repo: https://github.com/acalderonl/dev_ats (**público**, rama `main`).
- En el host hay Git y GitHub CLI; **no** hay Node ni Python: todo se compila y prueba dentro de los contenedores.
- Docker tiene 3,7 GB para todos los contenedores: levantar y medir antes de añadir servicios.

## Cómo se usa este sistema

1. **Al empezar** una sesión: leer este archivo. Dice la fase activa y qué está sin verificar.
2. **Durante**: si cambia el estado de un módulo o se termina una fase, se actualiza aquí y en `FASES.md`.
3. **Al terminar**: anotar el día en `BITACORA.md`. Para no inventar lo que se hizo:
   `git log --since=midnight --format="%h %s"`

Las reglas de qué significa "terminado" están en `FASES.md`.
