"""permisos por modulo y accion, con plantilla por rol y ajustes por usuario

Los permisos estaban escritos a mano en cada endpoint (`require_roles("...")`), asi
que no se podian administrar. Pasan a la base como catalogo, con dos niveles: lo que
trae un rol de fabrica y las excepciones de cada persona.

Los tres roles iniciales se marcan `es_sistema`: el codigo todavia los nombra, asi que
renombrarlos dejaria endpoints sin dejar pasar a nadie y sin error visible.

Revision ID: 0008_permisos
Revises: 0007_perfil_postulante
Create Date: 2026-10-16

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0008_permisos"
down_revision: Union[str, None] = "0007_perfil_postulante"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

ROLES_DE_SISTEMA = ("super_admin", "reclutador", "entrevistador")


def upgrade() -> None:
    op.add_column("roles", sa.Column("es_sistema", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("roles", sa.Column("activo", sa.Boolean(), nullable=False, server_default=sa.true()))
    op.execute(
        "UPDATE roles SET es_sistema = true WHERE nombre IN "
        f"({', '.join(repr(r) for r in ROLES_DE_SISTEMA)})"
    )

    op.create_table(
        "permisos",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("clave", sa.String(length=80), nullable=False),
        sa.Column("modulo", sa.String(length=40), nullable=False),
        sa.Column("accion", sa.String(length=40), nullable=False),
        sa.Column("etiqueta", sa.String(length=150), nullable=False),
        sa.Column("orden", sa.Integer(), nullable=False, server_default="0"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("clave"),
    )
    op.create_index("ix_permisos_clave", "permisos", ["clave"])
    op.create_index("ix_permisos_modulo", "permisos", ["modulo"])

    op.create_table(
        "rol_permisos",
        sa.Column("rol_id", sa.Integer(), nullable=False),
        sa.Column("permiso_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["rol_id"], ["roles.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["permiso_id"], ["permisos.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("rol_id", "permiso_id"),
    )

    op.create_table(
        "usuario_permisos",
        sa.Column("usuario_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("permiso_id", sa.Integer(), nullable=False),
        sa.Column("concedido", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(["usuario_id"], ["usuarios.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["permiso_id"], ["permisos.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("usuario_id", "permiso_id"),
        sa.UniqueConstraint("usuario_id", "permiso_id", name="uq_usuario_permiso"),
    )


def downgrade() -> None:
    op.drop_table("usuario_permisos")
    op.drop_table("rol_permisos")
    op.drop_index("ix_permisos_modulo", table_name="permisos")
    op.drop_index("ix_permisos_clave", table_name="permisos")
    op.drop_table("permisos")
    op.drop_column("roles", "activo")
    op.drop_column("roles", "es_sistema")
