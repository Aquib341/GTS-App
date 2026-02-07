from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import Table, TableStyle
from io import BytesIO
from datetime import datetime

class InvoiceGenerator:
    def __init__(self, shop_details):
        self.shop_details = shop_details

    def generate_invoice(self, customer_details, items, total_amount):
        buffer = BytesIO()
        c = canvas.Canvas(buffer, pagesize=letter)
        width, height = letter
        
        # --- Config ---
        left_margin = 50
        top_margin = height - 50
        line_height = 20

        # --- Estimate Header ---
        c.setFont("Helvetica", 8)
        c.drawCentredString(width / 2, top_margin + 20, "Estimate")
        
        # --- Header Section (Shop Info) ---
        c.setFont("Helvetica-Bold", 24)
        c.drawString(left_margin, top_margin, self.shop_details['name'])
        
        c.setFont("Helvetica", 10)
        c.setFillColor(colors.grey)
        c.drawString(left_margin, top_margin - 25, self.shop_details['address'])
        c.drawString(left_margin, top_margin - 40, f"GSTIN: {self.shop_details['gstin']}")
        c.drawString(left_margin, top_margin - 55, f"Contact: {self.shop_details['phone']}")
        c.setFillColor(colors.black)

        # --- Invoice Meta ---
        c.setFont("Helvetica-Bold", 16)
        c.drawRightString(width - 50, top_margin, "INVOICE")
        
        c.setFont("Helvetica", 10)
        invoice_no = f"INV-{int(datetime.now().timestamp())}"
        c.drawRightString(width - 50, top_margin - 25, f"Date: {datetime.now().strftime('%d-%m-%Y')}")
        c.drawRightString(width - 50, top_margin - 40, f"No: {invoice_no}")

        # --- Divider ---
        c.setStrokeColor(colors.lightgrey)
        c.line(left_margin, top_margin - 80, width - 50, top_margin - 80)

        # --- Customer Details ---
        c.setFont("Helvetica-Bold", 12)
        c.drawString(left_margin, top_margin - 110, "Bill To:")
        
        c.setFont("Helvetica", 11)
        c.drawString(left_margin, top_margin - 130, customer_details.get("name", "Walk-in Customer"))
        
        c.setFont("Helvetica", 10)
        c.setFillColor(colors.grey)
        phone = customer_details.get("phone", "")
        address = customer_details.get("address", "")
        if phone: c.drawString(left_margin, top_margin - 145, f"Phone: {phone}")
        if address: c.drawString(left_margin, top_margin - 160, f"Addr: {address}")
        c.setFillColor(colors.black)

        # --- Items Table ---
        # Data Preparation
        data = [['Item Description', 'Qty', 'Price', 'Amount']]
        for item in items:
            data.append([
                item['name'],
                str(item['qty']),
                f"{item['price']:.2f}",
                f"{item['total']:.2f}"
            ])
        
        # Add Buffer Rows if needed or just Total
        data.append(['', '', 'Grand Total:', f"{total_amount:.2f}"])

        # Table Style
        table = Table(data, colWidths=[300, 50, 80, 80])
        style = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.Color(0.2, 0.4, 0.6)), # Header Blue
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (1, 0), (-1, -1), 'RIGHT'), # Align numbers right
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
            ('TOPPADDING', (0, 0), (-1, 0), 10),
            ('GRID', (0, 0), (-1, -2), 0.5, colors.lightgrey),
            ('LINEBELOW', (0, -2), (-1, -2), 1, colors.black), # Line above Total
            ('FONTNAME', (-2, -1), (-1, -1), 'Helvetica-Bold'), # Bold Total
            ('FONTSIZE', (-2, -1), (-1, -1), 12),
            ('TEXTCOLOR', (-2, -1), (-1, -1), colors.Color(0.2, 0.4, 0.6)),
        ])
        table.setStyle(style)

        # Draw Table
        # Calculate Y position dynamically
        # Start drawing table at Y = top_margin - 200
        table_start_y = top_margin - 200
        table.wrapOn(c, width, height)
        # table.drawOn(c, left_margin, table_start_y - table._height) 
        # Better: use Flowables if lengthy, but for single page:
        w, h = table.wrap(width - 100, height)
        table.drawOn(c, left_margin, table_start_y - h)

        # --- Footer ---
        c.setFont("Helvetica-Oblique", 9)
        c.setFillColor(colors.grey)
        c.drawCentredString(width / 2, 30, "Thank you for choosing Govind Tiles & Sanitary!")
        
        c.showPage()
        c.save()
        buffer.seek(0)
        return buffer
