import io

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas


def render_pdf_report(report_text: str) -> bytes:
    """Convert plain text report to a simple PDF document."""
    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    x = 40
    y = height - 40
    line_height = 12

    for line in report_text.splitlines():
        if y < 40:
            pdf.showPage()
            y = height - 40
        pdf.drawString(x, y, line)
        y -= line_height

    pdf.save()
    return buffer.getvalue()
