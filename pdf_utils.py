
from io import BytesIO
from pypdf import PdfReader

MAX_PDF_SIZE = 5 * 1024 * 1024


def extract_pdf_text(uploaded_file):
    if uploaded_file.size > MAX_PDF_SIZE:
        raise ValueError("Le PDF ne doit pas dépasser 5 Mo.")

    reader = PdfReader(BytesIO(uploaded_file.getvalue()))

    if reader.is_encrypted:
        raise ValueError(
            "PDF protégé par mot de passe non pris en charge."
        )

    text = "\n".join(
        page.extract_text() or ""
        for page in reader.pages
    )

    if not text.strip():
        raise ValueError(
            "Aucun texte extrait. Le PDF est peut-être scanné."
        )

    return text
