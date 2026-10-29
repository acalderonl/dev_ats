"""Límite de peticiones para los endpoints abiertos del portal público.

Por qué hace falta ahora y no antes: hasta ahora lo peor que podía hacer alguien era
llenar la base de postulaciones basura. Desde que la lectura del CV llama a la API de
Claude, **cada llamada cuesta dinero**, y un endpoint sin autenticación ni freno en
internet es una factura abierta a quien quiera escribir un bucle.

Se cuenta por IP y en memoria del proceso. Es deliberadamente simple:

- **Por IP** porque el candidato no está autenticado; no hay nada mejor que mirar.
- **En memoria** porque con un solo proceso basta y evita montar Redis para esto. La
  consecuencia está asumida: al reiniciar se olvida, y con varias réplicas cada una
  lleva su cuenta. Para un entorno de prueba es suficiente; si algún día hay varias
  instancias, esto es lo que hay que mover a un almacén compartido.
"""

import time
from collections import defaultdict, deque
from threading import Lock

from fastapi import HTTPException, Request, status

# Peticiones permitidas por ventana, por IP.
LIMITES = {
    # La lectura del CV cuesta dinero por llamada: es la más restringida.
    "leer_cv": (5, 60 * 10),
    # Postular es algo que una persona hace una vez, dos si se equivoca.
    "postular": (10, 60 * 10),
    # Mirar una vacante es barato y legítimo repetir.
    "consulta": (60, 60),
    # Subir una foto o un CV escribe en disco sin que nadie haya iniciado sesión.
    "subir_archivo": (10, 60 * 10),
}

_accesos: dict[str, deque[float]] = defaultdict(deque)
_cerrojo = Lock()


def _ip_de(request: Request) -> str:
    """La IP del cliente, mirando la cabecera del proxy.

    Railway, Render y cualquier proxy ponen la IP real en `X-Forwarded-For`; sin esto
    todas las peticiones parecerían venir del proxy y el límite se aplicaría a todo el
    mundo junto.
    """
    reenviada = request.headers.get("x-forwarded-for")
    if reenviada:
        return reenviada.split(",")[0].strip()
    return request.client.host if request.client else "desconocida"


def limitar(nombre: str):
    """Dependencia de FastAPI que aplica uno de los límites de `LIMITES`."""
    maximo, ventana = LIMITES[nombre]

    def dependencia(request: Request) -> None:
        clave = f"{nombre}:{_ip_de(request)}"
        ahora = time.monotonic()
        with _cerrojo:
            marcas = _accesos[clave]
            # Fuera lo que ya salió de la ventana.
            while marcas and ahora - marcas[0] > ventana:
                marcas.popleft()
            if len(marcas) >= maximo:
                espera = int(ventana - (ahora - marcas[0])) + 1
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"Demasiadas peticiones. Vuelve a intentarlo en {espera} segundos.",
                    headers={"Retry-After": str(espera)},
                )
            marcas.append(ahora)

    return dependencia


def reiniciar() -> None:
    """Olvida lo contado. Solo para las pruebas: sin esto se arrastran entre casos."""
    with _cerrojo:
        _accesos.clear()
