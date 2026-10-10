import os
from pathlib import Path
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfgen import canvas

OUTPUT_DIR = Path(os.getenv("CERTIFICATE_OUTPUT_DIR", "generated_certificates"))


def generate_certificate_pdf(
    recipient_name: str,
    event_name: str,
    issue_date: str,
    recipient_id: str,
) -> str:
    """Generate one PDF certificate and return its path."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = OUTPUT_DIR / f"{recipient_id}.pdf"

    page_width, page_height = landscape(A4)
    pdf = canvas.Canvas(str(output_path), pagesize=(page_width, page_height))

    # Simple single predefined template.
    margin = 28
    pdf.setFillColor(colors.HexColor("#FCFAF3"))
    pdf.rect(0, 0, page_width, page_height, fill=1, stroke=0)
    pdf.setStrokeColor(colors.HexColor("#B08D45"))
    pdf.setLineWidth(3)
    pdf.rect(margin, margin, page_width - 2 * margin, page_height - 2 * margin)
    pdf.setLineWidth(1)
    pdf.rect(margin + 8, margin + 8, page_width - 2 * (margin + 8), page_height - 2 * (margin + 8))

    pdf.setFillColor(colors.HexColor("#23334D"))
    pdf.setFont("Helvetica-Bold", 30)
    pdf.drawCentredString(page_width / 2, page_height - 105, "CERTIFICATE")
    pdf.setFont("Helvetica", 15)
    pdf.drawCentredString(page_width / 2, page_height - 135, "OF PARTICIPATION")

    pdf.setFillColor(colors.HexColor("#444444"))
    pdf.setFont("Helvetica", 14)
    pdf.drawCentredString(page_width / 2, page_height - 190, "This certificate is proudly presented to")

    pdf.setFillColor(colors.HexColor("#23334D"))
    pdf.setFont("Helvetica-Bold", 27)
    pdf.drawCentredString(page_width / 2, page_height - 235, recipient_name[:80])

    pdf.setFillColor(colors.HexColor("#444444"))
    pdf.setFont("Helvetica", 14)
    pdf.drawCentredString(page_width / 2, page_height - 275, f"for participating in {event_name[:120]}")

    pdf.setFont("Helvetica", 12)
    pdf.drawCentredString(page_width / 2, page_height - 315, f"Issued on {issue_date}")

    pdf.setStrokeColor(colors.HexColor("#777777"))
    pdf.line(page_width / 2 - 90, 75, page_width / 2 + 90, 75)
    pdf.setFont("Helvetica", 10)
    pdf.drawCentredString(page_width / 2, 58, "Authorized Signature")

    pdf.showPage()
    pdf.save()
    return str(output_path)
