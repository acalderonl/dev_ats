"""Una convocatoria es una vez que la vacante sale a recibir gente.

La vacante guarda las condiciones del puesto (sueldo, horario, contrato, campos). La
convocatoria guarda **el ciclo**: hasta cuándo se reciben postulaciones, en qué estado
va, el post con el que se anunció, el enlace público y, colgando de ella, los
postulantes. Una misma vacante se puede convocar varias veces —porque nadie encajó, o
porque el puesto se volvió a abrir— y cada vez queda registrada para el control.

La convocatoria **no copia** las condiciones: las lee de la vacante (decisión del dueño
el 2026-11-04). Si se edita el sueldo de la vacante, cambia lo que se ve en todas sus
convocatorias, también las cerradas. Se eligió así por simplicidad, sabiendo eso.

Del `slug`: antes vivía en la vacante y era su URL pública. Ahora cada convocatoria
tiene el suyo, porque hace falta saber **a cuál** se postuló alguien. La migración
0010 le dio a la primera convocatoria de cada vacante el slug que ya tenía la vacante,
para que ningún enlace repartido dejara de funcionar.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

ESTADOS = ("borrador", "abierta", "cerrada")
# "compartido" NO es "publicado": al abrir el compositor de LinkedIn entregamos el
# contenido, pero quien pulsa Publicar es la persona y el sistema no puede saber si lo
# hizo. Decir "publicado" sin saberlo sería mentir en la pantalla.
ESTADOS_DEL_POST = ("borrador", "programado", "compartido", "publicado", "error")


class Convocatoria(Base):
    __tablename__ = "convocatorias"
    __table_args__ = (UniqueConstraint("vacante_id", "numero", name="uq_convocatoria_numero_por_vacante"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    vacante_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("vacantes.id"), nullable=False, index=True
    )
    # 1, 2, 3... dentro de la vacante. Es lo que la gente dice: "la segunda convocatoria".
    numero: Mapped[int] = mapped_column(Integer, nullable=False)

    # --- El ciclo ---
    fecha_limite: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    estado: Mapped[str] = mapped_column(String(20), default="borrador", nullable=False)
    slug: Mapped[str] = mapped_column(String(250), unique=True, nullable=False, index=True)

    # --- La publicación ---
    asunto: Mapped[str | None] = mapped_column(String(200), nullable=True)
    post_cuerpo: Mapped[str | None] = mapped_column(Text, nullable=True)
    post_imagen_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    post_programado_para: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    post_estado: Mapped[str] = mapped_column(String(20), default="borrador", nullable=False)
    post_publicado_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    post_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    linkedin_post_id: Mapped[str | None] = mapped_column(String(200), nullable=True)
    enviado_internamente_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    creado_por: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=True)
    creado_en: Mapped[datetime] = mapped_column(server_default=func.now())

    vacante: Mapped["Vacante"] = relationship(back_populates="convocatorias")  # noqa: F821
    postulaciones: Mapped[list["Postulacion"]] = relationship(back_populates="convocatoria")  # noqa: F821

    @property
    def acepta_postulaciones(self) -> bool:
        """Solo una convocatoria abierta y no vencida recibe gente."""
        limite = self.fecha_limite
        if limite.tzinfo is None:
            limite = limite.replace(tzinfo=timezone.utc)
        return self.estado == "abierta" and limite > datetime.now(timezone.utc)
