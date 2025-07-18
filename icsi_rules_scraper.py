from pathlib import Path
from bs4 import BeautifulSoup
import pdfkit
from urllib.parse import urljoin
import base64
import json
import os
import random
import time
import requests
from playwright.sync_api import sync_playwright, Error, Page, Browser, BrowserContext
import re


os.makedirs('downloads', exist_ok=True)

# wkhtmltopdf setup
path_wkhtmltopdf = r"C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe"
config = pdfkit.configuration(wkhtmltopdf=path_wkhtmltopdf)

# Output directory
output_dir = Path("ICSI_rules")
output_dir.mkdir(exist_ok=True)


def sanitize_filename(name, max_length=100):
    # name = name.replace('\t', '_')  # Replace tab characters explicitly
    # # Replace invalid Windows filename characters with underscore
    # name = re.sub(r'[<>:"/\\|?*]', '_', name)
    # return name[:max_length]
    # Replace forbidden characters including control characters
    name = re.sub(r'[<>:"/\\|?*\n\r\t]', '_', name)
    # Replace any remaining non-printable control characters
    name = ''.join(c if c.isprintable() else '_' for c in name)
    return name.strip()[:max_length]


def backoff_retry(failure_count):
    delay = min(30, (2 ** failure_count) + random.uniform(0, 1))
    print(f"Backing off for {delay:.2f} seconds...")
    time.sleep(delay)


def download_as_pdf(pdf_url: str, download_dir: str, headers: dict[str, str], name: str = ''):
    # Pass the PDF URL as pdf_url and the directory where you want to store file as download_dir
    os.makedirs(download_dir, exist_ok=True)
    filename = name.removesuffix('\n') if name else os.path.basename(pdf_url.split("?")[0])
    save_path = os.path.join(download_dir, sanitize_filename(filename))
    cookies = {
    }

    if not save_path.lower().endswith('.pdf'):
        save_path += '.pdf'
    retries = 4
    for attempt in range(retries):
        try:
            response = requests.get(pdf_url, headers=headers, cookies=cookies)
            if response and response.status_code != 200:
                print(f"Failed to load homepage: {response.status_code}")
                backoff_retry(attempt)
                continue
            with open(save_path, "wb") as f:
                f.write(response.content)
                print(f"Downloaded to: {save_path}")
                f.close()
            if "application/pdf" not in response.headers.get("content-type", ""):
                print("Did not receive a PDF. Response content-type:", response.headers.get("content-type"))
                print("Response text:", response.text[:500])  # Print first 500 chars for debugging
                backoff_retry(attempt)
                continue
            break
        except requests.exceptions.RequestException as e:
            print(f"Error: {e}")
            backoff_retry(attempt)

def build_download_url(link, docCategory="Circulars"):
    doc = encode_link(link)
    return f"https://www.mca.gov.in/bin/ebook/dms/getdocument?doc={doc}&docCategory={docCategory}&type=open"


def encode_link(link_value):
    # Ensure link_value is a string
    link_str = str(link_value)
    encoded = base64.b64encode(link_str.encode('utf-8')).decode('utf-8')
    return encoded


