from pydantic import BaseModel


class PipelineEtapaCount(BaseModel):
    estado: str
    total: int


class OrigenCount(BaseModel):
    origen: str
    total: int


class DashboardMetricsOut(BaseModel):
    vacantes_activas: int
    vacantes_expiradas: int
    postulaciones_totales: int
    postulaciones_por_etapa: list[PipelineEtapaCount]
    postulaciones_por_origen: list[OrigenCount]
    entrevistas_pendientes: int
