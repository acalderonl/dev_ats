"""departamentos: la unidad organizativa a la que pertenece cada cargo

Un cargo pertenece a exactamente un departamento (`NOT NULL`). Para que los cargos que
ya existen no queden huerfanos, la migracion crea «Sin asignar» y los pone ahi; se
reasignan despues desde la pantalla. Ese departamento va marcado `es_sistema` para que
no se pueda desactivar ni renombrar: es el sitio al que caen los cargos cuando se
desactiva su departamento.

No se confunde con la *clasificacion* del cargo, que sigue existiendo: aquella dice que
tipo de puesto es; esta dice donde esta dentro de la institucion.

Revision ID: 0009_departamentos
Revises: 0008_permisos
Create Date: 2026-11-04

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0009_departamentos"
down_revision: Union[str, None] = "0008_permisos"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

SIN_ASIGNAR = "Sin asignar"


def upgrade() -> None:
    op.create_table(
        "departamentos",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("nombre", sa.String(length=120), nullable=False, unique=True),
        sa.Column("descripcion", sa.Text(), nullable=True),
        sa.Column("activo", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("es_sistema", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("creado_en", sa.DateTime(), server_default=sa.func.now()),
    )

    op.execute(
        sa.text(
            "INSERT INTO departamentos (nombre, descripcion, es_sistema) "
            "VALUES (:nombre, :descripcion, true)"
        ).bindparams(
            nombre=SIN_ASIGNAR,
            descripcion="Cargos que todavía no tienen departamento. Reasígnalos desde Cargos.",
        )
    )

    # Primero como opcional, se rellena, y solo entonces se exige: al reves fallaria en
    # cualquier base que ya tenga cargos.
    op.add_column("cargos", sa.Column("departamento_id", sa.Integer(), nullable=True))
    op.execute(
        sa.text(
            "UPDATE cargos SET departamento_id = "
            "(SELECT id FROM departamentos WHERE nombre = :nombre)"
        ).bindparams(nombre=SIN_ASIGNAR)
    )
    op.alter_column("cargos", "departamento_id", nullable=False)
    op.create_foreign_key("fk_cargos_departamento", "cargos", "departamentos", ["departamento_id"], ["id"])
    op.create_index("ix_cargos_departamento_id", "cargos", ["departamento_id"])


def downgrade() -> None:
    op.drop_index("ix_cargos_departamento_id", table_name="cargos")
    op.drop_constraint("fk_cargos_departamento", "cargos", type_="foreignkey")
    op.drop_column("cargos", "departamento_id")
    op.drop_table("departamentos")
