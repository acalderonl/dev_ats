"""perfil completo del postulante: datos personales, educacion, idiomas y experiencia

El formulario de postulacion pasa de 12 campos a los ~40 del esquema que pidio el
dueno (docs/resouces/ESQUEMA FORMULARIO PARA APLICANTE ATS.docx).

Educacion, idiomas y experiencia salen de columnas JSONB a tablas propias: dejaron de
ser un apunte y son datos que hay que filtrar y buscar. Lo que hubiera en
`experiencia_laboral` se copia antes de borrar la columna.

Las fechas van en mes y anio por separado. Un CV dice "Junio 2019", no un dia
concreto: componer una fecha completa seria precision inventada.

Revision ID: 0007_perfil_postulante
Revises: 0006_vacante_pub
Create Date: 2026-10-14

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0007_perfil_postulante"
down_revision: Union[str, None] = "0006_vacante_pub"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _columnas_de_fila() -> list[sa.Column]:
    return [
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("postulante_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("orden", sa.Integer(), nullable=False, server_default="0"),
    ]


def upgrade() -> None:
    # --- Datos personales ---
    for nombre, tipo in (
        ("tipo_documento", sa.String(length=50)),
        ("genero", sa.String(length=30)),
        ("nacionalidad", sa.String(length=100)),
        ("foto_url", sa.String(length=500)),
        ("telefono_codigo_pais", sa.String(length=10)),
        ("telefono_tipo", sa.String(length=30)),
        ("pais_residencia", sa.String(length=100)),
        ("provincia", sa.String(length=100)),
        ("localidad", sa.String(length=100)),
        ("linkedin_url", sa.String(length=300)),
    ):
        op.add_column("postulantes", sa.Column(nombre, tipo, nullable=True))

    op.add_column("postulantes", sa.Column("fecha_nacimiento", sa.Date(), nullable=True))
    op.add_column("postulantes", sa.Column("estudios_secundarios_completos", sa.Boolean(), nullable=True))
    op.add_column("postulantes", sa.Column("expectativas", sa.Text(), nullable=True))
    op.add_column("postulantes", sa.Column("acepto_privacidad_en", sa.DateTime(timezone=True), nullable=True))
    op.add_column(
        "postulantes", sa.Column("otras_redes", postgresql.JSONB(), nullable=False, server_default="[]")
    )
    op.add_column(
        "postulantes", sa.Column("origen_datos", sa.String(length=20), nullable=False, server_default="manual")
    )

    # El CV ya no es obligatorio al crear la ficha: el candidato puede rellenar el
    # formulario a mano sin subir nada.
    op.alter_column("postulantes", "cv_documento_url", existing_type=sa.String(length=500), nullable=True)

    # --- Las tres listas ---
    op.create_table(
        "postulante_educacion",
        *_columnas_de_fila(),
        sa.Column("titulo", sa.String(length=250), nullable=True),
        sa.Column("pais", sa.String(length=100), nullable=True),
        sa.Column("institucion", sa.String(length=250), nullable=True),
        sa.Column("area_estudio", sa.String(length=150), nullable=True),
        sa.Column("nivel_estudio", sa.String(length=100), nullable=True),
        sa.Column("estado_estudio", sa.String(length=50), nullable=True),
        sa.Column("inicio_mes", sa.Integer(), nullable=True),
        sa.Column("inicio_anio", sa.Integer(), nullable=True),
        sa.Column("actualmente", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("fin_mes", sa.Integer(), nullable=True),
        sa.Column("fin_anio", sa.Integer(), nullable=True),
        sa.Column("descripcion", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["postulante_id"], ["postulantes.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_postulante_educacion_postulante_id", "postulante_educacion", ["postulante_id"])

    op.create_table(
        "postulante_idiomas",
        *_columnas_de_fila(),
        sa.Column("idioma", sa.String(length=100), nullable=False),
        sa.Column("nivel_escrito", sa.String(length=50), nullable=True),
        sa.Column("nivel_oral", sa.String(length=50), nullable=True),
        sa.ForeignKeyConstraint(["postulante_id"], ["postulantes.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_postulante_idiomas_postulante_id", "postulante_idiomas", ["postulante_id"])

    op.create_table(
        "postulante_experiencia",
        *_columnas_de_fila(),
        sa.Column("puesto", sa.String(length=250), nullable=True),
        sa.Column("jerarquia", sa.String(length=50), nullable=True),
        sa.Column("empresa", sa.String(length=250), nullable=True),
        sa.Column("pais", sa.String(length=100), nullable=True),
        sa.Column("industria", sa.String(length=150), nullable=True),
        sa.Column("area_trabajo", sa.String(length=150), nullable=True),
        sa.Column("subarea_trabajo", sa.String(length=150), nullable=True),
        sa.Column("inicio_mes", sa.Integer(), nullable=True),
        sa.Column("inicio_anio", sa.Integer(), nullable=True),
        sa.Column("actualmente", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("fin_mes", sa.Integer(), nullable=True),
        sa.Column("fin_anio", sa.Integer(), nullable=True),
        sa.Column("descripcion", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["postulante_id"], ["postulantes.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_postulante_experiencia_postulante_id", "postulante_experiencia", ["postulante_id"])

    # Lo que haya en el JSONB viejo se copia antes de borrarlo. `->>` saca el texto;
    # las claves son las del esquema anterior (`empresa`, `cargo`, `descripcion`).
    op.execute(
        """
        INSERT INTO postulante_experiencia (postulante_id, orden, empresa, puesto, descripcion, actualmente)
        SELECT p.id,
               fila.orden - 1,
               fila.valor ->> 'empresa',
               fila.valor ->> 'cargo',
               fila.valor ->> 'descripcion',
               false
        FROM postulantes p
        CROSS JOIN LATERAL jsonb_array_elements(p.experiencia_laboral) WITH ORDINALITY AS fila(valor, orden)
        WHERE p.experiencia_laboral IS NOT NULL
          AND jsonb_typeof(p.experiencia_laboral) = 'array'
        """
    )

    for columna in ("formacion_secundaria", "formacion_superior", "titulos", "experiencia_laboral"):
        op.drop_column("postulantes", columna)


def downgrade() -> None:
    op.add_column("postulantes", sa.Column("experiencia_laboral", postgresql.JSONB(), nullable=True))
    op.add_column("postulantes", sa.Column("titulos", postgresql.ARRAY(sa.Text()), nullable=True))
    op.add_column("postulantes", sa.Column("formacion_superior", postgresql.JSONB(), nullable=True))
    op.add_column("postulantes", sa.Column("formacion_secundaria", postgresql.JSONB(), nullable=True))

    op.drop_table("postulante_experiencia")
    op.drop_table("postulante_idiomas")
    op.drop_table("postulante_educacion")

    op.alter_column("postulantes", "cv_documento_url", existing_type=sa.String(length=500), nullable=False)
    for columna in (
        "origen_datos",
        "otras_redes",
        "acepto_privacidad_en",
        "expectativas",
        "estudios_secundarios_completos",
        "fecha_nacimiento",
        "linkedin_url",
        "localidad",
        "provincia",
        "pais_residencia",
        "telefono_tipo",
        "telefono_codigo_pais",
        "foto_url",
        "nacionalidad",
        "genero",
        "tipo_documento",
    ):
        op.drop_column("postulantes", columna)
