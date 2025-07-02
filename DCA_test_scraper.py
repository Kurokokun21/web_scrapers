import os
import shutil
import time

from playwright.sync_api import sync_playwright, Page, Error
from datetime import date, timedelta
from PIL import Image
import pytesseract

# Set this to the path of your Tesseract.exe file:
pytesseract.pytesseract.tesseract_cmd = r"C:\Users\schir\AppData\Local\Programs\Tesseract-OCR\tesseract.exe"




def on_popup(new_page):
    folder_name = f"DCA_Data"
    download_path = os.path.abspath(folder_name)
    os.makedirs(download_path, exist_ok=True)

    print("New tab detected:", new_page.url)
    new_page.wait_for_load_state('domcontentloaded')
    if 'The specified URL is inaccessible at this time. Please try after some time' in new_page.content():
        print('Inaccessible')
        return
    else:
        # Save the data
        with new_page.expect_download() as download_info:
            new_page.click('input#btnsave')
        download = download_info.value
        temp_file_path = download.path()
        new_filename = f"Report_"
        table = new_page.locator("table")  # or a more specific selector, e.g. table#myTable
        # Then find text inside that table:
        if table.locator(":text('Wholesale')").count() > 0:
            new_filename += "Wholesale"
        if table.locator(":text('Retail')").count() > 0:
            new_filename += "Retail"
        new_filename += ".xls"
        final_file_path = os.path.join(download_path, new_filename)
        shutil.move(temp_file_path, final_file_path)

        print(f"✅ File downloaded and saved as: {final_file_path}")

        time.sleep(2)
        return


def handle_other_categories(page: Page, manual_captcha: bool):
    # Select Price report
    page.get_by_label("Price report").click()
    page.wait_for_load_state('domcontentloaded')
    time.sleep(2)
    # Select daily prices
    # Select dropdowns for daily prices
    price_dropdown = page.locator("select#ctl00_MainContent_Ddl_Rpt_Option0").first
    price_dropdown.click()
    price_dropdown.wait_for(state="visible")
    # Select retail
    options = price_dropdown.locator("option").all_inner_texts()
    page.evaluate("""
      ([selId, value]) => {
        const sel = document.getElementById(selId);
        if (!sel) throw new Error("Dropdown element not found: " + selId);
        sel.value = value;
        sel.dispatchEvent(new Event('change', { bubbles: true }));
      }
    """, ["ctl00_MainContent_Ddl_Rpt_Option0", "Daily Prices"])

    print('Successfully selected Daily Prices')

    # Fill the date
    current_date = date.today() - timedelta(days=1)
    date_loc = page.locator('input#ctl00_MainContent_Txt_FrmDate')
    date_loc.click()  # to move focus to it
    # while True:
    req_day = str(current_date.day)
    req_month = str(current_date.month)
    req_year = str(current_date.year)
    if len(req_day) == 1:
        req_day = '0' + req_day
    if current_date.month not in (10, 11, 12):
        req_month = '0' + req_month
    page.keyboard.type(req_day + '/' + req_month + '/' + req_year, delay=300)

    current_date -= timedelta(days=1)  # Go back one day each time

    if manual_captcha:
        input('Solve CAPTCHA...')
    else:
        img_element = page.locator("img#ctl00_MainContent_captchalogin")

        # Take a screenshot of just the element (no need to crop manually!)
        img_element.screenshot(path="cropped_image.png")
        image = Image.open("cropped_image.png")
        # Optional preprocessing: convert to grayscale (can improve OCR on simple captchas)
        image = image.convert("L")
        image = image.resize((image.width * 4, image.height * 4), Image.LANCZOS)
        image = image.point(lambda x: 0 if x < 140 else 255, "1")  # binarize

        # Simple binary threshold
        threshold = 150
        bw = image.point(lambda x: 0 if x < threshold else 255, '1')
        bw.save("preprocessed.png")

        # Run Tesseract OCR with recommended config for captchas:
        # --psm 7 = treat image as a single text line
        # tessedit_char_whitelist = limit recognized chars to letters/numbers you expect
        custom_config = r'--psm 7 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'

        # Extract text
        extracted_text = pytesseract.image_to_string(bw, config=custom_config)
        print("Extracted text:", extracted_text)
        captcha_box = page.locator('input#ctl00_MainContent_Captcha')
        captcha_box.click()  # to move focus to it
        page.keyboard.type(extracted_text, delay=300)

    print('Opening page...')
    # context.on("page", on_popup)
    # with page.expect_navigation(wait_until="domcontentloaded", timeout=60000) as nav:
    # page.click("#ctl00_MainContent_btn_getdata1", timeout=0, no_wait_after=True)
    print("Dispatching manual click via evaluate()...")
    try:
        page.evaluate("document.querySelector('#ctl00_MainContent_btn_getdata1').click()")
    except Exception as e:
        if "Execution context was destroyed" in str(e):
            print("✅ Click triggered navigation; continuing...")
        else:
            print(page.url)
            raise  # re-raise unexpected errors
    print('processing...')
    time.sleep(2)
    on_popup(page)

def dca_scraper(manual_captcha=False):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=300)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        page.goto('https://fcainfoweb.nic.in/reports/Report_Menu_Web.aspx')
        page.wait_for_load_state('domcontentloaded')
        # Select dropdowns for retail reports
        retail_dropdown = page.locator("select#ctl00_MainContent_Ddl_Rpt_type").first
        retail_dropdown.click()
        retail_dropdown.wait_for(state="visible")
        # Select retail
        retail_dropdown.select_option("Retail")
        print('Successfully selected Retail')
        handle_other_categories(page=page, manual_captcha=manual_captcha)

        page.goto('https://fcainfoweb.nic.in/reports/Report_Menu_Web.aspx')
        page.wait_for_load_state('domcontentloaded')

        # Select dropdowns for wholesale reports
        wholesale_dropdown = page.locator("select#ctl00_MainContent_Ddl_Rpt_type").first
        wholesale_dropdown.click()
        wholesale_dropdown.wait_for(state="visible")
        # Select wholesale
        wholesale_dropdown.select_option("Wholesale")
        print('Successfully selected Wholesale')
        handle_other_categories(page=page, manual_captcha=manual_captcha)

        print('Finished final call')
        # Fill the date
        # page.click("#ctl00_MainContent_btn_getdata1", modifiers=["Control"])
        # page.wait_for_timeout(5000)  # adjust as needed

        page.close()
        context.close()
        browser.close()


dca_scraper()






