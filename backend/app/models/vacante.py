"""Una vacante es un cargo puesto en circulación: **las condiciones del puesto**.

El título ya no se escribe: se elige el cargo y el título se copia de él al crearla.
Es una copia deliberada, no un `join`: si el título siguiera al catálogo, renombrar un
cargo cambiaría lo que ya se publicó.

Desde la migración 0010 la vacante **no lleva el ciclo**: ni fecha límite, ni estado de
proceso, ni post, ni enlace público, ni postulantes. Todo eso vive en la
**convocatoria** (`app/models/convocatoria.py`), porque una misma vacante se convoca
varias veces y cada vez tiene que quedar registrada. La vacante queda con lo que no
cambia entre convocatorias: sueldo, horario, contrato, campos y a quién puede llegar.

Lo que sí queda aquí y se confunde:

- `activa`: si la vacante sigue en uso. Se desactiva, no se borra, como los cargos.
- `visibilidad`: a quién puede llegar (pública, interna, mixta). Es del puesto, no del
  ciclo: si una ronda tuviera que ser interna y la siguiente pública, habría que
  moverla a la convocatoria; hoy no hace falta.
"""

import uuid
from datetime import datetime, time
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, ForeignKey, Numeric, String, Text, Time, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

VISIBILIDADES = ("publica", "interna", "mixta")


class Vacante(Base):
    __tablename__ = "vacantes"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cargo_id: Mapped[int] = mapped_column(ForeignKey("cargos.id"), nullable=False)
    # Copia del nombre del cargo en el momento de crearla. Ver el comentario de arriba.
    titulo: Mapped[str] = mapped_column(String(200), nullable=False)
    descripcion: Mapped[str] = mapped_column(Text, nullable=False)

    # --- Condiciones del puesto ---
    remuneracion: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    # Horas copiadas de la jornada elegida, no una clave foránea: cambiar la jornada
    # en Configuración no debe reescribir el horario de vacantes ya publicadas.
    jornada_horas: Mapped[Decimal | None] = mapped_column(Numeric(4, 2), nullable=True)
    hora_entrada: Mapped[time | None] = mapped_column(Time, nullable=True)
    hora_salida: Mapped[time | None] = mapped_column(Time, nullable=True)
    tipo_contrato_id: Mapped[int | None] = mapped_column(ForeignKey("tipos_contrato.id"), nullable=True)

    # Campos que inventa quien publica: [{"etiqueta": "...", "valor": "..."}]. Son
    # libres por definición, así que no tienen tabla ni esquema fijo.
    campos_personalizados: Mapped[list] = mapped_column(JSONB, default=list, nullable=False)

    # --- Alcance ---
    visibilidad: Mapped[str] = mapped_column(String(20), default="publica", nullable=False)
    # Correos a los que se envía cuando la vacante es interna o mixta.
    destinatarios_internos: Mapped[list] = mapped_column(JSONB, default=list, nullable=False)

    documento_adjunto_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    empleador_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=False)
    activa: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    creado_en: Mapped[datetime] = mapped_column(server_default=func.now())

    cargo: Mapped["Cargo"] = relationship(back_populates="vacantes")  # noqa: F821
    tipo_contrato: Mapped["TipoContrato | None"] = relationship(back_populates="vacantes")  # noqa: F821
    # De la más reciente a la primera: la actual es `convocatorias[0]`.
    convocatorias: Mapped[list["Convocatoria"]] = relationship(  # noqa: F821
        back_populates="vacante", order_by="Convocatoria.numero.desc()", cascade="all, delete-orphan"
    )

    @property
    def convocatoria_actual(self) -> "Convocatoria | None":  # noqa: F821
        """La última convocatoria, que es sobre la que se actúa desde la tarjeta."""
        return self.convocatorias[0] if self.convocatorias else None


class TokenLinkedIn(Base):
    """Token OAuth de LinkedIn por usuario.

    LinkedIn solo entrega *refresh token* a partners aprobados, así que un token de
    autoservicio caduca a los ~60 días y no se puede renovar solo: hay que volver a
    conectar. Por eso se guarda `expira_en` y la pantalla de Configuración avisa antes.

    El token va cifrado, igual que los secretos de `configuracion`.
    """

    __tablename__ = "tokens_linkedin"

    usuario_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("usuarios.id", ondelete="CASCADE"), primary_key=True
    )
    access_token_cifrado: Mapped[str] = mapped_column(Text, nullable=False)
    # urn:li:person:xxxx — a quién pertenece el muro donde se publica.
    persona_urn: Mapped[str] = mapped_column(String(200), nullable=False)
    nombre_en_linkedin: Mapped[str | None] = mapped_column(String(200), nullable=True)
    expira_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revocado: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    creado_en: Mapped[datetime] = mapped_column(server_default=func.now())
