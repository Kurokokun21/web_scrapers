import os
import shutil
import time

from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

def ccil_scraper():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=300)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        page.goto('https://www.ccilindia.com/web/ccil/home')
        page.wait_for_load_state('domcontentloaded')
        html = page.content()
        soup = BeautifulSoup(html, "html.parser")
        target_li = soup.select("li.nav-item.dropdown.megamenu")
        print(len(target_li))
        links = []
        for a in target_li[3].find_all("a", href=True):
            if a['href'] != '':
                links.append(a['href'])

        for link in links:
            page.goto(link)
            # Extract table data and convert to json
            # Handle pagination

            time.sleep(2)


        time.sleep(10)
        page.close()
        context.close()
        browser.close()

ccil_scraper()