import os
import shutil
import time

from playwright.sync_api import sync_playwright, Page, Error
from datetime import date, timedelta
from PIL import Image
import pytesseract


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

        time.sleep(10)
    page.close()
    context.close()
    browser.close()


brics_scraper()