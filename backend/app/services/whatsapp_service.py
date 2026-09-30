from urllib.parse import quote


def build_share_link(titulo: str, url_postulacion: str) -> str:
    mensaje = f"¡Estamos contratando! {titulo}. Postula aquí: {url_postulacion}"
    return f"https://api.whatsapp.com/send?text={quote(mensaje)}"
