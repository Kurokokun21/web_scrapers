import os
from pathlib import Path
from playwright.sync_api import sync_playwright
from fpdf import FPDF

# Create output folder
output_dir = Path("ICSI_rules")
output_dir.mkdir(exist_ok=True)

# Sanitize filename for Windows
def sanitize_filename(name):
    return "".join(c if c.isalnum() or c in " ._-()" else "_" for c in name).strip()

# Save content as PDF
def save_pdf(content, filename):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    for line in content.splitlines():
        pdf.multi_cell(0, 10, line)
    pdf.output(output_dir / filename)

# Main scraper logic
with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()
    page.goto("https://e-book.icsi.edu/Default.aspx?page=rules")
    page.wait_for_load_state('domcontentloaded')
    
    # Optional debug
    page.screenshot(path="debug.png")

    # Wait for the table of rules to load
    # page.wait_for_selector("table#testTable", timeout=60000)
    page.wait_for_selector("table#rg_rules_ctl00", timeout=60000)

    rule_rows = page.locator("table#rg_rules_ctl00 tbody tr")
    total_rules = rule_rows.count()
    print(rule_rows.count())

    for i in range(total_rules):
        page.click(f"#rg_rules_ctl00__{i}")

        # Change the selectors here:
        page.wait_for_selector(f"table#rg_rules_ctl00__{i}", timeout=60000)  # Wait for sub-rule table
        
        # Now on sub-rules table
        # page.wait_for_selector(f"table#rg_rules_ctl00__{i}")
        sub_rows = page.locator(f"table#rg_rules_ctl00__{i} tbody tr")
        sub_count = sub_rows.count()

        for j in range(sub_count):
            sub_rows = page.locator("table#rg_rules_ctl00 tbody tr")  # Refresh
            sub_row = sub_rows.nth(j)
            sub_title = sub_row.inner_text().strip()
            print(f"   🔸 Clicking Sub-Rule: {sub_title}")

            with page.expect_popup() as iframe_modal_opened:
                sub_row.click()

            iframe = page.frame_locator("iframe").frame()
            iframe.wait_for_selector("body")
            content = iframe.inner_text("body")

            # Save to PDF
            filename = sanitize_filename(f"{sub_title}.pdf")
            save_pdf(content, filename)
            print(f"      ✅ Saved to {filename}")

            # Close the iframe modal
            page.click("a.rwCloseButton")
            page.wait_for_selector("iframe", state="detached")

        # Go back to main rules page
        page.go_back()
        page.wait_for_selector("table#testTable")

    print("✅ All rules scraped.")
    browser.close()

