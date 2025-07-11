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


def fbil_scraper():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, slow_mo=300)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        page.goto('https://www.fbil.org.in/#/home')
