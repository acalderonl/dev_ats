import uuid
from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Postulante(Base):
    """Perfil del candidato.

    Los campos siguen el esquema que pidió el dueño (ver
    `docs/resouces/ESQUEMA FORMULARIO PARA APLICANTE ATS.docx`): datos personales
    aquí, y educación, idiomas y experiencia en tablas aparte porque son listas.

    `nivel_instruccion` se queda aunque la educación tenga ya su propia tabla: lo usa
    el filtro del directorio de contactos, y resolverlo con una subconsulta a la tabla
    en cada búsqueda sería más caro que mantener este resumen.
    """

    __tablename__ = "postulantes"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # --- Identidad ---
    nombres: Mapped[str] = mapped_column(String(100), nullable=False)
    apellidos: Mapped[str] = mapped_column(String(100), nullable=False)
    tipo_documento: Mapped[str | None] = mapped_column(String(50), nullable=True)
    cedula: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    fecha_nacimiento: Mapped[date | None] = mapped_column(Date, nullable=True)
    genero: Mapped[str | None] = mapped_column(String(30), nullable=True)
    nacionalidad: Mapped[str | None] = mapped_column(String(100), nullable=True)
    foto_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # --- Contacto ---
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    telefono_codigo_pais: Mapped[str | None] = mapped_column(String(10), nullable=True)
    telefono: Mapped[str | None] = mapped_column(String(50), nullable=True)
    telefono_tipo: Mapped[str | None] = mapped_column(String(30), nullable=True)
    pais_residencia: Mapped[str | None] = mapped_column(String(100), nullable=True)
    provincia: Mapped[str | None] = mapped_column(String(100), nullable=True)
    localidad: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # --- Resumen y extras ---
    # Se mantiene por el filtro del directorio de contactos. Ver el comentario de arriba.
    nivel_instruccion: Mapped[str | None] = mapped_column(String(100), nullable=True)
    estudios_secundarios_completos: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    linkedin_url: Mapped[str | None] = mapped_column(String(300), nullable=True)
    # [{"red": "GitHub", "url": "..."}]: las redes que no son LinkedIn son una lista
    # abierta que no merece una tabla.
    otras_redes: Mapped[list] = mapped_column(JSONB, default=list, nullable=False)
    expectativas: Mapped[str | None] = mapped_column(Text, nullable=True)

    cv_documento_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # --- Consentimiento ---
    # Cuándo aceptó, no solo que aceptó: sin la fecha no se puede demostrar qué
    # versión de la política aceptó.
    acepto_privacidad_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # --- Trazabilidad del llenado automático ---
    # De dónde salieron los datos: 'manual' o 'cv'. Importa para saber si una ficha
    # la revisó una persona o la rellenó la extracción sin que nadie la mirara.
    origen_datos: Mapped[str] = mapped_column(String(20), default="manual", nullable=False)

    edad: Mapped[int | None] = mapped_column(Integer, nullable=True)
    creado_en: Mapped[datetime] = mapped_column(server_default=func.now())

    educacion: Mapped[list["PostulanteEducacion"]] = relationship(  # noqa: F821
        back_populates="postulante", cascade="all, delete-orphan", order_by="PostulanteEducacion.orden"
    )
    idiomas: Mapped[list["PostulanteIdioma"]] = relationship(  # noqa: F821
        back_populates="postulante", cascade="all, delete-orphan", order_by="PostulanteIdioma.orden"
    )
    experiencia: Mapped[list["PostulanteExperiencia"]] = relationship(  # noqa: F821
        back_populates="postulante", cascade="all, delete-orphan", order_by="PostulanteExperiencia.orden"
    )
    postulaciones: Mapped[list["Postulacion"]] = relationship(back_populates="postulante")  # noqa: F821
