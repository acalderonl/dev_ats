# Estado del proyecto — dónde estamos AHORA

> Última actualización: **2026-10-12** · Días trabajados: **5** · Pruebas: **53 en verde**
> Este archivo se lee al empezar cada sesión. Si algo aquí ya no es cierto, se corrige antes de seguir.

## En una línea

La suite ya corre y está aislada de la base de desarrollo, y el **módulo de Cargos (M1) quedó
rehecho** como descriptivo de puesto completo. Siguen abiertas las **5 puertas de seguridad** que
impiden salir a internet: con destino de producción real, esa es la próxima etapa.

## Fase activa

| | |
|---|---|
| **Fase** | `S.1 — Secretos fuera del código` |
| **Etapa** | 2 de 6 — Bloqueantes de seguridad |
| **Ojo** | Lleva **dos sesiones sin empezar**: los días 4 y 12 de octubre se dedicaron a M1 por petición del dueño. La etapa 2 sigue intacta. |
| **Por qué esta** | `config.py:10` trae `SECRET_KEY` con valor por defecto, publicado en este repo. Con él se puede fabricar un token de super admin sin contraseña. |
| **Terminada cuando** | Si falta `SECRET_KEY`, la app **no arranca**. El valor de producción se genera aparte y nunca se sube. |
| **Antes hay que** | Levantar el entorno: `docker compose up -d`. |

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
| **M1** Cargos, vacantes e integraciones | 🟢 | Cargos: crear, editar y activar/desactivar, **con pruebas**. Vacantes: crear (a mano) | M1.1 subir el documento | 3 |
| **M2** Portal público y parsing de CV | 🟡 | ❌ nada | M2.1 guardar el CV de verdad | 3 |
| **M3** Pipeline de reclutamiento | 🟡 | Reglas de transición, **con pruebas** | M3.3 puntuación de coincidencia | 4 |
| **M4** Directorio de contactos | 🟡 | Búsqueda, **con pruebas** | M4.1 exportar de verdad | 4 |
| **M5** Evaluaciones | 🟡 | ❌ nada | M5.1 scorecard consolidado | 4 |
| **M6** Dashboard | 🟡 | Carga y dibuja (a mano) | M6.1 volumen en el tiempo | 6 |
| **M7** Usuarios y roles | 🟡 | Login y RBAC, **con pruebas** | M7.1 guardas de ruta | 4 |
| **S** Seguridad | 🔴 | 4 fallos **confirmados** en el código | **S.1 secretos fuera del código** ⬅ activa | 2 |
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

## Lo más urgente, en una frase

`SECRET_KEY` tiene un valor por defecto que está publicado en GitHub. Con él se puede **fabricar un
token de super admin sin contraseña**. Mientras el sistema solo corra en tu equipo no hay riesgo, pero
es lo primero que hay que cerrar antes de que esto toque internet (fase S.1).

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
