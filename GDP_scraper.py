import os
import re
import string
import time

import requests
from playwright.sync_api import sync_playwright, Error, Page
from bs4 import BeautifulSoup, Tag

def sanitize_filename(name, max_length=100):
    # Replace invalid Windows filename characters with underscore
    name = re.sub(r'[<>:"/\\|?*]', '_', name)
    return name[:max_length]


def download_as_pdf(pdf_url: str, download_dir: str):
    os.makedirs(sanitize_filename(download_dir), exist_ok=True)
    filename = os.path.basename(pdf_url.split("?")[0])
    save_path = os.path.join(download_dir, sanitize_filename(filename))
    response = requests.get(pdf_url)
    with open(save_path, "wb") as f:
        f.write(response.content)
    print(f"Downloaded to: {save_path}")


def gdp_scraper():
    with sync_playwright() as p:
        browser = p.chromium.la