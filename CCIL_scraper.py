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
        return page.inner_text("#ctl00_SuperMainContent_cleFrmDealDate_title", timeout=1000)
    except Error as e:
        return page.inner_text("#ctl00_SuperMainContent_txtFrmDealDate_CalendarExtender_title")


def save_json(data: str, name: str):
    download_path = os.path.join(os.path.abspath("CCIL_India_Data"), name+".json")
    with open(download_path, "w") as f:
        f.write(data)
    f.close()


def download_market_data(page: Page, calender_icon: string = 'input#ctl00_SuperMainContent_imbFrmDate', prev_arrow: string ="#ctl00_SuperMainContent_cleFrmDealDate_prevArrow", next_arrow: string = "#ctl00_SuperMainContent_cleFrmDealDate_nextArrow"):
    filename = (page.url.split('/')[-1]).split('.')[0]
    fill_date = date.today() - timedelta(days=7)
    if calender_icon is None:
        calender_icon += 'input#ctl00_SuperMainContent_imbFrmDate'
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
    final_file_path = os.path.join(download_path, filename) + ".xls"
    shutil.move(temp_file_path, final_file_path)


def ccil_scraper(l: list[str]):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, slow_mo=300)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        links = []
        if not l:
            page.goto('https://www.ccilindia.com/web/ccil/home')
            page.wait_for_load_state('domcontentloaded')
            html = page.content()
            soup = BeautifulSoup(html, "html.parser")
            target_li = soup.select("li.nav-item.dropdown.megamenu")
            for a in target_li[3].find_all("a", href=True):
                if a['href'] != '':
                    links.append(a['href'])
        else:
            links = l

        folder_name = f"CCIL_India_Data"
        os.makedirs(folder_name, exist_ok=True)
        for link in links:
            page.goto(link)
            page.wait_for_load_state('domcontentloaded')
            print('Visiting: '+link)
            # For selected websites which require further navigation:
            if link == 'https://www.ccilindia.com/web/ccil/primary-and-secondary-market':

                soup = BeautifulSoup(page.content(), "html.parser")
                table_link = soup.find("table")
                for a in table_link.find_all("a", href=True):
                    page.goto(a['href'])
                    page.wait_for_load_state('domcontentloaded')
                    time.sleep(1)
                    # get the ids for relevant extraction:
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
                    download_market_data(page=page, calender_icon=calender_icon, prev_arrow=prev_arrow, next_arrow=next_arrow)
                    print('Tables saved successfully')
            else:
                # Get filename from url
                file_name = page.url.split('/')[-1]

                # Check if page already has table
                soup = BeautifulSoup(page.content(), "html.parser")
                table = str(soup.find('table'))
                if table != 'None':
                    # Select max no of entries:
                    selector = "select:not(.form-control)"
                    # Grab all <option> elements inside your select
                    options = page.query_selector_all(f"{selector} option")
                    max_val = None

                    for option in options:
                        val = option.get_attribute("value")
                        try:
                            num = int(val)
                            if max_val is None or num > max_val:
                                max_val = num
                        except (TypeError, ValueError):
                            continue

                    if max_val is not None:
                        print(f"Selecting option with highest value: {max_val}")
                        page.select_option(selector, value=str(max_val))
                    else:
                        print("No valid options found")
                    # Get no of pages
                    page_txt = soup.find('div', class_='dataTables_info').text
                    match = re.search(r'of\s+(\d+)\s+entries', page_txt)
                    num_pages = 0
                    if match and max_val is not None:
                        num_pages = int(match.group(1))//max_val # max_val = no of entries in a page

                    print('No. of pages: '+str(num_pages))
                    table_json = ""
                    for i in range(num_pages+1):
                        # Call the json_converter() function with the html in the form of a string to convert it to json.. it returns a json file that can be stored
                        if i == 0:
                            table_json = json_converter(table)
                        else:
                            # Handle pagination: click '>'
                            nxt_btns = page.query_selector_all('a.paginate_button.next')
                            for btn in nxt_btns:
                                if btn.is_visible():
                                    btn.click()
                                    break
                            else:
                                print("No visible 'next' button found!")
                            page.wait_for_timeout(5000)
                            sp = BeautifulSoup(page.content(), 'html.parser')
                            # Reload table
                            table = str(sp.find('table'))
                            list1 = json.loads(table_json)
                            list2 = json.loads(json_converter(table))
                            list1 += list2
                            table_json = json.dumps(list1, indent=2)

                    save_json(table_json, file_name)
                    print(f"table at: {page.url} saved successfully")
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

                # Get number of pages
                soup = BeautifulSoup(page.content(), 'html.parser')
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
                            page.fill('input#page_current', str(i+1))
                            page.keyboard.press("Enter")
                            page.wait_for_timeout(2000)
                            sp = BeautifulSoup(page.content(), 'html.parser')
                            # Reload table
                            table = str(sp.find('table', id='JR_PAGE_ANCHOR_0_'+str(i+1)))
                            list1 = json.loads(table_json)
                            list2 = json.loads(json_converter(table))
                            list1 += list2
                            table_json = json.dumps(list1, indent=2)

                    save_json(table_json, file_name)
                    print(f"table at: {page.url} saved successfully")
                else:
                    print('Table not found')

            time.sleep(2)

        page.close()
        context.close()
        browser.close()


if __name__ == '__main__':
    ccil_scraper([])
