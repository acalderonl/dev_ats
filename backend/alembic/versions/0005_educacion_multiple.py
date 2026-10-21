"""educacion formal: hasta dos niveles, titulos y areas; checklist de experiencia

La sección 4 pasa de un valor por campo a una lista (tope de dos, validado en el esquema),
así que los cuatro campos sueltos de `cargos` se mudan a tres tablas. Lo ya guardado se
copia antes de borrar las columnas.

La sección 7 suma tres exigencias sueltas: experiencia en empresas similares, en cargos
similares y experiencia interna en otros cargos.

Revision ID: 0005_edu_multiple
Revises: 0004_educacion
Create Date: 2026-10-12

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0005_edu_multiple"
down_revision: Union[str, None] = "0004_educacion"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "cargo_niveles_educacion",
        sa.Column("cargo_id", sa.Integer(), sa.ForeignKey("cargos.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("nivel_id", sa.Integer(), sa.ForeignKey("niveles_educacion.id"), primary_key=True),
        sa.Column("estado", sa.String(length=20), server_default="completa", nullable=False),
        sa.Column("orden", sa.Integer(), server_default="0", nullable=False),
    )
    op.create_table(
        "cargo_titulos",
        sa.Column("cargo_id", sa.Integer(), sa.ForeignKey("cargos.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("titulo_id", sa.Integer(), sa.ForeignKey("titulos_academicos.id"), primary_key=True),
        sa.Column("orden", sa.Integer(), server_default="0", nullable=False),
    )
    op.create_table(
        "cargo_areas_academicas",
        sa.Column("cargo_id", sa.Integer(), sa.ForeignKey("cargos.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("area_id", sa.Integer(), sa.ForeignKey("areas_academicas.id"), primary_key=True),
        sa.Column("orden", sa.Integer(), server_default="0", nullable=False),
    )

    # Mudar lo que ya estaba guardado, antes de borrar las columnas de origen.
    op.execute(
        """
        INSERT INTO cargo_niveles_educacion (cargo_id, nivel_id, estado, orden)
        SELECT id, nivel_educacion_id, COALESCE(estado_educacion, 'completa'), 0
        FROM cargos WHERE nivel_educacion_id IS NOT NULL
        """
    )
    op.execute(
        """
        INSERT INTO cargo_titulos (cargo_id, titulo_id, orden)
        SELECT id, titulo_id, 0 FROM cargos WHERE titulo_id IS NOT NULL
        """
    )
    op.execute(
        """
        INSERT INTO cargo_areas_academicas (cargo_id, area_id, orden)
        SELECT id, area_academica_id, 0 FROM cargos WHERE area_academica_id IS NOT NULL
        """
    )

    op.drop_constraint("fk_cargos_area", "cargos", type_="foreignkey")
    op.drop_constraint("fk_cargos_titulo", "cargos", type_="foreignkey")
    op.drop_constraint("fk_cargos_nivel_educacion", "cargos", type_="foreignkey")
    op.drop_column("cargos", "area_academica_id")
    op.drop_column("cargos", "titulo_id")
    op.drop_column("cargos", "estado_educacion")
    op.drop_column("cargos", "nivel_educacion_id")

    for columna in (
        "experiencia_empresas_similares",
        "experiencia_cargos_similares",
        "experiencia_interna_otros_cargos",
    ):
        op.add_column("cargos", sa.Column(columna, sa.Boolean(), server_default=sa.false(), nullable=False))


def downgrade() -> None:
    for columna in (
        "experiencia_interna_otros_cargos",
        "experiencia_cargos_similares",
        "experiencia_empresas_similares",
    ):
        op.drop_column("cargos", columna)

    op.add_column("cargos", sa.Column("nivel_educacion_id", sa.Integer(), nullable=True))
    op.add_column("cargos", sa.Column("estado_educacion", sa.String(length=20), nullable=True))
    op.add_column("cargos", sa.Column("titulo_id", sa.Integer(), nullable=True))
    op.add_column("cargos", sa.Column("area_academica_id", sa.Integer(), nullable=True))

    # Al volver atrás solo cabe uno por campo: se conserva el primero de cada lista.
    op.execute(
        """
        UPDATE cargos c SET nivel_educacion_id = e.nivel_id, estado_educacion = e.estado
        FROM cargo_niveles_educacion e WHERE e.cargo_id = c.id AND e.orden = 0
        """
    )
    op.execute(
        "UPDATE cargos c SET titulo_id = t.titulo_id FROM cargo_titulos t "
        "WHERE t.cargo_id = c.id AND t.orden = 0"
    )
    op.execute(
        "UPDATE cargos c SET area_academica_id = a.area_id FROM cargo_areas_academicas a "
        "WHERE a.cargo_id = c.id AND a.orden = 0"
    )

    op.create_foreign_key("fk_cargos_nivel_educacion", "cargos", "niveles_educacion", ["nivel_educacion_id"], ["id"])
    op.create_foreign_key("fk_cargos_titulo", "cargos", "titulos_academicos", ["titulo_id"], ["id"])
    op.create_foreign_key("fk_cargos_area", "cargos", "areas_academicas", ["area_academica_id"], ["id"])

    op.drop_table("cargo_areas_academicas")
    op.drop_table("cargo_titulos")
    op.drop_table("cargo_niveles_educacion")
