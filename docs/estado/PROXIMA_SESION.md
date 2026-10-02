# Arranque de la próxima sesión

> Escrito al cerrar el **2026-10-02**. Si al leerlo ya no cuadra con el código, manda el código:
> se corrige este archivo antes de seguir.

## 1. Situarse (5 minutos)

```bash
docker compose up -d                      # el entorno completo
docker compose exec backend pytest -q     # deben salir 48 en verde
```

Si las pruebas no salen en verde, **eso es la sesión**: no se empieza nada nuevo sobre terreno que
ya se movió.

Luego leer `ESTADO.md` (dónde estamos) y, de `FASES.md`, la etapa 2.

## 2. La fase que toca: S.1 — Secretos fuera del código

Es la primera de la etapa 2 y la más grave de las cuatro puertas abiertas.

**El problema, medido:** `backend/app/core/config.py:10` trae
`secret_key: str = "supersecretkey_ats_2026"`, y ese valor está publicado en este repo. Con él,
cualquiera puede **firmar un token de super admin sin conocer ninguna contraseña**.

**Terminada cuando:**
- `SECRET_KEY` no tiene valor por defecto: si falta, la aplicación **no arranca** y lo dice claro.
- `docker-compose.yml` y `.env.example` dejan de traer el valor real; se documenta cómo generar uno.
- Hay una prueba que comprueba que, sin `SECRET_KEY`, la configuración falla.

**Cuidado con:** al quitar el valor por defecto, las pruebas y el arranque local necesitan uno. Que
el fallo sea explícito y con mensaje útil, no un `KeyError` a medio arrancar.

**Después, en la misma etapa:** `S.2` (el seed no debe crear usuarios de demo fuera de desarrollo:
hoy `main.py:18` lo hace en cada arranque sin mirar el entorno), `S.3` (límite de tamaño y tipo real
en los archivos subidos) y `S.4` (límite de peticiones en el portal público).

## 3. Lo que quedó abierto del módulo de Cargos

Ninguna de estas bloquea la etapa 2; se recogen para que no se pierdan.

- **M1.5 — Devolver la gestión de preguntas filtro.** Se quitó de las tarjetas por petición del
  dueño, y hoy **no hay forma de crear preguntas desde la aplicación**. El portal del candidato solo
  mostrará las que creó el seed. Lo natural es traerlas como una sección más del modal de cargo.
- **Contrastar las taxonomías.** Los niveles de educación (LOES) y las áreas académicas
  (CINE-UNESCO) se sembraron de memoria en `backend/app/seed.py`. Conviene verificarlos contra la
  fuente oficial vigente antes de que entren datos reales.
- **Faltan secciones del modal.** El dueño dijo "faltan más ítems": hoy van siete bloques.

## 4. Decisiones que siguen pendientes del dueño

1. ¿El repo sigue público? No es un problema en sí, pero obliga a cerrar la etapa 2 antes de desplegar.
2. ¿Dónde se despliega? Sin eso no se puede detallar `D.1`.
3. ¿Dónde se guardan los CVs? Cambia bastante cómo se hace `M2.1`.

## 5. Cómo se cierra la sesión

1. Actualizar `ESTADO.md` si cambió la fase activa o el estado de algún módulo.
2. Anotar el día en `BITACORA.md`, separando **lo verificado** de lo que solo se escribió.
   Para no inventar: `git log --since=midnight --format="%h %s"`.
3. Reescribir este archivo para la sesión siguiente.
4. Commit y push.
