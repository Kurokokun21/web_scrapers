# IMPORTANT:
# Run in terminal: pip install google-generativeai
# Generate the API Key first and put it in the last line before running
# Generate the key from:https://aistudio.google.com/app/apikey
# Go the website and click on 'Create API key'
# Copy the text in the textbox and paste it between the double quotes on the last line
# Run this in your terminal: pip install google-generativeai
# Now, the code can be run


import os
import time

from playwright.sync_api import sync_playwright, Page, Error
from datetime import date, timedelta
from PIL import Image
import google.generativeai as genai


def fill_date(current_date: date, page: Page):
    req_day = str(current_date.day)
    req_month = str(current_date.month)
    req_year = str(current_date.year)
    if len(req_day) == 1:
        req_day = '0' + req_day
    if current_date.month not in (10, 11, 12):
        req_month = '0' + req_month
    page.keyboard.type(req_day + '-' + req_month + '-' + req_year, delay=300)


def brics_scraper(api_key: str):
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-1.5-flash")
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
        # page.click('//button[@onclick="javascript:showCaptcha()"] >> nth=1')
        # page.click('//*[@id="frmSearch"]/fieldset[1]/div[1]/div[7]/div/button[2]')
        page.click('//button[@onclick="javascript:showCaptcha()"]')

        # Locate the image
        img_element = page.locator("img#imgCaptchaModal")

        # Take a screenshot of just the element (no need to crop manually!)
        img_element.screenshot(path="cropped_image.png")
        # Load your image
        img = Image.open("cropped_image.png")

        response = model.generate_content([
            "What text is in this image?",
            img
        ])

        print("Extracted text:", response.text)
        captcha_box = page.locator('//*[@id="captcha"]')
        captcha_box.click()  # to move focus to it
        page.keyboard.type(response.text, delay=300)
        page.keyboard.press("Enter")
        page.wait_for_load_state('domcontentloaded')
        download_path = "BRICS_NSE_Data"
        os.makedirs(download_path, exist_ok=True)
        # input("Page has stopped loading?")
        with page.expect_download() as download_info:
            page.keyboard.press("Enter")
        download = download_info.value
        save_path = os.path.join(download_path, download.suggested_filename)
        download.save_as(save_path)
        print(f"File downloaded to: {save_path}")
        # Save the data
    page.close()
    context.close()
    browser.close()


brics_scraper(api_key="")