import shutil
import sys
from pdf2image import convert_from_path
import pytesseract

# Caminho completo opcional (caso queira forçar)
# pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# Verificar se o Poppler está instalado (busca por pdfinfo.exe no PATH)
if shutil.which("pdfinfo") is None:
    print("❌ Poppler (pdfinfo.exe) não foi encontrado no PATH.")
    print("➡ Baixe de: https://github.com/oschwartz10612/poppler-windows/releases")
    print("➡ Extraia e adicione o caminho de 'poppler\\Library\\bin' ao PATH do sistema.")
    sys.exit(1)

# Tentativa de extração com OCR
try:
    pages = convert_from_path("André Comte-Sponville.pdf", dpi=300, first_page=55, last_page=64)
    texto = ""

    for i, page in enumerate(pages, start=55):
        texto += f"--- Página {i} ---\n"
        texto += pytesseract.image_to_string(page, lang="por") + "\n\n"

    with open("capitulo_5_extraido.txt", "w", encoding="utf-8") as f:
        f.write(texto)

    print("✅ Texto extraído com sucesso: capitulo_5_extraido.txt")

except Exception as e:
    print(f"❌ Erro ao extrair texto: {e}")
