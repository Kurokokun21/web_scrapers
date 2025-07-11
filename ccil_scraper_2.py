import datetime
import os
import re
import shutil
import string
import time
import json

import requests
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright, Page, Error
from datetime import datetime, date, timedelta
import CCIL_scraper

def json_converter(html):
    soup = BeautifulSoup(html, "html.parser")
    table = soup.find("table")

    # Extract headers from thead
    data = []
    if table.find("thead") is not None:
        headers = [th.get_text(strip=True) for th in table.find("thead").find_all("th")]
        # Extract row data from tbody
        for row in table.find("tbody").find_all("tr"):
            cells = row.find_all("td")
            if len(cells) == len(headers):
                row_data = {headers[i]: cells[i].get_text(strip=True) for i in range(len(headers))}
                data.append(row_data)

    else:
        rows = table.find_all('tr')
        # Skip first two non-functional rows and the header
        if len(rows) <= 3:
            raise ValueError("Table does not have enough rows after skipping two.")
        header_cells = rows[3].find_all(['td', 'th'])
        headers = [cell.get_text(strip=True) for cell in header_cells]
        for row in rows[3:]:  # start from row 4 (index 3)
            cells = row.find_all(['td', 'th'])
            values = [cell.get_text(strip=True) for cell in cells]
            # Skip incomplete rows that don't match header length
            if len(values) == len(headers):
                data.append(dict(zip(headers, values)))

    # Convert to JSON
    json_output = json.dumps(data, indent=2)
    return json_output


def save_json(data: str, name: str):
    download_path = os.path.join(os.path.abspath("CCIL_India_Data"), name+".json")
    with open(download_path, "w") as f:
        f.write(data)
    f.close()


def fill_date(current_date: date, to_id: string, page: Page):
    date_loc = page.locator('input#' + to_id)
    date_loc.click()  # to move focus to it
    page.fill(f'input[name={to_id}]', current_date.isoformat())


def api_call_data(url: string, form_data: dict[str, str], headers: dict[str, str], is_data: bool):
    filename = headers["referer"].split('/')[-1]
    # API URL
    num_pages = 22  # fix later -> extract from webpage
    all_rows = []
    for i in range(num_pages):
        form_data["draw"] = str(i+1)
        response = requests.post(url, data=form_data, headers=headers)
        full_response = response.json()
        # print(full_response)
        if is_data:
            columns_to_keep = ["HighPrice", "HighYield", "LowPrice", "LowYield", "MaturityDate", "Volume", "WtdAvgPrice",
                               "WtdAvgYield"]
            filtered_data = [
                {k: row[k] for k in columns_to_keep if k in row}
                for row in full_response["data"]
            ]
            all_rows.extend(filtered_data)
        else:
            all_rows.extend(full_response)
        time.sleep(1)

    combined_data = json.dumps(all_rows, indent=4)
    save_json(data=combined_data, name=filename)


