"""Preferências de experiência (animação de inicialização). Guardadas em app_settings."""
from . import settings

BOOT_KEY = "ui.boot_mode"
BOOT_MODES: dict[str, str] = {
    "session": "Uma vez por sessão (ao abrir o navegador)",
    "dashboard": "Sempre que abrir o Dashboard",
    "off": "Desligada",
}
DEFAULT_BOOT_MODE = "session"

MANIFESTO = "SE ESSE SISTEMA QUER ME USAR, ENTÃO EU VOU USAR O SISTEMA."


def boot_mode() -> str:
    mode = settings.get_setting(BOOT_KEY, DEFAULT_BOOT_MODE)
    return mode if mode in BOOT_MODES else DEFAULT_BOOT_MODE


def set_boot_mode(mode: str) -> None:
    settings.set_setting(BOOT_KEY, mode if mode in BOOT_MODES else DEFAULT_BOOT_MODE)
