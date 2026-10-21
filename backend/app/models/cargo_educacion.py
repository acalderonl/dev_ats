"""Educación formal exigida por un cargo (sección 4 del descriptivo).

Antes cada cargo guardaba un solo nivel, un solo título y una sola área en columnas
propias. Ahora admite **hasta dos de cada uno**, así que pasan a tablas aparte: una fila
por valor elegido.

El tope de dos se valida en el esquema (`app/schemas/cargo.py`), no en la base: es una
regla de producto que puede cambiar, y expresarla en SQL exigiría un disparador.

La clave primaria incluye el id del catálogo, así que la base impide elegir dos veces el
mismo nivel, título o área dentro de un mismo cargo.
"""

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class CargoNivelEducacion(Base):
    __tablename__ = "cargo_niveles_educacion"

    cargo_id: Mapped[int] = mapped_column(Integer, ForeignKey("cargos.id", ondelete="CASCADE"), primary_key=True)
    nivel_id: Mapped[int] = mapped_column(Integer, ForeignKey("niveles_educacion.id"), primary_key=True)
    # 'completa' o 'en_curso': cada nivel exigido lleva el suyo.
    estado: Mapped[str] = mapped_column(String(20), nullable=False, default="completa")
    orden: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    cargo: Mapped["Cargo"] = relationship(back_populates="niveles_educacion")  # noqa: F821
    nivel: Mapped["NivelEducacion"] = relationship()  # noqa: F821


class CargoTitulo(Base):
    __tablename__ = "cargo_titulos"

    cargo_id: Mapped[int] = mapped_column(Integer, ForeignKey("cargos.id", ondelete="CASCADE"), primary_key=True)
    titulo_id: Mapped[int] = mapped_column(Integer, ForeignKey("titulos_academicos.id"), primary_key=True)
    orden: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    cargo: Mapped["Cargo"] = relationship(back_populates="titulos")  # noqa: F821
    titulo: Mapped["TituloAcademico"] = relationship()  # noqa: F821


class CargoAreaAcademica(Base):
    __tablename__ = "cargo_areas_academicas"

    cargo_id: Mapped[int] = mapped_column(Integer, ForeignKey("cargos.id", ondelete="CASCADE"), primary_key=True)
    area_id: Mapped[int] = mapped_column(Integer, ForeignKey("areas_academicas.id"), primary_key=True)
    orden: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    cargo: Mapped["Cargo"] = relationship(back_populates="areas_academicas")  # noqa: F821
    area: Mapped["AreaAcademica"] = relationship()  # noqa: F821
