"""Extrai o texto de um documento enviado (.txt, .md, .docx, .pdf) para o parser de rotinas.

Sem IA: o texto extraído é mostrado para você conferir e ajustar antes de salvar. Funciona bem com
documentos que já listam o treino em linhas (como um PDF de personal ou uma planilha exportada).
"""
import io
import re
import zipfile
from xml.etree import ElementTree

MAX_BYTES = 5 * 1024 * 1024
ALLOWED = {".txt", ".md", ".docx", ".pdf"}
_W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"


class DocumentError(Exception):
    """Documento que não deu para ler. A mensagem é mostrada ao usuário."""


def extract_text(filename: str, content: bytes) -> str:
    name = (filename or "").lower()
    extension = name[name.rfind("."):] if "." in name else ""
    if extension not in ALLOWED:
        raise DocumentError("Formato não aceito. Envie .txt, .md, .docx ou .pdf.")
    if len(content) > MAX_BYTES:
        raise DocumentError("Arquivo maior que 5 MB.")
    if not content:
        raise DocumentError("O arquivo está vazio.")
    if extension in (".txt", ".md"):
        text = _decode(content)
    elif extension == ".docx":
        text = _docx(content)
    else:
        text = _pdf(content)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    if not text:
        raise DocumentError("Não encontrei texto no arquivo. Se for um PDF escaneado (imagem), copie o texto à mão.")
    return text[:20000]


def _decode(content: bytes) -> str:
    for encoding in ("utf-8-sig", "cp1252", "latin-1"):
        try:
            return content.decode(encoding)
        except UnicodeDecodeError:
            continue
    return content.decode("utf-8", "replace")


def _docx(content: bytes) -> str:
    """Lê word/document.xml: cada parágrafo vira uma linha; células de tabela também."""
    try:
        with zipfile.ZipFile(io.BytesIO(content)) as archive:
            xml = archive.read("word/document.xml")
    except (zipfile.BadZipFile, KeyError) as exc:
        raise DocumentError("Não consegui abrir o .docx. Salve de novo no Word e tente outra vez.") from exc
    root = ElementTree.fromstring(xml)
    lines = []
    for paragraph in root.iter(f"{_W}p"):
        text = "".join(node.text or "" for node in paragraph.iter(f"{_W}t"))
        if paragraph.find(f".//{_W}numPr") is not None and text.strip():
            text = f"- {text}"  # item de lista do Word vira exercício
        lines.append(text)
    return "\n".join(lines)


def _pdf(content: bytes) -> str:
    try:
        from pypdf import PdfReader
        from pypdf.errors import PdfReadError
    except ImportError as exc:  # pragma: no cover - dependência listada no requirements.txt
        raise DocumentError("Leitura de PDF indisponível (instale pypdf).") from exc
    try:
        reader = PdfReader(io.BytesIO(content))
        if reader.is_encrypted:
            raise DocumentError("PDF protegido por senha. Remova a senha e envie de novo.")
        return "\n".join(page.extract_text() or "" for page in reader.pages[:30])
    except PdfReadError as exc:
        raise DocumentError("Não consegui ler o PDF.") from exc
