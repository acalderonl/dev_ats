"""Una vacante es un cargo puesto en circulación.

El título ya no se escribe: se elige el cargo y el título se copia de él al crearla.
Es una copia deliberada, no un `join`. El título alimenta el `slug`, que es la URL
pública por la que entra el postulante; si el título siguiera al catálogo, renombrar
un cargo cambiaría la dirección de una vacante ya publicada y rompería los enlaces
que la gente ya tiene.

Tres cosas que se confunden y aquí son columnas distintas:

- `estado`: en qué punto está el proceso de selección (abierta, cerrada, borrador).
- `post_estado`: en qué punto está la publicación (borrador, programado, publicado, error).
- `visibilidad`: a quién puede llegar (pública, interna, mixta).

Una vacante puede estar abierta con el post todavía en borrador, o publicada y ya
cerrada. Meterlas en una sola columna obligaría a inventar estados combinados.
"""

import uuid
from datetime import datetime, time
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, ForeignKey, Numeric, String, Text, Time, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

ESTADOS = ("borrador", "abierta", "cerrada")
ESTADOS_DEL_POST = ("borrador", "programado", "publicado", "error")
VISIBILIDADES = ("publica", "interna", "mixta")


class Vacante(Base):
    __tablename__ = "vacantes"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cargo_id: Mapped[int] = mapped_column(ForeignKey("cargos.id"), nullable=False)
    # Copia del nombre del cargo en el momento de crearla. Ver el comentario de arriba.
    titulo: Mapped[str] = mapped_column(String(200), nullable=False)
    descripcion: Mapped[str] = mapped_column(Text, nullable=False)
    slug: Mapped[str] = mapped_column(String(250), unique=True, nullable=False, index=True)
    fecha_limite: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

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

    # --- La publicación ---
    asunto: Mapped[str | None] = mapped_column(String(200), nullable=True)
    post_cuerpo: Mapped[str | None] = mapped_column(Text, nullable=True)
    post_imagen_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    post_programado_para: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    post_estado: Mapped[str] = mapped_column(String(20), default="borrador", nullable=False)
    post_publicado_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    post_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    linkedin_post_id: Mapped[str | None] = mapped_column(String(200), nullable=True)

    # --- Alcance ---
    visibilidad: Mapped[str] = mapped_column(String(20), default="publica", nullable=False)
    # Correos a los que se envía cuando la vacante es interna o mixta.
    destinatarios_internos: Mapped[list] = mapped_column(JSONB, default=list, nullable=False)
    enviado_internamente_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    documento_adjunto_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    empleador_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=False)
    estado: Mapped[str] = mapped_column(String(50), default="borrador", nullable=False)
    creado_en: Mapped[datetime] = mapped_column(server_default=func.now())

    cargo: Mapped["Cargo"] = relationship(back_populates="vacantes")  # noqa: F821
    tipo_contrato: Mapped["TipoContrato | None"] = relationship(back_populates="vacantes")  # noqa: F821
    postulaciones: Mapped[list["Postulacion"]] = relationship(back_populates="vacante")  # noqa: F821

    @property
    def acepta_postulaciones(self) -> bool:
        """Solo una vacante abierta y no vencida recibe gente."""
        return self.estado == "abierta" and self.fecha_limite > datetime.now(self.fecha_limite.tzinfo)


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
