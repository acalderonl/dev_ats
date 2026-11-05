"""convocatorias: el ciclo de una vacante sale de la vacante y cuelga de la convocatoria

Una vacante se convoca varias veces. Lo que cambia entre una vez y otra -hasta cuando se
reciben postulaciones, en que estado va, el post, el enlace publico y los postulantes-
pasa a la tabla `convocatorias`. La vacante se queda con las condiciones del puesto.

Para no perder nada, a cada vacante existente se le crea su **convocatoria 1** con los
datos que tenia (incluido el mismo `slug`, para que los enlaces ya repartidos sigan
funcionando) y las postulaciones se reapuntan a ella. Solo despues se quitan las
columnas de la vacante.

La regla "una persona, una vez por convocatoria" la aplica el endpoint y no una
restriccion aqui: los datos anteriores podian tenerla repetida y la migracion habria
fallado a mitad de camino.

Revision ID: 0010_convocatorias
Revises: 0009_departamentos
Create Date: 2026-11-04

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0010_convocatorias"
down_revision: Union[str, None] = "0009_departamentos"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Lo que se muda de `vacantes` a `convocatorias`, tal cual se llama en las dos.
COLUMNAS_QUE_SE_MUDAN = (
    "fecha_limite",
    "estado",
    "slug",
    "asunto",
    "post_cuerpo",
    "post_imagen_url",
    "post_programado_para",
    "post_estado",
    "post_publicado_en",
    "post_error",
    "linkedin_post_id",
    "enviado_internamente_en",
)


def upgrade() -> None:
    op.create_table(
        "convocatorias",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("vacante_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("vacantes.id"), nullable=False),
        sa.Column("numero", sa.Integer(), nullable=False),
        sa.Column("fecha_limite", sa.DateTime(timezone=True), nullable=False),
        sa.Column("estado", sa.String(length=20), nullable=False, server_default="borrador"),
        sa.Column("slug", sa.String(length=250), nullable=False),
        sa.Column("asunto", sa.String(length=200), nullable=True),
        sa.Column("post_cuerpo", sa.Text(), nullable=True),
        sa.Column("post_imagen_url", sa.String(length=500), nullable=True),
        sa.Column("post_programado_para", sa.DateTime(timezone=True), nullable=True),
        sa.Column("post_estado", sa.String(length=20), nullable=False, server_default="borrador"),
        sa.Column("post_publicado_en", sa.DateTime(timezone=True), nullable=True),
        sa.Column("post_error", sa.Text(), nullable=True),
        sa.Column("linkedin_post_id", sa.String(length=200), nullable=True),
        sa.Column("enviado_internamente_en", sa.DateTime(timezone=True), nullable=True),
        sa.Column("creado_por", postgresql.UUID(as_uuid=True), sa.ForeignKey("usuarios.id"), nullable=True),
        sa.Column("creado_en", sa.DateTime(), server_default=sa.func.now()),
        sa.UniqueConstraint("vacante_id", "numero", name="uq_convocatoria_numero_por_vacante"),
        sa.UniqueConstraint("slug", name="uq_convocatorias_slug"),
    )
    op.create_index("ix_convocatorias_vacante_id", "convocatorias", ["vacante_id"])
    op.create_index("ix_convocatorias_slug", "convocatorias", ["slug"])

    # La convocatoria 1 de cada vacante, con lo que la vacante ya tenia. `gen_random_uuid`
    # viene en PostgreSQL 13+ sin extensiones.
    columnas = ", ".join(COLUMNAS_QUE_SE_MUDAN)
    op.execute(
        f"INSERT INTO convocatorias (id, vacante_id, numero, {columnas}, creado_por, creado_en) "
        f"SELECT gen_random_uuid(), id, 1, {columnas}, empleador_id, creado_en FROM vacantes"
    )

    # Las postulaciones pasan a colgar de esa convocatoria 1.
    op.add_column("postulaciones", sa.Column("convocatoria_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.execute(
        "UPDATE postulaciones p SET convocatoria_id = c.id "
        "FROM convocatorias c WHERE c.vacante_id = p.vacante_id AND c.numero = 1"
    )
    op.alter_column("postulaciones", "convocatoria_id", nullable=False)
    op.create_foreign_key(
        "fk_postulaciones_convocatoria", "postulaciones", "convocatorias", ["convocatoria_id"], ["id"]
    )
    op.create_index("ix_postulaciones_convocatoria_id", "postulaciones", ["convocatoria_id"])
    op.drop_constraint("postulaciones_vacante_id_fkey", "postulaciones", type_="foreignkey")
    op.drop_column("postulaciones", "vacante_id")

    # La vacante se queda con las condiciones; lo demas ya vive en la convocatoria.
    op.add_column("vacantes", sa.Column("activa", sa.Boolean(), nullable=False, server_default=sa.true()))
    for columna in COLUMNAS_QUE_SE_MUDAN:
        op.drop_column("vacantes", columna)


def downgrade() -> None:
    # Se devuelve lo de la convocatoria 1; las demas convocatorias se pierden. Es lo
    # mas que se puede prometer al deshacer una tabla que no existia.
    op.add_column("vacantes", sa.Column("fecha_limite", sa.DateTime(timezone=True), nullable=True))
    op.add_column("vacantes", sa.Column("estado", sa.String(length=50), nullable=False, server_default="borrador"))
    op.add_column("vacantes", sa.Column("slug", sa.String(length=250), nullable=True))
    op.add_column("vacantes", sa.Column("asunto", sa.String(length=200), nullable=True))
    op.add_column("vacantes", sa.Column("post_cuerpo", sa.Text(), nullable=True))
    op.add_column("vacantes", sa.Column("post_imagen_url", sa.String(length=500), nullable=True))
    op.add_column("vacantes", sa.Column("post_programado_para", sa.DateTime(timezone=True), nullable=True))
    op.add_column("vacantes", sa.Column("post_estado", sa.String(length=20), nullable=False, server_default="borrador"))
    op.add_column("vacantes", sa.Column("post_publicado_en", sa.DateTime(timezone=True), nullable=True))
    op.add_column("vacantes", sa.Column("post_error", sa.Text(), nullable=True))
    op.add_column("vacantes", sa.Column("linkedin_post_id", sa.String(length=200), nullable=True))
    op.add_column("vacantes", sa.Column("enviado_internamente_en", sa.DateTime(timezone=True), nullable=True))
    asignaciones = ", ".join(f"{c} = c.{c}" for c in COLUMNAS_QUE_SE_MUDAN)
    op.execute(f"UPDATE vacantes v SET {asignaciones} FROM convocatorias c WHERE c.vacante_id = v.id AND c.numero = 1")
    op.alter_column("vacantes", "fecha_limite", nullable=False)
    op.alter_column("vacantes", "slug", nullable=False)
    op.create_unique_constraint("vacantes_slug_key", "vacantes", ["slug"])
    op.drop_column("vacantes", "activa")

    op.add_column("postulaciones", sa.Column("vacante_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.execute(
        "UPDATE postulaciones p SET vacante_id = c.vacante_id FROM convocatorias c WHERE c.id = p.convocatoria_id"
    )
    op.alter_column("postulaciones", "vacante_id", nullable=False)
    op.create_foreign_key("postulaciones_vacante_id_fkey", "postulaciones", "vacantes", ["vacante_id"], ["id"])
    op.drop_index("ix_postulaciones_convocatoria_id", table_name="postulaciones")
    op.drop_constraint("fk_postulaciones_convocatoria", "postulaciones", type_="foreignkey")
    op.drop_column("postulaciones", "convocatoria_id")

    op.drop_index("ix_convocatorias_slug", table_name="convocatorias")
    op.drop_index("ix_convocatorias_vacante_id", table_name="convocatorias")
    op.drop_table("convocatorias")
