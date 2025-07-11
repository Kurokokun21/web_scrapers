import datetime
import os
import re
import shutil
import string
import time
import json
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright, Page, Error, Locator
from datetime import datetime, date, timedelta


def fill_date(current_date: date, date_loc: Locator, page: Page):
    date_loc.click()  # to move focus to it
    date_loc.click()  # to move focus to textbox
    req_day = str(current_date.day)
    req_month = str(current_date.month)
    req_year = str(current_date.year)
    if len(req_day) == 1:
        req_day = '0' + req_day
    if current_date.month not in (10, 11, 12):
        req_month = '0' + req_month
    page.keyboard.type(req_day + '/' + req_month + '/' + req_year, delay=300)


def fbil_scraper():
    # The scraper captures data for 1 month (including today)
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=300)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        page.goto('https://www.fbil.org.in/#/home')
        page.wait_for_load_state('domcontentloaded')
        page.get_by_role("tab", name="FIXED INCOME SECURITIES").click()
        # Get all matching locators
        date_inputs = page.locator("input[placeholder='DD-MM-YYYY']")

        # Filter only visible ones
        visible_inputs = [date_inputs.nth(i) for i in range(date_inputs.count()) if date_inputs.nth(i).is_visible()]

        # Fill 1st date
        l1 = visible_inputs[0]
        fill_date(current_date=date.today()-timedelta(days=30), date_loc=l1, page = page)

        # Fill second date input (e.g., "To" date)
        l2 = visible_inputs[1]
        fill_date(current_date=date.today(), date_loc=l2, page = page)

        buttons = page.locator("button:has-text('Fetch')")
        count = buttons.count()

        visible_button = None

        for i in range(count):
            btn = buttons.nth(i)
            if btn.is_visible():
                visible_button = btn
                break

        if visible_button:
            print("Found visible 'Fetch' button.")
            # Now you can use it like this:
            visible_button.click()
        else:
            print("No visible 'Fetch' button found.")

        # Continue here:

        time.sleep(10)

        page.close()
        context.close()
        browser.close()

fbil_scraper()
