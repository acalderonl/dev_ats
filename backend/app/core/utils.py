import re
import unicodedata
import uuid


def slugify(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-z0-9]+", "-", normalized.lower()).strip("-")
    suffix = uuid.uuid4().hex[:6]
    return f"{slug}-{suffix}"
