"""educacion formal requerida: niveles, titulos y areas academicas

Tres catálogos nuevos para la sección 4 del cargo, más las columnas que los referencian.
`estado_educacion` guarda si el nivel se exige completo o en curso.

Revision ID: 0004_educacion
Revises: 0003_competencias
Create Date: 2026-10-01

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0004_educacion"
down_revision: Union[str, None] = "0003_competencias"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_CATALOGOS = ["niveles_educacion", "titulos_academicos", "areas_academicas"]


def upgrade() -> None:
    for tabla in _CATALOGOS:
        op.create_table(
            tabla,
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("nombre", sa.String(length=200), nullable=False, unique=True),
            sa.Column("activo", sa.Boolean(), server_default=sa.true(), nullable=False),
        )

    op.add_column("cargos", sa.Column("nivel_educacion_id", sa.Integer(), nullable=True))
    op.add_column("cargos", sa.Column("estado_educacion", sa.String(length=20), nullable=True))
    op.add_column("cargos", sa.Column("titulo_id", sa.Integer(), nullable=True))
    op.add_column("cargos", sa.Column("area_academica_id", sa.Integer(), nullable=True))

    op.create_foreign_key("fk_cargos_nivel_educacion", "cargos", "niveles_educacion", ["nivel_educacion_id"], ["id"])
    op.create_foreign_key("fk_cargos_titulo", "cargos", "titulos_academicos", ["titulo_id"], ["id"])
    op.create_foreign_key("fk_cargos_area", "cargos", "areas_academicas", ["area_academica_id"], ["id"])


def downgrade() -> None:
    op.drop_constraint("fk_cargos_area", "cargos", type_="foreignkey")
    op.drop_constraint("fk_cargos_titulo", "cargos", type_="foreignkey")
    op.drop_constraint("fk_cargos_nivel_educacion", "cargos", type_="foreignkey")

    op.drop_column("cargos", "area_academica_id")
    op.drop_column("cargos", "titulo_id")
    op.drop_column("cargos", "estado_educacion")
    op.drop_column("cargos", "nivel_educacion_id")

    for tabla in reversed(_CATALOGOS):
        op.drop_table(tabla)
