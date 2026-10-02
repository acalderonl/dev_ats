"""actividades con favorito, competencias (academicas y blandas) y experiencia requerida

- `actividades` pasa de lista de textos a lista de objetos {texto, favorita}.
- Nace el catálogo `competencias` (académicas y blandas) con su tabla puente por cargo,
  donde se marca si cada una es requerida o deseada.
- `cargos.experiencia_requerida` guarda el tramo de años.

Se activa `pg_trgm` para poder sugerir competencias parecidas y evitar que se dupliquen
escritas de formas distintas.

Revision ID: 0003_competencias
Revises: 0002_cargo_estructurado
Create Date: 2026-10-01

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0003_competencias"
down_revision: Union[str, None] = "0002_cargo_estructurado"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")

    # --- Actividades: de ["texto"] a [{"texto": ..., "favorita": false}] ---
    op.execute(
        """
        UPDATE cargos SET actividades = COALESCE(
            (
                SELECT jsonb_agg(jsonb_build_object('texto', valor, 'favorita', false))
                FROM jsonb_array_elements_text(actividades) AS valor
            ),
            '[]'::jsonb
        )
        """
    )

    # --- Experiencia requerida ---
    op.add_column("cargos", sa.Column("experiencia_requerida", sa.String(length=20), nullable=True))

    # --- Competencias: un solo catálogo con tipo, porque académicas y blandas se
    #     gestionan igual y así el buscador de parecidos sirve para las dos. ---
    op.create_table(
        "competencias",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("nombre", sa.String(length=200), nullable=False),
        # Sin tildes y en minúsculas: es la columna contra la que se busca y se comparan
        # duplicados, para que "Programación" y "programacion" no convivan.
        sa.Column("nombre_normalizado", sa.String(length=200), nullable=False),
        sa.Column("tipo", sa.String(length=20), nullable=False),
        sa.Column("activo", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.UniqueConstraint("tipo", "nombre_normalizado", name="uq_competencia_tipo_nombre"),
    )
    op.create_index(
        "ix_competencias_trgm",
        "competencias",
        ["nombre_normalizado"],
        postgresql_using="gin",
        postgresql_ops={"nombre_normalizado": "gin_trgm_ops"},
    )

    op.create_table(
        "cargo_competencias",
        sa.Column("cargo_id", sa.Integer(), sa.ForeignKey("cargos.id", ondelete="CASCADE"), primary_key=True),
        sa.Column(
            "competencia_id",
            sa.Integer(),
            sa.ForeignKey("competencias.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("requerido", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column("deseado", sa.Boolean(), server_default=sa.false(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("cargo_competencias")
    op.drop_index("ix_competencias_trgm", table_name="competencias")
    op.drop_table("competencias")
    op.drop_column("cargos", "experiencia_requerida")

    op.execute(
        """
        UPDATE cargos SET actividades = COALESCE(
            (
                SELECT jsonb_agg(elemento->>'texto')
                FROM jsonb_array_elements(actividades) AS elemento
            ),
            '[]'::jsonb
        )
        """
    )