def save_documents(cat: str, d_dir: str, headers: dict[str, str]):
    print(f'Saving {cat}...')
    with open(cat+'.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
        f.close()
    # yrs = set(item['notificationdate'].strip()[-4:] for item in data['data'] if 'notificationdate' in item)
    links = []
    names = []
    years = []
    if cat == 'Forms':
        for item in data['data']:
            links.append(item['docLink'])
            names.append(item['docName'] if 'docName' in item else '')
            years.append('N/A')
    else:
        for item in data['data']:
            if item['docGroup'].strip() == 'The Companies Act, 2013':
                links.append(item['link'])
                names.append(item['docName'] if 'docName' in item else '')
                years.append(item['notificationdate'].strip()[-4:] if 'notificationdate' in item else 'Unknown')
    # print(links)
    yrs = set(years)
    if years is not None and years[0] != 'N/A':
        for yr in yrs:
            os.makedirs(os.path.join(d_dir, sanitize_filename(yr)), exist_ok=True)
    for link, name, year in zip(links, names, years):
        url = build_download_url(link=link, docCategory=cat)
        # print(os.path.join(d_dir, sanitize_filename(year)))
        if year != 'N/A':
            download_as_pdf(pdf_url=url, download_dir=os.path.join(d_dir, sanitize_filename(year)), name=name, headers=headers)
        else:
            download_as_pdf(pdf_url=url, download_dir=d_dir, name=name, headers=headers)
        time.sleep(1.5)


# Sanitize filename
def sanitize_filename_2(name):
    return "".join(c if c.isalnum() or c in " ._-()" else "_" for c in name).strip()


def mca_scr():
    # Code for notifications, forms, circulars
    d_dir = "MCA_Data"
    headers = {
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "accept-language": "en-US,en;q=0.9",
        "cache-control": "max-age=0",
        "priority": "u=0, i",
        "sec-ch-ua": "\"Not)A;Brand\";v=\"8\", \"Chromium\";v=\"138\", \"Google Chrome\";v=\"138\"",
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": "\"Windows\"",
        "sec-fetch-dest": "document",
        "sec-fetch-mode": "navigate",
        "sec-fetch-site": "none",
        "sec-fetch-user": "?1",
        "upgrade-insecure-requests": "1",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36"
    }
    names = ["Forms", "Circulars", "Notifications"]
    # names = ["Notifications", "Circulars"]
    # TO DO: Add circular based filtering for forms in save_data function
    try:
        for cat in names:
            os.makedirs(sanitize_filename(cat), exist_ok=True)
            if cat == 'Forms':
                url = "https://www.mca.gov.in/bin/ebook/service/documentMetadata?docCategory=Forms&docGroup=The%20Companies%20Act%2C%202013&flag=initial"
            else:
                url = f"https://www.mca.gov.in/bin/ebook/service/documentMetadata?docCategory={cat}&flag=initial&status=Current"
            response = requests.get(url, headers=headers)
            response.raise_for_status()  # Raise exception for HTTP errors

            data = response.json()  # Parse JSON content
            # Save to local file
            with open(cat+".json", "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            print(f"JSON data saved to {cat}.json")
            save_documents(cat=cat, d_dir=os.path.join(d_dir, sanitize_filename(cat)), headers=headers)

    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")

    # Code for Rules
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        rule_pages = [
            "https://e-book.icsi.edu/Default.aspx?page=rules",
            "https://e-book.icsi.edu/Default.aspx?page=rules&rg_rulesChangePage=2"
        ]

        for page_url in rule_pages:
            page.goto(page_url)
            page.wait_for_load_state('domcontentloaded')
            page.wait_for_selector("table#rg_rules_ctl00", timeout=60000)

            print(f"📄 Processing: {page_url}")
            rule_rows = page.locator("table#rg_rules_ctl00 tbody tr")
            total_rules = rule_rows.count()
            options = {'encoding': 'UTF-8'}

            for i in range(total_rules):
                rule_rows = page.locator("table#rg_rules_ctl00 tbody tr")
                print(f"🔹 Clicking Rule Row #{i}")
                rule_rows.nth(i).click()
                time.sleep(2)

                subrule_rows = page.locator("table#rg_rules_ctl00 tbody tr")
                total_subrules = subrule_rows.count()

                for j in range(total_subrules):
                    sub_rows = page.locator("table#rg_rules_ctl00 tbody tr")  # Refresh
                    sub_row = sub_rows.nth(j)
                    sub_title = sub_row.inner_text().strip()
                    print(f"   🔸 Clicking Sub-Rule: {sub_title}")
                    sub_row.click()
                    time.sleep(2)

                    # Get iframe src
                    soup = BeautifulSoup(page.content(), "html.parser")
                    iframe_tag = soup.find('iframe', {"name": "RadWindow1"})

                    if not iframe_tag:
                        print("      ❌ No iframe found.")
                        continue

                    src = iframe_tag.get('src')
                    absolute_src = urljoin("https://e-book.icsi.edu/", src)

                    try:
                        response = requests.get(absolute_src)
                        response.raise_for_status()
                        html = response.text

                        filename = sanitize_filename_2(sub_title) + ".pdf"
                        output_path = output_dir / filename
                        pdfkit.from_string(html, str(output_path), configuration=config, options=options)

                        print(f"      ✅ Saved to {filename}")
                    except OSError as e:
                        if 'ProtocolUnknownError' in str(e):
                            print("PDF likely generated, but wkhtmltopdf reported a non-fatal ProtocolUnknownError.")
                        else:
                            print(f"      ❌ Error saving PDF for {sub_title}: {e}")
                    except Exception as e:
                        print(f"      ❌ Error saving PDF for {sub_title}: {e}")

                    # Close modal
                    try:
                        page.click("a.rwCloseButton")
                        page.wait_for_selector("iframe[name='RadWindow1']", state="hidden", timeout=10000)
                    except Exception:
                        print(f"      ⚠️ Could not close modal cleanly, continuing...")

        print("✅ All rules scraped.")
        browser.close()


mca_scr()

