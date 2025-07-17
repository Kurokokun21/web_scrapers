import os
import time
from pathlib import Path
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import pdfkit
import requests
from urllib.parse import urljoin

# wkhtmltopdf setup
path_wkhtmltopdf = r"C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe"
config = pdfkit.configuration(wkhtmltopdf=path_wkhtmltopdf)

# Output directory
output_dir = Path("ICSI_rules")
output_dir.mkdir(exist_ok=True)

# Sanitize filename
def sanitize_filename(name):
    return "".join(c if c.isalnum() or c in " ._-()" else "_" for c in name).strip()

# Main scraper
with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()
    page.goto("https://e-book.icsi.edu/Default.aspx?page=rules")
    page.wait_for_load_state('domcontentloaded')
    page.wait_for_selector("table#rg_rules_ctl00", timeout=60000)

    rule_rows = page.locator("table#rg_rules_ctl00 tbody tr")
    total_rules = rule_rows.count()

    for i in range(total_rules):
        page.goto("https://e-book.icsi.edu/Default.aspx?page=rules")
        print(f"🔹 Clicking Rule Row #{i}")
        page.click(f"#rg_rules_ctl00__{i}")
        time.sleep(2)

        subrule_rows = page.locator("table#rg_rules_ctl00 tbody tr")
        total_subrules = subrule_rows.count()

        for j in range(total_subrules):
            sub_rows = page.locator("table#rg_rules_ctl00 tbody tr")  # Refresh
            sub_row = sub_rows.nth(j)
            sub_title = sub_row.inner_text().strip()
            print(f"   🔸 Clicking Sub-Rule: {sub_title}")
            sub_row.click()
            time.sleep(2)

            # Get the iframe's src
            soup = BeautifulSoup(page.content(), "html.parser")
            iframe_tag = soup.find('iframe', {"name": "RadWindow1"})

            if not iframe_tag:
                print("      ❌ No iframe found.")
                continue

            src = iframe_tag.get('src')
            absolute_src = urljoin("https://e-book.icsi.edu/", src)

            try:
                response = requests.get(absolute_src)
                response.raise_for_status()
                html = response.text

                filename = sanitize_filename(sub_title) + ".pdf"
                output_path = output_dir / filename
                pdfkit.from_string(html, str(output_path), configuration=config)

                print(f"      ✅ Saved to {filename}")
            except Exception as e:
                print(f"      ❌ Error saving PDF for {sub_title}: {e}")

            # Close the modal popup
            try:
                page.click("a.rwCloseButton")
                page.wait_for_selector("iframe[name='RadWindow1']", state="detached", timeout=10000)
            except:
                print("      ⚠️ Could not close modal cleanly, continuing...")
        
    print("✅ All rules scraped.")
    browser.close()


