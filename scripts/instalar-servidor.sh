#!/usr/bin/env bash
#
# Prepara una máquina Ubuntu recién creada para alojar la aplicación.
#
# Se ejecuta UNA vez, por SSH, en la VM de Compute Engine:
#
#     curl -fsSL https://raw.githubusercontent.com/acalderonl/dev_ats/main/scripts/instalar-servidor.sh | bash
#
# o, si ya clonaste el repositorio:  bash scripts/instalar-servidor.sh
#
# Qué hace: instala Docker, clona el repositorio y deja el fichero de variables listo
# para rellenar. **No levanta nada**: eso es a propósito, porque sin las variables la
# aplicación no debe arrancar.

set -euo pipefail

REPOSITORIO="https://github.com/acalderonl/dev_ats.git"
DESTINO="${DESTINO:-$HOME/dev_ats}"
RAMA="${RAMA:-main}"

decir() { printf '\n\033[1;34m==>\033[0m %s\n' "$1"; }
aviso() { printf '\n\033[1;33m!!\033[0m %s\n' "$1"; }

if [[ $EUID -eq 0 ]]; then
    aviso "Estás como root. Mejor usa tu usuario normal: el script usa sudo cuando hace falta."
    exit 1
fi

decir "Actualizando el sistema"
sudo apt-get update -qq
sudo apt-get upgrade -y -qq

if ! command -v docker &>/dev/null; then
    decir "Instalando Docker"
    curl -fsSL https://get.docker.com | sudo sh
    # Sin esto habría que escribir sudo delante de cada comando de docker.
    sudo usermod -aG docker "$USER"
    aviso "Te he añadido al grupo docker. Cierra la sesión SSH y vuelve a entrar para que surta efecto."
else
    decir "Docker ya está instalado: $(docker --version)"
fi

if [[ ! -d "$DESTINO/.git" ]]; then
    decir "Clonando el repositorio en $DESTINO"
    git clone --branch "$RAMA" "$REPOSITORIO" "$DESTINO"
else
    decir "El repositorio ya está en $DESTINO"
fi

cd "$DESTINO"

if [[ ! -f .env.produccion ]]; then
    decir "Creando .env.produccion a partir del ejemplo"
    cp .env.produccion.example .env.produccion

    # Se generan aquí para que nadie tenga que inventárselas ni reutilizar otras.
    clave_secreta="$(openssl rand -base64 48 | tr -d '\n/+=')"
    clave_base="$(openssl rand -base64 32 | tr -d '\n/+=')"
    sed -i "s|^SECRET_KEY=.*|SECRET_KEY=${clave_secreta}|" .env.produccion
    sed -i "s|^POSTGRES_PASSWORD=.*|POSTGRES_PASSWORD=${clave_base}|" .env.produccion
    chmod 600 .env.produccion

    decir "Generadas SECRET_KEY y POSTGRES_PASSWORD"
else
    decir ".env.produccion ya existe: no se toca"
fi

cat <<'FIN'

────────────────────────────────────────────────────────────
  Falta lo que solo tú puedes decidir. Edita el fichero:

      nano ~/dev_ats/.env.produccion

  y rellena:
      DOMINIO                  el nombre que apunta a esta máquina
      ADMIN_INICIAL_EMAIL      tu correo, será el super admin
      ADMIN_INICIAL_PASSWORD   una contraseña larga y nueva

  Comprueba que el DNS ya apunta aquí ANTES de levantar, o el
  certificado fallará:

      dig +short TU.DOMINIO

  Y entonces:

      cd ~/dev_ats && bash scripts/actualizar.sh
────────────────────────────────────────────────────────────

FIN
