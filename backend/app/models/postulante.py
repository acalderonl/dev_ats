import uuid
from datetime import datetime

from sqlalchemy import ARRAY, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Postulante(Base):
    __tablename__ = "postulantes"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nombres: Mapped[str] = mapped_column(String(100), nullable=False)
    apellidos: Mapped[str] = mapped_column(String(100), nullable=False)
    cedula: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    telefono: Mapped[str | None] = mapped_column(String(50), nullable=True)
    edad: Mapped[int | None] = mapped_column(Integer, nullable=True)
    formacion_secundaria: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    formacion_superior: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    nivel_instruccion: Mapped[str | None] = mapped_column(String(100), nullable=True)
    titulos: Mapped[list[str] | None] = mapped_column(ARRAY(Text), nullable=True)
    experiencia_laboral: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    cv_documento_url: Mapped[str] = mapped_column(String(500), nullable=False)
    creado_en: Mapped[datetime] = mapped_column(server_default=func.now())

    postulaciones: Mapped[list["Postulacion"]] = relationship(back_populates="postulante")  # noqa: F821
