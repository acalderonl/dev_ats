"""esquema inicial del sistema ATS

Revision ID: 0001_initial
Revises:
Create Date: 2026-09-28

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "roles",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("nombre", sa.String(length=50), nullable=False, unique=True),
        sa.Column("descripcion", sa.Text(), nullable=True),
    )

    op.create_table(
        "usuarios",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(length=255), nullable=False, unique=True),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("nombres", sa.String(length=100), nullable=False),
        sa.Column("apellidos", sa.String(length=100), nullable=False),
        sa.Column("rol_id", sa.Integer(), sa.ForeignKey("roles.id"), nullable=False),
        sa.Column("activo", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column("creado_en", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_usuarios_email", "usuarios", ["email"])

    op.create_table(
        "cargos",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("nombre", sa.String(length=150), nullable=False),
        sa.Column("departamento", sa.String(length=100), nullable=True),
        sa.Column("descripcion", sa.Text(), nullable=True),
        sa.Column("activo", sa.Boolean(), server_default=sa.true(), nullable=False),
    )

    op.create_table(
        "preguntas_filtro",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("cargo_id", sa.Integer(), sa.ForeignKey("cargos.id", ondelete="CASCADE"), nullable=False),
        sa.Column("pregunta", sa.Text(), nullable=False),
        sa.Column("tipo_respuesta", sa.String(length=50), nullable=False),
        sa.Column("opciones", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("es_eliminatoria", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column("respuesta_correcta", sa.Text(), nullable=True),
    )

    op.create_table(
        "vacantes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("titulo", sa.String(length=200), nullable=False),
        sa.Column("cargo_id", sa.Integer(), sa.ForeignKey("cargos.id"), nullable=False),
        sa.Column("descripcion", sa.Text(), nullable=False),
        sa.Column("documento_adjunto_url", sa.String(length=500), nullable=True),
        sa.Column("slug", sa.String(length=250), nullable=False, unique=True),
        sa.Column("fecha_limite", sa.DateTime(timezone=True), nullable=False),
        sa.Column("linkedin_post_id", sa.String(length=100), nullable=True),
        sa.Column("empleador_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("usuarios.id"), nullable=False),
        sa.Column("estado", sa.String(length=50), server_default="activa", nullable=False),
        sa.Column("creado_en", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_vacantes_slug", "vacantes", ["slug"])

    op.create_table(
        "postulantes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("nombres", sa.String(length=100), nullable=False),
        sa.Column("apellidos", sa.String(length=100), nullable=False),
        sa.Column("cedula", sa.String(length=20), nullable=False, unique=True),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("telefono", sa.String(length=50), nullable=True),
        sa.Column("edad", sa.Integer(), nullable=True),
        sa.Column("formacion_secundaria", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("formacion_superior", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("nivel_instruccion", sa.String(length=100), nullable=True),
        sa.Column("titulos", postgresql.ARRAY(sa.Text()), nullable=True),
        sa.Column("experiencia_laboral", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("cv_documento_url", sa.String(length=500), nullable=False),
        sa.Column("creado_en", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_postulantes_cedula", "postulantes", ["cedula"])

    op.create_table(
        "postulaciones",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("vacante_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("vacantes.id"), nullable=False),
        sa.Column("postulante_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("postulantes.id"), nullable=False),
        sa.Column("respuestas_filtro", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("autorizado_por", postgresql.UUID(as_uuid=True), sa.ForeignKey("usuarios.id"), nullable=True),
        sa.Column("fecha_autorizacion", sa.DateTime(timezone=True), nullable=True),
        sa.Column("estado_pipeline", sa.String(length=50), server_default="pendiente_autorizacion", nullable=False),
        sa.Column("origen", sa.String(length=20), server_default="Directo", nullable=False),
        sa.Column("match_score", sa.Numeric(5, 2), nullable=True),
        sa.Column("creado_en", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "evaluaciones",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "postulacion_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("postulaciones.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("evaluador_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("usuarios.id"), nullable=False),
        sa.Column("tipo_evaluacion", sa.String(length=100), nullable=False),
        sa.Column("puntaje", sa.Numeric(5, 2), nullable=True),
        sa.Column("observaciones", sa.Text(), nullable=True),
        sa.Column("creado_en", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("evaluaciones")
    op.drop_table("postulaciones")
    op.drop_index("ix_postulantes_cedula", table_name="postulantes")
    op.drop_table("postulantes")
    op.drop_index("ix_vacantes_slug", table_name="vacantes")
    op.drop_table("vacantes")
    op.drop_table("preguntas_filtro")
    op.drop_table("cargos")
    op.drop_index("ix_usuarios_email", table_name="usuarios")
    op.drop_table("usuarios")
    op.drop_table("roles")
