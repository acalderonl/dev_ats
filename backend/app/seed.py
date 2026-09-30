"""Seed idempotente: roles base, usuarios de demo y catálogo inicial de cargos.

Se ejecuta en el evento de startup de la aplicación (ver app/main.py). Es seguro
llamarlo múltiples veces: cada bloque verifica si ya existe el dato antes de crearlo.
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models.cargo import Cargo
from app.models.pregunta_filtro import PreguntaFiltro
from app.models.rol import Rol
from app.models.usuario import Usuario

ROLES = ["super_admin", "reclutador", "entrevistador"]

DEMO_USERS = [
    ("admin@atsdemo.com", "Demo1234!", "Alejandra", "Torres", "super_admin"),
    ("reclutador@atsdemo.com", "Demo1234!", "Mateo", "Salazar", "reclutador"),
    ("entrevistador@atsdemo.com", "Demo1234!", "Carolina", "Reyes", "entrevistador"),
]

DEMO_CARGOS = [
    {
        "nombre": "Desarrollador Backend Senior",
        "departamento": "Tecnología",
        "descripcion": "Python/FastAPI, arquitectura limpia.",
        "preguntas": [
            ("¿Cuántos años de experiencia tiene en Python?", "numero", True, ">= 3"),
            ("¿Tiene experiencia con Docker?", "booleano", False, "Sí"),
        ],
    },
    {
        "nombre": "Diseñador UX/UI",
        "departamento": "Producto",
        "descripcion": "Diseño de experiencia e interfaces responsive.",
        "preguntas": [("¿Maneja Figma?", "booleano", True, "Sí")],
    },
    {
        "nombre": "Analista de Reclutamiento",
        "departamento": "Talento Humano",
        "descripcion": "Gestión de procesos de selección.",
        "preguntas": [("¿Disponibilidad para trabajo presencial?", "booleano", True, "Sí")],
    },
]


def seed_roles(db: Session) -> dict[str, Rol]:
    roles_por_nombre: dict[str, Rol] = {}
    for nombre in ROLES:
        rol = db.scalar(select(Rol).where(Rol.nombre == nombre))
        if rol is None:
            rol = Rol(nombre=nombre)
            db.add(rol)
            db.flush()
        roles_por_nombre[nombre] = rol
    db.commit()
    return roles_por_nombre


def seed_demo_users(db: Session, roles_por_nombre: dict[str, Rol]) -> None:
    for email, password, nombres, apellidos, rol_nombre in DEMO_USERS:
        existente = db.scalar(select(Usuario).where(Usuario.email == email))
        if existente is not None:
            continue
        usuario = Usuario(
            email=email,
            password_hash=hash_password(password),
            nombres=nombres,
            apellidos=apellidos,
            rol_id=roles_por_nombre[rol_nombre].id,
        )
        db.add(usuario)
    db.commit()


def seed_demo_cargos(db: Session) -> None:
    if db.scalar(select(Cargo)) is not None:
        return
    for data in DEMO_CARGOS:
        cargo = Cargo(nombre=data["nombre"], departamento=data["departamento"], descripcion=data["descripcion"])
        db.add(cargo)
        db.flush()
        for pregunta, tipo, eliminatoria, respuesta in data["preguntas"]:
            db.add(
                PreguntaFiltro(
                    cargo_id=cargo.id,
                    pregunta=pregunta,
                    tipo_respuesta=tipo,
                    es_eliminatoria=eliminatoria,
                    respuesta_correcta=respuesta,
                )
            )
    db.commit()


def run_seed(db: Session) -> None:
    roles_por_nombre = seed_roles(db)
    seed_demo_users(db, roles_por_nombre)
    seed_demo_cargos(db)
