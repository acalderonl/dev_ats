"""Permisos del sistema: qué se puede hacer, quién lo puede hacer.

El catálogo sale del **menú lateral**: un permiso por cada acción real dentro de cada
item. No se inventan permisos para cosas que la aplicación todavía no hace; la lista
crece con los módulos (`app/seed_permisos.py`).

Cómo se resuelve lo que puede un usuario:

    permisos del rol  (la plantilla)
    ± ajustes del propio usuario  (concedido=True suma, concedido=False quita)

El rol da el punto de partida y el usuario admite excepciones, que es lo que pidió el
dueño: poder marcar y desmarcar por usuario. Un `super_admin` los tiene todos siempre
y no admite ajustes: si se le pudieran quitar, alguien podría dejarse fuera de su
propio sistema sin forma de volver a entrar.
"""

import uuid

from sqlalchemy import Boolean, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Permiso(Base):
    __tablename__ = "permisos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    # 'vacantes.crear': el módulo es el item del menú y la acción, lo que se hace dentro.
    clave: Mapped[str] = mapped_column(String(80), unique=True, nullable=False, index=True)
    modulo: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    accion: Mapped[str] = mapped_column(String(40), nullable=False)
    etiqueta: Mapped[str] = mapped_column(String(150), nullable=False)
    orden: Mapped[int] = mapped_column(Integer, default=0, nullable=False)


class RolPermiso(Base):
    """Lo que trae un rol por defecto."""

    __tablename__ = "rol_permisos"

    rol_id: Mapped[int] = mapped_column(ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True)
    permiso_id: Mapped[int] = mapped_column(ForeignKey("permisos.id", ondelete="CASCADE"), primary_key=True)


class UsuarioPermiso(Base):
    """La excepción de una persona concreta respecto a su rol.

    `concedido` tiene tres estados en la práctica: no hay fila (lo que diga el rol),
    fila con True (se le da aunque el rol no lo tenga) y fila con False (se le quita
    aunque el rol sí lo tenga). Sin el False no se podría quitar un permiso puntual
    sin sacar a la persona de su rol.
    """

    __tablename__ = "usuario_permisos"
    __table_args__ = (UniqueConstraint("usuario_id", "permiso_id", name="uq_usuario_permiso"),)

    usuario_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("usuarios.id", ondelete="CASCADE"), primary_key=True
    )
    permiso_id: Mapped[int] = mapped_column(ForeignKey("permisos.id", ondelete="CASCADE"), primary_key=True)
    concedido: Mapped[bool] = mapped_column(Boolean, nullable=False)

    permiso: Mapped["Permiso"] = relationship()
