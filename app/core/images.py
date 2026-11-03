"""Tratamento de fotos enviadas (memórias e avatar): valida, gira pela orientação, reduz e regrava em
WebP **sem metadados** (EXIF, GPS, modelo do celular). O arquivo original nunca é guardado como veio.
"""
import io
from dataclasses import dataclass

from PIL import Image, ImageOps, UnidentifiedImageError

from .errors import DomainError

MAX_UPLOAD_BYTES = 10 * 1024 * 1024
MAX_PIXELS = 40_000_000  # evita "bombas" de descompressão
Image.MAX_IMAGE_PIXELS = MAX_PIXELS


@dataclass(frozen=True)
class Processed:
    data: bytes
    width: int
    height: int


def open_image(content: bytes) -> Image.Image:
    if not content:
        raise DomainError("Escolha uma foto.")
    if len(content) > MAX_UPLOAD_BYTES:
        raise DomainError(f"Foto grande demais (máximo {MAX_UPLOAD_BYTES // (1024 * 1024)} MB).")
    try:
        probe = Image.open(io.BytesIO(content))
        probe.verify()
        image = Image.open(io.BytesIO(content))
        image.load()
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError, SyntaxError) as exc:
        raise DomainError("Arquivo não é uma imagem válida (use JPG, PNG ou WebP).") from exc
    image = ImageOps.exif_transpose(image)  # aplica a rotação do celular antes de jogar o EXIF fora
    return image.convert("RGB")


def to_webp(image: Image.Image, max_side: int, quality: int = 80) -> Processed:
    copy = image.copy()
    copy.thumbnail((max_side, max_side), Image.Resampling.LANCZOS)
    out = io.BytesIO()
    copy.save(out, "WEBP", quality=quality, method=6)  # sem exif=: nenhum metadado é gravado
    return Processed(out.getvalue(), copy.width, copy.height)


def process(content: bytes, max_side: int, quality: int = 80) -> Processed:
    return to_webp(open_image(content), max_side, quality)
