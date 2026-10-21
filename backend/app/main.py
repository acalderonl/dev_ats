from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import api_router
from app.core.config import get_settings
from app.core.database import SessionLocal
from app.seed import run_seed
from app.seed_permisos import sembrar_permisos

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    db = SessionLocal()
    try:
        run_seed(db)
        # Después del seed: necesita que los roles existan para asignarles la plantilla.
        sembrar_permisos(db)
    finally:
        db.close()
    yield


app = FastAPI(title="ANAI - Seleccion de personal", version="1.0.0", lifespan=lifespan)

# En producción los orígenes salen solo de FRONTEND_ORIGIN; en desarrollo se añade
# localhost para no tener que configurarlo. Ver `Settings.origenes_permitidos`.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.origenes_permitidos(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}
