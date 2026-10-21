#!/usr/bin/env bash
#
# Pone el servidor en la última versión. Es el comando del día a día:
#
#     cd ~/dev_ats && bash scripts/actualizar.sh
#
# Trae los cambios, reconstruye lo que haya cambiado y reinicia. Las migraciones de
# base de datos las aplica el backend al arrancar, así que un cambio de esquema viaja
# con su código y no hay que acordarse de nada.
#
# Antes de reconstruir hace una copia de la base. Es barata y evita el único error
# irreversible: una migración que sale mal sobre datos que ya importaban.

set -euo pipefail

cd "$(dirname "$0")/.."

COMPOSE=(docker compose -f docker-compose.prod.yml --env-file .env.produccion)
CARPETA_COPIAS="${CARPETA_COPIAS:-$HOME/copias-ats}"
COPIAS_A_GUARDAR=7

decir() { printf '\n\033[1;34m==>\033[0m %s\n' "$1"; }
fallo() { printf '\n\033[1;31m!!\033[0m %s\n' "$1" >&2; exit 1; }

[[ -f .env.produccion ]] || fallo "No hay .env.produccion. Ejecuta antes scripts/instalar-servidor.sh"

decir "Trayendo los cambios"
rama="$(git rev-parse --abbrev-ref HEAD)"
antes="$(git rev-parse --short HEAD)"
git pull --ff-only origin "$rama"
despues="$(git rev-parse --short HEAD)"

if [[ "$antes" == "$despues" ]]; then
    decir "Ya estaba en la última versión ($antes). Reconstruyo igualmente por si cambió el entorno."
else
    decir "De $antes a $despues"
    git --no-pager log --oneline "$antes..$despues" | sed 's/^/    /'
fi

# Solo si la base ya está levantada: en el primer despliegue no hay nada que copiar.
if "${COMPOSE[@]}" ps --status running --services 2>/dev/null | grep -qx db; then
    decir "Copia de la base antes de tocar nada"
    mkdir -p "$CARPETA_COPIAS"
    archivo="$CARPETA_COPIAS/ats-$(date +%Y%m%d-%H%M%S).sql.gz"
    # shellcheck disable=SC1091
    usuario="$(grep -E '^POSTGRES_USER=' .env.produccion | cut -d= -f2)"
    base="$(grep -E '^POSTGRES_DB=' .env.produccion | cut -d= -f2)"
    "${COMPOSE[@]}" exec -T db pg_dump -U "$usuario" "${base:-ats}" | gzip > "$archivo"
    decir "Guardada en $archivo ($(du -h "$archivo" | cut -f1))"

    # Las viejas se van solas: si no, el disco se llena en silencio.
    ls -1t "$CARPETA_COPIAS"/ats-*.sql.gz 2>/dev/null | tail -n +$((COPIAS_A_GUARDAR + 1)) | xargs -r rm --
fi

decir "Reconstruyendo y levantando"
"${COMPOSE[@]}" up -d --build

decir "Esperando a que responda"
for intento in $(seq 1 30); do
    if "${COMPOSE[@]}" exec -T backend python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" 2>/dev/null; then
        decir "La API responde. Versión $despues desplegada."
        # Las imágenes de versiones anteriores se acumulan y llenan el disco.
        docker image prune -f >/dev/null
        exit 0
    fi
    sleep 2
done

fallo "La API no respondió en 60 segundos. Mira qué pasó:
    ${COMPOSE[*]} logs --tail=50 backend"
