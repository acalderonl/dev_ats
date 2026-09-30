"""Reglas de transición de estados del pipeline de reclutamiento.

Regla estricta del negocio (ver docs/objetivo_general-v2.md, Módulo 3.2): ninguna
postulación puede avanzar de etapa sin haber sido previamente autorizada por un
reclutador. Una vez autorizada, se permite avanzar a cualquier etapa posterior o
descartar en cualquier momento, pero no retroceder a una etapa anterior.
"""

from fastapi import HTTPException, status

ORDERED_STAGES = [
    "postulacion_revisada",
    "en_revision",
    "preseleccionado",
    "evaluaciones",
    "entrevista",
    "contratado",
]

TERMINAL_REJECTED = "descartado"
PENDIENTE = "pendiente_autorizacion"


def validate_transition(estado_actual: str, estado_destino: str) -> None:
    if estado_actual == PENDIENTE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="La postulación debe ser autorizada antes de ingresar al pipeline",
        )

    if estado_destino == TERMINAL_REJECTED:
        return

    if estado_actual == TERMINAL_REJECTED:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="No se puede reactivar una postulación descartada",
        )

    if estado_destino not in ORDERED_STAGES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Estado de destino inválido")

    if estado_actual == "contratado":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="La postulación ya fue contratada y no puede moverse de etapa",
        )

    indice_actual = ORDERED_STAGES.index(estado_actual)
    indice_destino = ORDERED_STAGES.index(estado_destino)
    if indice_destino < indice_actual:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="No se puede retroceder a una etapa anterior del pipeline",
        )