def ccil_scraper_2():
    # To avoid syncing issues with playwright:
    # For 3rd website:
    # https://www.ccilindia.com/web/ccil/client-bondfra -> archival data already collected by prev scraper, can be adjusted if necessary
    CCIL_scraper.ccil_scraper(['https://www.ccilindia.com/web/ccil/client-bondfra1'])
    print()
    print('Done with 3rd website. Continuing...')
    print()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, slow_mo=300)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        date1 = (date.today() - timedelta(days=30)).isoformat()
        date2 = (date.today()).isoformat()
        print('Running...')

        # 1st website -> API call
        form_data = {
            "draw": "1",
            "columns[0][data]": "Date",
            "columns[0][searchable]": "true",
            "columns[0][orderable]": "true",
            "_NewVolumeTradeMVC_NewVolumeTradeMVCPortlet_INSTANCE_qpnj_fromDate1": date1,
            "_NewVolumeTradeMVC_NewVolumeTradeMVCPortlet_INSTANCE_qpnj_toDate1": date2,
            "_NewVolumeTradeMVC_NewVolumeTradeMVCPortlet_INSTANCE_qpnj_cgs": "cgs",
            "_NewVolumeTradeMVC_NewVolumeTradeMVCPortlet_INSTANCE_qpnj_searchClicked": "true",
            "_NewVolumeTradeMVC_NewVolumeTradeMVCPortlet_INSTANCE_qpnj_hidFrom": "fhZZbHQhWKRghEXQRiirSg==",
            "_NewVolumeTradeMVC_NewVolumeTradeMVCPortlet_INSTANCE_qpnj_hidTo": "LFV8BAhOUgvJRKK05OppPg=="
        }

        headers = {
            "accept": "application/json, text/javascript, */*; q=0.01",
            "accept-language": "en-US,en;q=0.9",
            "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
            "origin": "https://www.ccilindia.com",
            "referer": "https://www.ccilindia.com/web/ccil/volumewise-outright-trade",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36 Edg/138.0.0.0",
            "x-requested-with": "XMLHttpRequest"
        }
        api_call_data(is_data=True, url="https://www.ccilindia.com/web/ccil/volumewise-outright-trade?p_p_id=NewVolumeTradeMVC_NewVolumeTradeMVCPortlet_INSTANCE_qpnj&p_p_lifecycle=2&p_p_state=normal&p_p_mode=view&p_p_resource_id=searchClicked&p_p_cacheability=cacheLevelPage&_NewVolumeTradeMVC_NewVolumeTradeMVCPortlet_INSTANCE_qpnj_cmd=jsonUserObjectArray1", form_data=form_data, headers=headers)
        # Next website:
        print()
        print('Done with 1st website. Continuing...')
        print()
        headers = {
            "accept": "application/json, text/javascript, */*; q=0.01",
            "accept-language": "en-US,en;q=0.9",
            "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
            "origin": "https://www.ccilindia.com",
            "referer": "https://www.ccilindia.com/web/ccil/security-wise-repo-market-summary",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36 Edg/138.0.0.0",
            "x-requested-with": "XMLHttpRequest",
        }
        form_data = {
            "draw": "1",
            "columns[0][data]": "Date",
            "columns[0][name]": "",
            "columns[0][searchable]": "true",
            "columns[0][orderable]": "false",
            "columns[0][search][value]": "",
            "columns[0][search][regex]": "false",
            "_SecurityWiseRepoMarketSummaryMvc_SecurityWiseRepoMarketSummaryMvcPortlet_INSTANCE_rcai_fromDate1": "2025-06-10",
            "_SecurityWiseRepoMarketSummaryMvc_SecurityWiseRepoMarketSummaryMvcPortlet_INSTANCE_rcai_toDate1": "2025-07-10",
            "_SecurityWiseRepoMarketSummaryMvc_SecurityWiseRepoMarketSummaryMvcPortlet_INSTANCE_rcai_searchClicked": "true"
        }

        api_call_data(is_data=False, url="https://www.ccilindia.com/web/ccil/security-wise-repo-market-summary?p_p_id=SecurityWiseRepoMarketSummaryMvc_SecurityWiseRepoMarketSummaryMvcPortlet_INSTANCE_rcai&p_p_lifecycle=2&p_p_state=normal&p_p_mode=view&p_p_resource_id=searchNotClicked&p_p_cacheability=cacheLevelPage&_SecurityWiseRepoMarketSummaryMvc_SecurityWiseRepoMarketSummaryMvcPortlet_INSTANCE_rcai_cmd=jsonUserObjectArray", form_data=form_data, headers=headers)

        print()
        print('Done with 2nd website. Continuing...')
        print()

        # For 4th website:
        page.goto('https://www.ccilindia.com/web/ccil/client-inr-interest-rate-trades')
        fill_date(page=page, current_date=date.today()-timedelta(days=30), to_id='from')
        fill_date(page=page, current_date=date.today(), to_id='to')
        # Click apply
        page.click('button.t1')
        iframe_locators = page.locator("iframe[src*='r.ccilindia.com/jasperserver']").all()
        srcs = []
        for i in range(len(iframe_locators)):
            iframe_locator = iframe_locators[i]
            iframe_src = iframe_locator.get_attribute("src")
            srcs.append(iframe_src)
        for iframe_src in srcs:
            # Access actual resource page from shadow DOM
            page.goto(iframe_src)
            page.wait_for_load_state('domcontentloaded')
            time.sleep(3)
            # Get name
            soup = BeautifulSoup(page.content(), 'html.parser')
            td = soup.find('td', class_='jrcolGroupHeader')
            if td:
                name = td.find('span').text.strip()
            else:
                name = 'Benchmark- INCMTBMK (INR)'
            # Get number of pages
            text = soup.find('span', id='page_total').text
            text = text.replace('\u00A0', ' ').replace('&nbsp;', ' ')
            match = re.search(r'of\s+(\d+)', text, re.IGNORECASE)
            num_pages = 0
            if match:
                num_pages = int(match.group(1))
                print(num_pages)
            else:
                print("No match found for number of pages")
                continue
            table = str(soup.find('table', id='JR_PAGE_ANCHOR_0_1'))
            # get data:
            if table != 'None':
                for i in range(num_pages):
                    # Call the json_converter() function with the html in the form of a string to convert it to json.. it returns a json file that can be stored
                    if i == 0:
                        table_json = json_converter(table)
                    else:
                        # Handle pagination: type next page and press enter
                        page.fill('input#page_current', str(i + 1))
                        page.keyboard.press("Enter")
                        page.wait_for_timeout(2000)
                        sp = BeautifulSoup(page.content(), 'html.parser')
                        # Reload table
                        table = str(sp.find('table', id='JR_PAGE_ANCHOR_0_' + str(i + 1)))
                        list1 = json.loads(table_json)
                        list2 = json.loads(json_converter(table))
                        list1 += list2
                        table_json = json.dumps(list1, indent=2)

                save_json(table_json, name)
                print(f"table at: {page.url} saved successfully")
            else:
                print('Table not found')

        print()
        print('Done with last website. Exiting...')
        print()
        page.close()
        context.close()
        browser.close()


ccil_scraper_2()
