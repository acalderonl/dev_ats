"""Catálogo de permisos, uno por cada acción real del sistema.

La lista sigue el **menú lateral**: cada item es un módulo y dentro van las acciones
que esa pantalla permite hoy. No hay permisos para cosas que todavía no existen —
una casilla que no gobierna nada es peor que ninguna casilla, porque hace creer que
algo está restringido cuando no lo está.

Cuando un módulo gane una función, se añade aquí y se asigna a quien corresponda.

El reparto por rol es la plantilla de partida, no una ley: desde la pantalla de
usuarios se marca y desmarca por persona.
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.permiso import Permiso, RolPermiso
from app.models.rol import Rol

# (modulo, accion, etiqueta). El orden de la lista es el del menú.
CATALOGO: list[tuple[str, str, str]] = [
    ("dashboard", "ver", "Ver el panel con las métricas"),
    ("cargos", "ver", "Ver los cargos"),
    ("cargos", "crear", "Crear cargos"),
    ("cargos", "editar", "Editar cargos"),
    ("cargos", "cambiar_estado", "Activar o desactivar un cargo"),
    ("cargos", "gestionar_catalogos", "Administrar catálogos y competencias"),
    ("vacantes", "ver", "Ver las vacantes"),
    ("vacantes", "crear", "Crear vacantes"),
    ("vacantes", "editar", "Editar vacantes"),
    ("vacantes", "cambiar_estado", "Abrir o cerrar una vacante"),
    ("vacantes", "publicar", "Publicar el post en LinkedIn"),
    ("vacantes", "enviar_interno", "Enviar la vacante por correo interno"),
    ("pipeline", "ver", "Ver el pipeline de candidatos"),
    ("pipeline", "autorizar", "Autorizar el ingreso de un candidato"),
    ("pipeline", "mover", "Mover candidatos de etapa"),
    ("contactos", "ver", "Ver el directorio de contactos"),
    ("contactos", "exportar", "Exportar el directorio"),
    ("evaluaciones", "ver", "Ver las evaluaciones"),
    ("evaluaciones", "crear", "Registrar evaluaciones"),
    ("usuarios", "ver", "Ver los usuarios"),
    ("usuarios", "crear", "Crear usuarios"),
    ("usuarios", "editar", "Editar usuarios"),
    ("usuarios", "cambiar_estado", "Activar o desactivar usuarios"),
    ("usuarios", "asignar_rol", "Asignar roles y permisos"),
    ("usuarios", "gestionar_roles", "Crear y editar roles"),
    ("configuracion", "ver", "Ver la configuración"),
    ("configuracion", "editar", "Cambiar credenciales y parámetros"),
]

# Qué trae cada rol de fábrica. `super_admin` no está: los tiene todos por definición
# y no se le pueden quitar (ver `app/core/permisos.py`).
PLANTILLA_POR_ROL: dict[str, list[str]] = {
    "reclutador": [
        "dashboard.ver",
        "cargos.ver",
        "cargos.crear",
        "cargos.editar",
        "cargos.cambiar_estado",
        "cargos.gestionar_catalogos",
        "vacantes.ver",
        "vacantes.crear",
        "vacantes.editar",
        "vacantes.cambiar_estado",
        "vacantes.publicar",
        "vacantes.enviar_interno",
        "pipeline.ver",
        "pipeline.autorizar",
        "pipeline.mover",
        "contactos.ver",
        "contactos.exportar",
        "evaluaciones.ver",
        "evaluaciones.crear",
    ],
    "entrevistador": [
        "dashboard.ver",
        "evaluaciones.ver",
        "evaluaciones.crear",
    ],
}


def clave(modulo: str, accion: str) -> str:
    return f"{modulo}.{accion}"


def sembrar_permisos(db: Session) -> None:
    """Crea los permisos que falten y asigna la plantilla a los roles que no tengan.

    Idempotente, como el resto del seed: añade lo que no está y no toca lo que sí.
    **No reasigna** a un rol que ya tiene permisos, para no deshacer lo que alguien
    haya ajustado a mano desde la pantalla.
    """
    existentes = {p.clave: p for p in db.scalars(select(Permiso)).all()}

    for orden, (modulo, accion, etiqueta) in enumerate(CATALOGO):
        k = clave(modulo, accion)
        if k in existentes:
            continue
        permiso = Permiso(clave=k, modulo=modulo, accion=accion, etiqueta=etiqueta, orden=orden)
        db.add(permiso)
        existentes[k] = permiso

    db.flush()

    for nombre_rol, claves in PLANTILLA_POR_ROL.items():
        rol = db.scalar(select(Rol).where(Rol.nombre == nombre_rol))
        if rol is None:
            continue
        ya_tiene = db.scalar(select(RolPermiso).where(RolPermiso.rol_id == rol.id))
        if ya_tiene is not None:
            continue
        for k in claves:
            permiso = existentes.get(k)
            if permiso is not None:
                db.add(RolPermiso(rol_id=rol.id, permiso_id=permiso.id))

    db.commit()
