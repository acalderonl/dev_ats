from sqlalchemy import Boolean, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Cargo(Base):
    """Descriptivo de un puesto: identificación, misión y actividades."""

    __tablename__ = "cargos"

    id: Mapped[int] = mapped_column(primary_key=True)

    # 1. Identificación del puesto
    nombre_id: Mapped[int] = mapped_column(ForeignKey("nombres_cargo.id"), nullable=False)
    tiene_personal_a_cargo: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    clasificacion_id: Mapped[int | None] = mapped_column(ForeignKey("clasificaciones_cargo.id"), nullable=True)

    # 2. Misión del cargo
    mision: Mapped[str | None] = mapped_column(Text, nullable=True)

    # 3. Actividades del cargo. Lista ordenada de {texto, favorita}; el orden del array es
    #    el que se muestra, y las favoritas ya vienen arriba (se ordenan al guardar).
    actividades: Mapped[list[dict]] = mapped_column(JSONB, default=list, nullable=False)

    # 4. Educación formal requerida. Hasta dos de cada uno: viven en tablas aparte
    #    (ver `app/models/cargo_educacion.py`).

    # 7. Experiencia requerida: el tramo de años más tres exigencias sueltas.
    experiencia_requerida: Mapped[str | None] = mapped_column(String(20), nullable=True)
    experiencia_empresas_similares: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    experiencia_cargos_similares: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    experiencia_interna_otros_cargos: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    activo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    nombre_catalogo: Mapped["NombreCargo"] = relationship(back_populates="cargos")  # noqa: F821
    niveles_educacion: Mapped[list["CargoNivelEducacion"]] = relationship(  # noqa: F821
        back_populates="cargo", cascade="all, delete-orphan", order_by="CargoNivelEducacion.orden"
    )
    titulos: Mapped[list["CargoTitulo"]] = relationship(  # noqa: F821
        back_populates="cargo", cascade="all, delete-orphan", order_by="CargoTitulo.orden"
    )
    areas_academicas: Mapped[list["CargoAreaAcademica"]] = relationship(  # noqa: F821
        back_populates="cargo", cascade="all, delete-orphan", order_by="CargoAreaAcademica.orden"
    )
    clasificacion_catalogo: Mapped["ClasificacionCargo | None"] = relationship(back_populates="cargos")  # noqa: F821
    competencias: Mapped[list["CargoCompetencia"]] = relationship(  # noqa: F821
        back_populates="cargo", cascade="all, delete-orphan"
    )
    preguntas_filtro: Mapped[list["PreguntaFiltro"]] = relationship(  # noqa: F821
        back_populates="cargo", cascade="all, delete-orphan"
    )
    vacantes: Mapped[list["Vacante"]] = relationship(back_populates="cargo")  # noqa: F821

    @property
    def nombre(self) -> str:
        """Nombre del cargo como texto.

        El nombre vive en un catálogo aparte desde la migración 0002, pero el resto del
        sistema (el portal público, la tabla de vacantes) sigue leyendo `cargo.nombre`:
        esta propiedad mantiene ese contrato intacto.
        """
        return self.nombre_catalogo.nombre

    @property
    def clasificacion(self) -> str | None:
        return self.clasificacion_catalogo.nombre if self.clasificacion_catalogo else None
