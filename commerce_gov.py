import os
import time
import requests
import urllib.parse
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

# ---------- CONFIG ----------
SITE_NAME = "commerce.gov.in"
BASE_URL = f"https://{SITE_NAME}"
TARGET_URL = f"{BASE_URL}/trade-statistics/latest-trade-figures/"
DOWNLOAD_DIR = SITE_NAME
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# ---------- SETUP VISIBLE CHROME ----------
chrome_options = Options()
# comment out headless to see what's happening
# chrome_options.add_argument("--headless")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--no-sandbox")

driver = webdriver.Chrome(options=chrome_options)
driver.get(TARGET_URL)

# ---------- WAIT FOR FULL RENDER ----------
print("⏳ Waiting for page to load...")
time.sleep(10)  # wait longer for JS to inject PDFs

# ---------- GET AND SAVE PAGE SOURCE ----------
html = driver.page_source
with open("debug_page.html", "w", encoding="utf-8") as f:
    f.write(html)
print("✅ HTML written to debug_page.html")

# ---------- PARSE WITH BEAUTIFULSOUP ----------
soup = BeautifulSoup(html, "html.parser")

pdf_links = []
for a in soup.find_all("a", href=True):
    href = a["href"]
    if ".pdf" in href.lower():
        full_url = urllib.parse.urljoin(BASE_URL, href)
        pdf_links.append(full_url)

# ---------- DOWNLOAD FIRST 2 PDFs ----------
if not pdf_links:
    print("❌ No PDF links found. Check debug_page.html to verify content.")
else:
    print(f"✅ Found {len(pdf_links)} PDF(s). Downloading first 2...")
    for i, link in enumerate(pdf_links[:2]):
        try:
            response = requests.get(link)
            if response.status_code == 200:
                filename = os.path.join(DOWNLOAD_DIR, f"document_{i+1}.pdf")
                with open(filename, "wb") as f:
                    f.write(response.content)
                print(f"✅ Saved: {filename}")
            else:
                print(f"❌ Failed to download {link} (status {response.status_code})")
        except Exception as e:
            print(f"❌ Error downloading {link}: {e}")

driver.quit()
