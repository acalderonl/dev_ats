"""Seed idempotente: roles base, usuarios de demo y catálogo inicial de cargos.

Se ejecuta en el evento de startup de la aplicación (ver app/main.py). Es seguro
llamarlo múltiples veces: cada bloque verifica si ya existe el dato antes de crearlo.
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models.cargo import Cargo
from app.models.cargo_educacion import CargoAreaAcademica, CargoNivelEducacion
from app.models.catalogos_educacion import AreaAcademica, NivelEducacion, TituloAcademico
from app.models.clasificacion_cargo import ClasificacionCargo
from app.models.nombre_cargo import NombreCargo
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
        "clasificacion": "Tecnología",
        "tiene_personal_a_cargo": False,
        "mision": "Diseñar y mantener los servicios del lado del servidor, garantizando que la "
        "plataforma sea estable, segura y fácil de evolucionar.",
        "actividades": [
            "Desarrollar y mantener los endpoints de la API.",
            "Diseñar el modelo de datos y sus migraciones.",
            "Revisar el código de otros desarrolladores.",
        ],
        "nivel_educacion": "Tercer Nivel (Grado)",
        "area_academica": "Tecnologías de la Información y la Comunicación",
        "experiencia_requerida": "3_a_5",
        "preguntas": [
            ("¿Cuántos años de experiencia tiene en Python?", "numero", True, ">= 3"),
            ("¿Tiene experiencia con Docker?", "booleano", False, "Sí"),
        ],
    },
    {
        "nombre": "Diseñador UX/UI",
        "clasificacion": "Producto",
        "tiene_personal_a_cargo": False,
        "mision": "Diseñar interfaces claras y accesibles que permitan a cada usuario completar su "
        "tarea sin fricción, en cualquier dispositivo.",
        "actividades": [
            "Levantar flujos de usuario y prototipos.",
            "Mantener el sistema de diseño.",
            "Validar las propuestas con usuarios reales.",
        ],
        "nivel_educacion": "Tercer Nivel (Grado)",
        "area_academica": "Artes y Humanidades",
        "experiencia_requerida": "1_a_3",
        "preguntas": [("¿Maneja Figma?", "booleano", True, "Sí")],
    },
    {
        "nombre": "Analista de Reclutamiento",
        "clasificacion": "Talento Humano",
        "tiene_personal_a_cargo": True,
        "mision": "Conducir los procesos de selección de principio a fin, asegurando que cada "
        "vacante se cubra con el perfil adecuado y en el plazo comprometido.",
        "actividades": [
            "Publicar las vacantes y difundirlas por los canales disponibles.",
            "Filtrar las postulaciones recibidas y coordinar las entrevistas.",
            "Acompañar al candidato seleccionado durante su incorporación.",
        ],
        "nivel_educacion": "Tercer Nivel (Grado)",
        "area_academica": "Administración de Empresas y Derecho",
        "experiencia_requerida": "mas_de_5",
        "preguntas": [("¿Disponibilidad para trabajo presencial?", "booleano", True, "Sí")],
    },
]


def seed_roles(db: Session) -> dict[str, Rol]:
    """Crea los tres roles base, marcados como **del sistema**.

    El `es_sistema=True` no es decorativo: protege contra renombrarlos, y el código
    todavía nombra estos roles en `require_roles(...)`. La migración 0008 marca los
    que ya existían, pero en una instalación nueva las filas las crea esta función,
    así que sin este argumento quedarían desprotegidas.
    """
    roles_por_nombre: dict[str, Rol] = {}
    for nombre in ROLES:
        rol = db.scalar(select(Rol).where(Rol.nombre == nombre))
        if rol is None:
            rol = Rol(nombre=nombre, es_sistema=True)
            db.add(rol)
            db.flush()
        elif not rol.es_sistema:
            # Por si la fila viene de antes de que existiera la marca.
            rol.es_sistema = True
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


# Niveles de la Ley Orgánica de Educación Superior (LOES) de Ecuador, más los previos.
NIVELES_EDUCACION = [
    "Educación Básica",
    "Bachillerato",
    "Técnico Superior",
    "Tecnológico Superior",
    "Tercer Nivel (Grado)",
    "Especialización",
    "Maestría",
    "Doctorado (PhD)",
]

# Campos amplios de la Clasificación Internacional Normalizada de la Educación (CINE-UNESCO),
# que es la que usa la SENESCYT para clasificar las carreras.
AREAS_ACADEMICAS = [
    "Educación",
    "Artes y Humanidades",
    "Ciencias Sociales, Periodismo e Información",
    "Administración de Empresas y Derecho",
    "Ciencias Naturales, Matemáticas y Estadística",
    "Tecnologías de la Información y la Comunicación",
    "Ingeniería, Industria y Construcción",
    "Agricultura, Silvicultura, Pesca y Veterinaria",
    "Salud y Bienestar",
    "Servicios",
]

# Arranque mínimo: la lista real es abierta y se amplía desde el engranaje del formulario.
TITULOS_ACADEMICOS = [
    "Ingeniero/a",
    "Licenciado/a",
    "Tecnólogo/a",
    "Técnico/a",
    "Abogado/a",
    "Economista",
    "Médico/a",
    "Psicólogo/a",
    "Contador/a Público/a",
    "Magíster",
    "Doctor/a (PhD)",
]


def seed_catalogos_educacion(db: Session) -> None:
    """Siembra los catálogos de la sección 4. Idempotente: solo añade lo que falta."""
    for modelo, nombres in (
        (NivelEducacion, NIVELES_EDUCACION),
        (AreaAcademica, AREAS_ACADEMICAS),
        (TituloAcademico, TITULOS_ACADEMICOS),
    ):
        for nombre in nombres:
            if db.scalar(select(modelo).where(modelo.nombre == nombre)) is None:
                db.add(modelo(nombre=nombre))
    db.commit()


def _catalogo(db: Session, modelo, nombre: str):
    """Devuelve el elemento del catálogo con ese nombre, creándolo si no existe."""
    item = db.scalar(select(modelo).where(modelo.nombre == nombre))
    if item is None:
        item = modelo(nombre=nombre)
        db.add(item)
        db.flush()
    return item


def seed_demo_cargos(db: Session) -> None:
    if db.scalar(select(Cargo)) is not None:
        return
    for data in DEMO_CARGOS:
        cargo = Cargo(
            nombre_id=_catalogo(db, NombreCargo, data["nombre"]).id,
            clasificacion_id=_catalogo(db, ClasificacionCargo, data["clasificacion"]).id,
            tiene_personal_a_cargo=data["tiene_personal_a_cargo"],
            mision=data["mision"],
            # La primera actividad queda marcada como favorita, para que el demo muestre
            # cómo se ven las destacadas.
            actividades=[{"texto": texto, "favorita": indice == 0} for indice, texto in enumerate(data["actividades"])],
            experiencia_requerida=data["experiencia_requerida"],
            experiencia_cargos_similares=True,
        )
        db.add(cargo)
        db.flush()

        db.add(
            CargoNivelEducacion(
                cargo_id=cargo.id,
                nivel_id=_catalogo(db, NivelEducacion, data["nivel_educacion"]).id,
                estado="completa",
                orden=0,
            )
        )
        db.add(
            CargoAreaAcademica(
                cargo_id=cargo.id,
                area_id=_catalogo(db, AreaAcademica, data["area_academica"]).id,
                orden=0,
            )
        )

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
    seed_catalogos_educacion(db)
    roles_por_nombre = seed_roles(db)
    seed_demo_users(db, roles_por_nombre)
    seed_demo_cargos(db)
