import os
import shutil
import time

from playwright.sync_api import sync_playwright, Page, Error
from datetime import date, timedelta
from PIL import Image
import pytesseract

pytesseract.pytesseract.tesseract_cmd = r"C:\Users\schir\AppData\Local\Programs\Tesseract-OCR\tesseract.exe"


def fill_date(current_date: date, page: Page):
    req_day = str(current_date.day)
    req_month = str(current_date.month)
    req_year = str(current_date.year)
    if len(req_day) == 1:
        req_day = '0' + req_day
    if current_date.month not in (10, 11, 12):
        req_month = '0' + req_month
    page.keyboard.type(req_day + '-' + req_month + '-' + req_year, delay=300)

def brics_scraper():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=300)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        page.goto('https://bricsonline.nseindia.com/bondsnew/rest/public?r=sebiannexure1')
        page.wait_for_load_state('domcontentloaded')
        # Fill the date (before). Current date is already filled.
        selector = 'input[placeholder="From Date"][data-role="datetimepicker"]'
        page.click(selector) # To move focus to textbox
        page.fill(selector, "")
        fill_date(page=page, current_date=date.today()-timedelta(days=7))
        # CLick the button which shows CAPTCHA
        page.locator('//button[contains(@onclick, "showCaptcha(true)")]').click()

        # Use Tesseract to solve captcha
        # Locate the image
        img_element = page.locator("img#imgCaptchaModal")

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
        custom_config = r'--psm 8 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'

        # Extract text
        extracted_text = pytesseract.image_to_string(bw, config=custom_config)
        print("Extracted text:", extracted_text)
        captcha_box = page.locator('//*[@id="captcha"]')
        captcha_box.click()  # to move focus to it
        page.keyboard.type(extracted_text, delay=300)
        page.wait_for_load_state('domcontentloaded')

        time.sleep(10)
        # Save the data

        time.sleep(10)
    page.close()
    context.close()
    browser.close()


brics_scraper()