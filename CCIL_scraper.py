import datetime
import os
import re
import shutil
import string
import time
import json
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright, Page, Error
from datetime import datetime, date, timedelta

#json_converter
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
        # Skip first two non-functional rows
        if len(rows) <= 2:
            raise ValueError("Table does not have enough rows after skipping two.")
        header_cells = rows[2].find_all(['td', 'th'])
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


def get_calendar_month_title(page: Page):
    try:
        return page.inner_text("#ctl00_SuperMainContent_cleFrmDealDate_title")
    except Error as e:
        return page.inner_text("#ctl00_SuperMainContent_txtFrmDealDate_CalendarExtender_title")


def save_json(data: str, name: str):
    download_path = os.path.join(os.path.abspath("CCIL_India_Data"), name+".json")
    with open(download_path, "w") as f:
        f.write(data)
    f.close()


def download_market_data(page: Page, calender_icon: string = 'input#ctl00_SuperMainContent_imbFrmDate', prev_arrow: string ="#ctl00_SuperMainContent_cleFrmDealDate_prevArrow", next_arrow: string = "#ctl00_SuperMainContent_cleFrmDealDate_nextArrow"):
    fill_date = date.today() - timedelta(days=30)
    if calender_icon is None:
        calender_icon = 'input#ctl00_SuperMainContent_imbFrmDate'
    if prev_arrow is None:
        prev_arrow = "#ctl00_SuperMainContent_cleFrmDealDate_prevArrow"
    if next_arrow is None:
        next_arrow = "#ctl00_SuperMainContent_cleFrmDealDate_nextArrow"

    max_tries = 50  # prevent infinite loop

    for _ in range(max_tries):
        current_title = get_calendar_month_title(page)
        # Example title: "June, 2025"
        if current_title == fill_date.strftime("%B, %Y"):
            # select day
            target_title = fill_date.strftime("%A, %B %d, %Y")

            # Locate the day cell by matching its title attribute exactly
            day_locator = page.locator(f"div.ajax__calendar_day[title='{target_title}']")

            # Wait for it to appear, then click it
            day_locator.wait_for(state="visible", timeout=5000)
            day_locator.click()
            break
        # Decide if we should go next or prev:
        displayed_date = datetime.strptime(current_title, "%B, %Y").date()
        if displayed_date < fill_date:
            page.click(next_arrow)
        else:
            page.click(prev_arrow)
        time.sleep(0.3)  # Give calendar time to update

    else:
        raise RuntimeError("Calendar navigation failed to reach desired month/year")

    # Click on export button to export as excel
    with page.expect_download() as download_info:
        page.click('input#ctl00_SuperMainContent_btnExprtExcel')
    download = download_info.value
    temp_file_path = download.path()
    download_path = os.path.abspath("CCIL_India_Data")
    final_file_path = os.path.join(download_path, temp_file_path.name) + ".xls"
    shutil.move(temp_file_path, final_file_path)


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
        links = []
        for a in target_li[3].find_all("a", href=True):
            if a['href'] != '':
                links.append(a['href'])

        folder_name = f"CCIL_India_Data"
        os.makedirs(folder_name, exist_ok=True)

        for link in links:
            page.goto(link)
            page.wait_for_load_state('domcontentloaded')
            print('Visiting: '+link)
            # For selected websites which require further navigation:
            if link == 'https://www.ccilindia.com/web/ccil/primary-and-secondary-market':
                """
                soup = BeautifulSoup(page.content(), "html.parser")
                table_link = soup.find("table")
                for a in table_link.find_all("a", href=True):
                    page.goto(a['href'])
                    page.wait_for_load_state('domcontentloaded')
                    time.sleep(1)
                    # get the ids for relevant extraction:
                    print(page.content())
                    sp = BeautifulSoup(page.content(), "html.parser")
                    # for div in sp.find_all("div"):
                    #     if div.has_attr("class"):
                    #         print(div)
                    # print()

                    calender_icon = sp.find("input", type="image", attrs={"src": lambda value: value and "Images/calendar.jpg" in value})
                    if calender_icon and calender_icon.has_attr("id"):
                        calender_icon = '#'+calender_icon['id']
                    page.click(calender_icon, timeout=30000)
                    page.wait_for_load_state('domcontentloaded')
                    next_arrow = sp.find("div", class_=re.compile(r"ajax__calendar_next"))
                    if next_arrow and next_arrow.has_attr("id"):
                        next_arrow = '#'+next_arrow['id']
                    prev_arrow = sp.find("div", class_=re.compile(r"ajax__calendar_prev"))
                    if prev_arrow and prev_arrow.has_attr("id"):
                        prev_arrow = '#'+prev_arrow['id']
                    print(calender_icon)
                    print(next_arrow)
                    print(prev_arrow)
                    download_market_data(page=page, calender_icon=calender_icon, prev_arrow=prev_arrow, next_arrow=next_arrow)
                    """
            else:
                # Get filename from url
                file_name = page.url.split('/')[-1]

                # Check if page already has table
                soup = BeautifulSoup(page.content(), "html.parser")
                table = str(soup.find('table'))
                if table!='None':
                    # Call the json_converter() function with the html in the form of a string to convert it to json.. it returns a json file that can be stored
                    table_json = json_converter(table)
                    save_json(table_json, file_name)
                    print(f"table at: {page.url} saved successfully")
                    # Handle pagination
                    continue
                elif not soup.find('div', class_=['layout-frame', 'mr-1']).get_text(strip=True):
                    print(f'No text found at: {page.url}. Continuing...')
                    continue
                iframe_locator = page.locator("iframe[src*='r.ccilindia.com/jasperserver']")
                iframe_locator.wait_for(timeout=15000)

                iframe_src = iframe_locator.get_attribute("src")
                # Access actual resource page from shadow DOM
                page.goto(iframe_src)
                page.wait_for_load_state('domcontentloaded')
                time.sleep(2)
                soup = BeautifulSoup(page.content(), "html.parser")
                # partial match with re.compile()
                err_message = soup.find(string=re.compile(r"You must apply input values"))
                req_tag = soup.find_all("input", class_=['date', 'hasDatepicker'])
                from_id = ""
                to_id = ""
                if req_tag:
                    from_id = req_tag[0]['id']
                    to_id = req_tag[1]['id']
                if err_message:
                    # Fill the date in from
                    current_date = date.today() - timedelta(days=30)
                    date_loc = page.locator('input#'+from_id)
                    date_loc.click()  # to move focus to it
                    req_day = str(current_date.day)
                    req_month = str(current_date.month)
                    req_year = str(current_date.year)
                    if len(req_day) == 1:
                        req_day = '0' + req_day
                    if current_date.month not in (10, 11, 12):
                        req_month = '0' + req_month
                    page.keyboard.type(req_day + '-' + req_month + '-' + req_year, delay=300)
                    # Fill the date in 'To'
                    current_date = date.today()
                    date_loc = page.locator('input#'+to_id)
                    date_loc.click()  # to move focus to it
                    req_day = str(current_date.day)
                    req_month = str(current_date.month)
                    req_year = str(current_date.year)
                    if len(req_day) == 1:
                        req_day = '0' + req_day
                    if current_date.month not in (10, 11, 12):
                        req_month = '0' + req_month
                    page.keyboard.type(req_day + '-' + req_month + '-' + req_year, delay=300)
                    # Click 'Apply':
                    page.click('button#apply')
                    page.wait_for_load_state('domcontentloaded')
                    time.sleep(2)

                soup = BeautifulSoup(page.content(), 'html.parser')
                table = str(soup.find('table', id='JR_PAGE_ANCHOR_0_1'))
                if table!='None':
                    # Call the json_converter() function with the html in the form of a string to convert it to json.. it returns a json file that can be stored
                    table_json = json_converter(table)
                    save_json(table_json, file_name)
                    print(f"table at: {page.url} saved successfully")
                    # Handle pagination
                else:
                    print(f'Table at {page.url} not found')

            time.sleep(2)


        time.sleep(10)
        page.close()
        context.close()
        browser.close()

ccil_scraper()
