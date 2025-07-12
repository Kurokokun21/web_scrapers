import os
from datetime import date, timedelta
from playwright.sync_api import sync_playwright

DOWNLOAD_DIR = "fbil_data"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

def fill_date_input(date_obj, input_field, page):
    input_field.click()
    input_field.click()
    formatted = date_obj.strftime("%d/%m/%Y")
    page.keyboard.type(formatted, delay=100)

def fbil_scraper():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=200)
        context = browser.new_context(accept_downloads=True)
        page = context.new_page()

        page.goto("https://www.fbil.org.in/#/home")
        page.wait_for_load_state("domcontentloaded")
        page.get_by_role("tab", name="FIXED INCOME SECURITIES").click()

        # Fill From & To date
        date_inputs = page.locator("input[placeholder='DD-MM-YYYY']")
        visible_inputs = [date_inputs.nth(i) for i in range(date_inputs.count()) if date_inputs.nth(i).is_visible()]
        fill_date_input(date.today() - timedelta(days=30), visible_inputs[0], page)
        fill_date_input(date.today(), visible_inputs[1], page)

        # Click Fetch
        fetch_buttons = page.locator("button:has-text('Fetch')")
        for i in range(fetch_buttons.count()):
            btn = fetch_buttons.nth(i)
            if btn.is_visible():
                btn.click()
                break

        # Wait for results
        page.wait_for_selector("table#Gsec tbody tr")
        rows = page.locator("table#Gsec tbody tr")
        row_count = rows.count()

        for i in range(row_count):
            # 🔁 Make sure modal is closed before proceeding
            try:
                if page.locator("#downloadPrompt").is_visible():
                    close_btn = page.locator("button[data-dismiss='modal']")
                    if close_btn.is_visible():
                        close_btn.click()
                        page.wait_for_selector("#downloadPrompt", state="hidden", timeout=5000)
            except:
                pass  # Modal already closed

            row = rows.nth(i)

            # Get date
            date_text = row.locator("td").nth(0).locator("div").inner_text().strip()
            file_base_name = f"{date_text.replace(' ', '_')}.xlsx"
            print(f"Processing: {file_base_name}")

            # Click link
            link = row.locator("a", has_text="FBIL GOI Prices")
            try:
                link.click()
                page.wait_for_selector("#downloadPrompt", state="visible", timeout=5000)

                # Locate the Download Excel button by icon
                download_button = page.locator("button:has(.fa-file-excel-o)")
                download_button.wait_for(state="visible", timeout=5000)

                # Start download
                with page.expect_download() as download_info:
                    download_button.click()

                download = download_info.value
                download.save_as(os.path.join(DOWNLOAD_DIR, file_base_name))
                print(f"✅ Saved: {file_base_name}")

            except Exception as e:
                print(f"❌ Download failed for {date_text}: {e}")

            finally:
                # Try to close modal always
                try:
                    close_btn = page.locator("button[data-dismiss='modal']")
                    if close_btn.is_visible():
                        close_btn.click()
                        page.wait_for_selector("#downloadPrompt", state="hidden", timeout=5000)
                except:
                    pass

        page.close()
        context.close()
        browser.close()

fbil_scraper()
