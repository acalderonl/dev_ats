from sqlalchemy import Boolean, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class PreguntaFiltro(Base):
    __tablename__ = "preguntas_filtro"

    id: Mapped[int] = mapped_column(primary_key=True)
    cargo_id: Mapped[int] = mapped_column(ForeignKey("cargos.id", ondelete="CASCADE"), nullable=False)
    pregunta: Mapped[str] = mapped_column(Text, nullable=False)
    tipo_respuesta: Mapped[str] = mapped_column(String(50), nullable=False)
    opciones: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)
    es_eliminatoria: Mapped[bool] = mapped_column(Boolean, default=False)
    respuesta_correcta: Mapped[str | None] = mapped_column(Text, nullable=True)

    cargo: Mapped["Cargo"] = relationship(back_populates="preguntas_filtro")  # noqa: F821
