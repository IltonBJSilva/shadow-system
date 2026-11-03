"""Avatar do Hunter gerado a partir de uma foto do jogador.

Arquitetura de provedores: `AvatarProvider` define como transformar a foto num avatar. Hoje existe só o
provedor local (`LocalStyleProvider`, Pillow): recorta em retrato e aplica um estilo do System. Para usar
um serviço externo de geração de imagens no futuro, crie outra classe com a mesma interface e registre
em PROVIDERS; a escolha fica em AVATAR_PROVIDER (config). Não há IA aqui.

Privacidade: a foto original (já sem metadados) fica só para o dono e pode ser apagada a qualquer
momento; os outros Hunters veem apenas o avatar estilizado. A evolução por rank (moldura, aura) é
feita em CSS por cima do avatar, então muda sozinha quando o rank sobe.
"""
import io
from typing import Protocol

from PIL import Image, ImageDraw, ImageFilter, ImageOps

from app.core import images

SIZE = (480, 640)  # retrato 3:4


class AvatarProvider(Protocol):
    key: str
    styles: dict[str, str]

    def generate(self, photo: Image.Image, style: str) -> bytes: ...


class LocalStyleProvider:
    """Estilos feitos com processamento de imagem (sem IA, sem enviar a foto para fora)."""

    key = "local"
    styles = {
        "shadow": "Sombra (azul profundo)",
        "monarch": "Monarca (roxo)",
        "hologram": "Holograma (ciano com linhas)",
        "classic": "Clássico (foto tratada)",
    }
    _palettes = {
        "shadow": ("#030712", "#1d4ed8", "#dbeafe"),
        "monarch": ("#05010d", "#6d28d9", "#f3e8ff"),
        "hologram": ("#020617", "#0891b2", "#cffafe"),
    }

    def generate(self, photo: Image.Image, style: str) -> bytes:
        portrait = ImageOps.fit(photo, SIZE, Image.Resampling.LANCZOS, centering=(0.5, 0.35))
        if style in self._palettes:
            black, mid, white = self._palettes[style]
            gray = ImageOps.autocontrast(ImageOps.grayscale(portrait), cutoff=1)
            result = ImageOps.colorize(gray, black=black, mid=mid, white=white)
            if style == "hologram":
                result = _scanlines(result)
        else:
            result = ImageOps.autocontrast(portrait, cutoff=1)
            tint = Image.new("RGB", SIZE, "#1e3a8a")
            result = Image.blend(result, tint, 0.12)
        result = _vignette(result)
        out = io.BytesIO()
        result.save(out, "WEBP", quality=82, method=6)
        return out.getvalue()


def _vignette(image: Image.Image) -> Image.Image:
    mask = Image.new("L", image.size, 0)
    ImageDraw.Draw(mask).ellipse((-image.width * 0.15, -image.height * 0.05, image.width * 1.15, image.height * 1.1), fill=255)
    mask = mask.filter(ImageFilter.GaussianBlur(image.width // 8))
    dark = Image.new("RGB", image.size, "#02030a")
    return Image.composite(image, dark, mask)


def _scanlines(image: Image.Image) -> Image.Image:
    lines = Image.new("L", image.size, 255)
    draw = ImageDraw.Draw(lines)
    for y in range(0, image.height, 4):
        draw.line((0, y, image.width, y), fill=170)
    glow = image.filter(ImageFilter.GaussianBlur(3))
    return Image.composite(Image.blend(image, glow, 0.35), Image.new("RGB", image.size, "#020617"), lines)


PROVIDERS: dict[str, AvatarProvider] = {"local": LocalStyleProvider()}


def provider(key: str = "local") -> AvatarProvider:
    return PROVIDERS.get(key, PROVIDERS["local"])


def prepare_photo(content: bytes) -> tuple[Image.Image, bytes]:
    """Abre a foto enviada e devolve a imagem e uma cópia reduzida, sem metadados, para guardar."""
    image = images.open_image(content)
    stored = images.to_webp(image, 1024, 85).data
    return image, stored
