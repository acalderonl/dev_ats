"""la vacante pasa a ser una publicacion: condiciones, post, estados y visibilidad

El titulo deja de escribirse a mano (se elige el cargo), pero la columna se queda: es
una copia del nombre del cargo al crear la vacante, porque de ella sale el `slug` que
es la URL publica. Si siguiera al catalogo, renombrar un cargo romperia los enlaces ya
repartidos.

`estado` cambia de vocabulario: 'activa' pasa a 'abierta'. Lo ya guardado se traduce.

Dos catalogos nuevos (tipos de contrato y jornadas) y una tabla de configuracion donde
viven las credenciales de LinkedIn y Gmail, cifradas.

Revision ID: 0006_vacante_pub
Revises: 0005_edu_multiple
Create Date: 2026-10-12

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0006_vacante_pub"
down_revision: Union[str, None] = "0005_edu_multiple"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


TIPOS_DE_CONTRATO_INICIALES = [
    "Indefinido",
    "Plazo fijo",
    "Eventual",
    "Por obra o servicio",
    "Pasantía",
    "Prestación de servicios profesionales",
]

JORNADAS_INICIALES = [
    ("Jornada completa (8 horas)", 8),
    ("Jornada de 6 horas", 6),
    ("Media jornada (4 horas)", 4),
]


def upgrade() -> None:
    op.create_table(
        "tipos_contrato",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("nombre", sa.String(length=100), nullable=False),
        sa.Column("activo", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("nombre"),
    )
    op.create_table(
        "jornadas",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("nombre", sa.String(length=100), nullable=False),
        sa.Column("horas", sa.Numeric(precision=4, scale=2), nullable=False),
        sa.Column("activo", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("nombre"),
    )
    op.create_table(
        "configuracion",
        sa.Column("clave", sa.String(length=100), nullable=False),
        sa.Column("valor", sa.Text(), nullable=True),
        sa.Column("es_secreto", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("actualizado_en", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("clave"),
    )
    op.create_table(
        "tokens_linkedin",
        sa.Column("usuario_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("access_token_cifrado", sa.Text(), nullable=False),
        sa.Column("persona_urn", sa.String(length=200), nullable=False),
        sa.Column("nombre_en_linkedin", sa.String(length=200), nullable=True),
        sa.Column("expira_en", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revocado", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("creado_en", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["usuario_id"], ["usuarios.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("usuario_id"),
    )

    op.bulk_insert(
        sa.table("tipos_contrato", sa.column("nombre", sa.String)),
        [{"nombre": nombre} for nombre in TIPOS_DE_CONTRATO_INICIALES],
    )
    op.bulk_insert(
        sa.table("jornadas", sa.column("nombre", sa.String), sa.column("horas", sa.Numeric)),
        [{"nombre": nombre, "horas": horas} for nombre, horas in JORNADAS_INICIALES],
    )

    # --- Condiciones del puesto ---
    op.add_column("vacantes", sa.Column("remuneracion", sa.Numeric(precision=12, scale=2), nullable=True))
    op.add_column("vacantes", sa.Column("jornada_horas", sa.Numeric(precision=4, scale=2), nullable=True))
    op.add_column("vacantes", sa.Column("hora_entrada", sa.Time(), nullable=True))
    op.add_column("vacantes", sa.Column("hora_salida", sa.Time(), nullable=True))
    op.add_column("vacantes", sa.Column("tipo_contrato_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "fk_vacantes_tipo_contrato", "vacantes", "tipos_contrato", ["tipo_contrato_id"], ["id"]
    )
    op.add_column(
        "vacantes",
        sa.Column("campos_personalizados", postgresql.JSONB(), nullable=False, server_default="[]"),
    )

    # --- La publicación ---
    op.add_column("vacantes", sa.Column("asunto", sa.String(length=200), nullable=True))
    op.add_column("vacantes", sa.Column("post_cuerpo", sa.Text(), nullable=True))
    op.add_column("vacantes", sa.Column("post_imagen_url", sa.String(length=500), nullable=True))
    op.add_column("vacantes", sa.Column("post_programado_para", sa.DateTime(timezone=True), nullable=True))
    op.add_column(
        "vacantes", sa.Column("post_estado", sa.String(length=20), nullable=False, server_default="borrador")
    )
    op.add_column("vacantes", sa.Column("post_publicado_en", sa.DateTime(timezone=True), nullable=True))
    op.add_column("vacantes", sa.Column("post_error", sa.Text(), nullable=True))

    # --- Alcance ---
    op.add_column(
        "vacantes", sa.Column("visibilidad", sa.String(length=20), nullable=False, server_default="publica")
    )
    op.add_column(
        "vacantes",
        sa.Column("destinatarios_internos", postgresql.JSONB(), nullable=False, server_default="[]"),
    )
    op.add_column("vacantes", sa.Column("enviado_internamente_en", sa.DateTime(timezone=True), nullable=True))

    # El id de post de LinkedIn real es un URN largo (urn:li:share:...): 100 se queda corto.
    op.alter_column("vacantes", "linkedin_post_id", type_=sa.String(length=200), existing_nullable=True)

    # Vocabulario de estados. Lo ya publicado estaba 'activa'; pasa a 'abierta'.
    op.execute("UPDATE vacantes SET estado = 'abierta' WHERE estado = 'activa'")
    # Una vacante que ya tenía post de LinkedIn estaba publicada, aunque la columna
    # no existiera para decirlo.
    op.execute("UPDATE vacantes SET post_estado = 'publicado' WHERE linkedin_post_id IS NOT NULL")


def downgrade() -> None:
    op.execute("UPDATE vacantes SET estado = 'activa' WHERE estado = 'abierta'")
    op.alter_column("vacantes", "linkedin_post_id", type_=sa.String(length=100), existing_nullable=True)
    for columna in (
        "enviado_internamente_en",
        "destinatarios_internos",
        "visibilidad",
        "post_error",
        "post_publicado_en",
        "post_estado",
        "post_programado_para",
        "post_imagen_url",
        "post_cuerpo",
        "asunto",
        "campos_personalizados",
    ):
        op.drop_column("vacantes", columna)
    op.drop_constraint("fk_vacantes_tipo_contrato", "vacantes", type_="foreignkey")
    for columna in ("tipo_contrato_id", "hora_salida", "hora_entrada", "jornada_horas", "remuneracion"):
        op.drop_column("vacantes", columna)
    op.drop_table("tokens_linkedin")
    op.drop_table("configuracion")
    op.drop_table("jornadas")
    op.drop_table("tipos_contrato")
