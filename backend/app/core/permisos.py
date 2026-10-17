"""Qué puede hacer un usuario, resolviendo rol y ajustes personales.

    permisos del rol  ±  ajustes del usuario

El rol es la plantilla; el usuario admite excepciones en ambos sentidos. Un ajuste
`concedido=False` **gana** sobre el rol: quitar un permiso puntual a una persona sin
sacarla de su rol es justo el caso que motiva tener dos niveles.

`super_admin` los tiene todos y sus ajustes se ignoran. Sin esa regla, un super admin
podría quitarse a sí mismo el permiso de administrar usuarios y **dejar el sistema sin
nadie capaz de devolvérselo**.
"""

from fastapi import Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.permiso import Permiso, RolPermiso, UsuarioPermiso
from app.models.usuario import Usuario

ROL_TODOPODEROSO = "super_admin"


def permisos_de(db: Session, usuario: Usuario) -> set[str]:
    """El conjunto efectivo de claves de permiso de este usuario."""
    if usuario.rol.nombre == ROL_TODOPODEROSO:
        return set(db.scalars(select(Permiso.clave)).all())

    del_rol = set(
        db.scalars(
            select(Permiso.clave)
            .join(RolPermiso, RolPermiso.permiso_id == Permiso.id)
            .where(RolPermiso.rol_id == usuario.rol_id)
        ).all()
    )

    ajustes = db.execute(
        select(Permiso.clave, UsuarioPermiso.concedido)
        .join(UsuarioPermiso, UsuarioPermiso.permiso_id == Permiso.id)
        .where(UsuarioPermiso.usuario_id == usuario.id)
    ).all()

    for clave, concedido in ajustes:
        if concedido:
            del_rol.add(clave)
        else:
            del_rol.discard(clave)
    return del_rol


def tiene_permiso(db: Session, usuario: Usuario, clave: str) -> bool:
    return clave in permisos_de(db, usuario)


def require_permission(clave: str):
    """Dependencia de FastAPI que exige un permiso concreto.

    Convive con `require_roles`, que sigue protegiendo los endpoints que aún no se han
    migrado. Se van pasando a este a medida que los módulos se cierran; mientras tanto
    ninguno queda sin protección.
    """

    def dependencia(db: Session = Depends(get_db), usuario: Usuario = Depends(get_current_user)) -> Usuario:
        if not tiene_permiso(db, usuario, clave):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Tu rol no tiene el permiso '{clave}'",
            )
        return usuario

    return dependencia
