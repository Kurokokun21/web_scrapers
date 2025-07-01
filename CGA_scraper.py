import os
import pdfkit

folder_name = "cga_report"
os.makedirs(folder_name, exist_ok=True)

def pdf_converter(html , num):
    # --- Step 1: Final PDF file path ---
    pdf_filename = os.path.join(folder_name, f"report_{num}.pdf")

    # --- Step 2: wkhtmltopdf configuration (only needed on Windows) ---
    # Change the path below if it's installed elsewhere
    pdfkit_config = pdfkit.configuration(
        wkhtmltopdf=r"C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe"
    )

    # --- Step 3: Convert HTML string to PDF ---
    pdfkit.from_string(html, pdf_filename, configuration=pdfkit_config)

    print(f"✅ PDF saved at: {pdf_filename}")

