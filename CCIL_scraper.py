import os
import shutil
import time
import json
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
#json_converter
def json_converter(html):
    soup = BeautifulSoup(html, "html.parser")
    table = soup.find("table")

    # Extract headers from thead
    headers = [th.get_text(strip=True) for th in table.find("thead").find_all("th")]

    # Extract row data from tbody
    data = []
    for row in table.find("tbody").find_all("tr"):
        cells = row.find_all("td")
        if len(cells) == len(headers):
            row_data = {headers[i]: cells[i].get_text(strip=True) for i in range(len(headers))}
            data.append(row_data)

    # Convert to JSON
    json_output = json.dumps(data, indent=2)
    return json_output


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

            #call the json_converter() function with the html in the form of a string to convert it to json.. it returns a json file that can be stored 
            # Handle pagination

            time.sleep(2)


        time.sleep(10)
        page.close()
        context.close()
        browser.close()

ccil_scraper()
