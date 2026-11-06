"""cargo estructurado: catalogos de nombre y clasificacion, mision y actividades

El nombre del cargo pasa a un catálogo (para no escribir el mismo puesto de varias
formas) y el antiguo `departamento` se convierte en `clasificacion`, también de catálogo.
`descripcion` pasa a llamarse `mision`. Se añaden `tiene_personal_a_cargo` y `actividades`.

Los datos existentes NO se pierden: los nombres y departamentos actuales se vuelcan a los
catálogos y cada cargo queda apuntando al suyo.

Revision ID: 0002_cargo_estructurado
Revises: 0001_initial
Create Date: 2026-10-01

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0002_cargo_estructurado"
down_revision: Union[str, None] = "0001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "nombres_cargo",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("nombre", sa.String(length=150), nullable=False, unique=True),
        sa.Column("activo", sa.Boolean(), server_default=sa.true(), nullable=False),
    )
    op.create_table(
        "clasificaciones_cargo",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("nombre", sa.String(length=100), nullable=False, unique=True),
        sa.Column("activo", sa.Boolean(), server_default=sa.true(), nullable=False),
    )

    # Volcar lo que ya existe a los catálogos antes de tocar la tabla de cargos.
    op.execute("INSERT INTO nombres_cargo (nombre, activo) SELECT DISTINCT nombre, true FROM cargos")
    op.execute(
        "INSERT INTO clasificaciones_cargo (nombre, activo) "
        "SELECT DISTINCT departamento, true FROM cargos WHERE departamento IS NOT NULL"
    )

    op.add_column("cargos", sa.Column("nombre_id", sa.Integer(), nullable=True))
    op.add_column("cargos", sa.Column("clasificacion_id", sa.Integer(), nullable=True))
    op.add_column(
        "cargos",
        sa.Column("tiene_personal_a_cargo", sa.Boolean(), server_default=sa.false(), nullable=False),
    )
    op.add_column("cargos", sa.Column("mision", sa.Text(), nullable=True))
    op.add_column(
        "cargos",
        sa.Column(
            "actividades",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'[]'::jsonb"),
            nullable=False,
        ),
    )

    op.execute("UPDATE cargos c SET nombre_id = n.id FROM nombres_cargo n WHERE n.nombre = c.nombre")
    op.execute(
        "UPDATE cargos c SET clasificacion_id = cl.id "
        "FROM clasificaciones_cargo cl WHERE cl.nombre = c.departamento"
    )
    op.execute("UPDATE cargos SET mision = descripcion WHERE descripcion IS NOT NULL")

    op.alter_column("cargos", "nombre_id", nullable=False)
    op.create_foreign_key("fk_cargos_nombre", "cargos", "nombres_cargo", ["nombre_id"], ["id"])
    op.create_foreign_key(
        "fk_cargos_clasificacion", "cargos", "clasificaciones_cargo", ["clasificacion_id"], ["id"]
    )

    op.drop_column("cargos", "nombre")
    op.drop_column("cargos", "departamento")
    op.drop_column("cargos", "descripcion")


def downgrade() -> None:
    op.add_column("cargos", sa.Column("nombre", sa.String(length=150), nullable=True))
    op.add_column("cargos", sa.Column("departamento", sa.String(length=100), nullable=True))
    op.add_column("cargos", sa.Column("descripcion", sa.Text(), nullable=True))

    op.execute("UPDATE cargos c SET nombre = n.nombre FROM nombres_cargo n WHERE n.id = c.nombre_id")
    op.execute(
        "UPDATE cargos c SET departamento = cl.nombre "
        "FROM clasificaciones_cargo cl WHERE cl.id = c.clasificacion_id"
    )
    op.execute("UPDATE cargos SET descripcion = mision WHERE mision IS NOT NULL")
    op.alter_column("cargos", "nombre", nullable=False)

    op.drop_constraint("fk_cargos_clasificacion", "cargos", type_="foreignkey")
    op.drop_constraint("fk_cargos_nombre", "cargos", type_="foreignkey")
    op.drop_column("cargos", "actividades")
    op.drop_column("cargos", "mision")
    op.drop_column("cargos", "tiene_personal_a_cargo")
    op.drop_column("cargos", "clasificacion_id")
    op.drop_column("cargos", "nombre_id")

    op.drop_table("clasificaciones_cargo")
    op.drop_table("nombres_cargo")
