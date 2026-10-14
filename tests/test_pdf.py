
from io import BytesIO
from types import SimpleNamespace

import pytest
from reportlab.pdfgen import canvas
from pypdf import PdfWriter
from pypdf.errors import PdfReadError

from pdf_utils import extract_pdf_text


# Simuler un fichier charge dans Streamlit
def fake_upload(content, size=None):
    return SimpleNamespace(
        size=len(content) if size is None else size,
        getvalue=lambda: content
    )


# Generer un PDF de test avec du texte
@pytest.fixture
def valid_pdf():
    buffer = BytesIO()

    pdf = canvas.Canvas(buffer)
    pdf.drawString(
        72, 750,
        "Competences : Python, SQL et BigQuery"
    )
    pdf.save()

    return buffer.getvalue()


# TEST 1 : PDF valide
def test_valid_pdf(valid_pdf):
    text = extract_pdf_text(fake_upload(valid_pdf))

    assert "Python" in text
    assert "SQL" in text
    assert "BigQuery" in text


# TEST 2 : PDF vide
def test_empty_pdf():
    writer = PdfWriter()
    writer.add_blank_page(width=595, height=842)

    buffer = BytesIO()
    writer.write(buffer)

    with pytest.raises(ValueError, match="Aucun texte"):
        extract_pdf_text(fake_upload(buffer.getvalue()))


# TEST 3 : PDF trop volumineux
def test_oversized_pdf(valid_pdf):
    with pytest.raises(ValueError, match="5 Mo"):
        extract_pdf_text(
            fake_upload(
                valid_pdf,
                size=6 * 1024 * 1024
            )
        )


# TEST 4 : Fichier PDF corrompu
def test_invalid_pdf():
    with pytest.raises(PdfReadError):
        extract_pdf_text(
            fake_upload(b"Ce fichier n'est pas un PDF")
        )
