import os
import requests
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
from urllib.parse import urljoin

def sanitize_filename(name, max_length=100):
    import re
    name = re.sub(r'[<>:"/\\|?*]', '_', name)
    return name[:max_length]

def download_file(file_url: str, download_dir: str, filename: str, downloaded_files: set):
    os.makedirs(download_dir, exist_ok=True)
    filename = sanitize_filename(filename)
    save_path = os.path.join(download_dir, filename)
    
    if filename in downloaded_files:
        print(f"🔄 Already processed: {filename}")
        return False
    
    if os.path.exists(save_path):
        print(f"⏭️ File exists: {filename}")
        downloaded_files.add(filename)
        return False
    
    try:
        response = requests.get(file_url, headers={"User-Agent": "Mozilla/5.0", "Referer": "https://mospi.gov.in/"}, timeout=30)
        if response.status_code == 200:
            with open(save_path, "wb") as f:
                f.write(response.content)
            downloaded_files.add(filename)
            print(f"✅ Downloaded: {filename} ({len(response.content)//1024} KB)")
            return True
        else:
            print(f"❌ Failed: {filename} (Status: {response.status_code})")
            return False
    except Exception as e:
        print(f"❌ Error: {filename} - {e}")
        return False

def iip_data_scraper():
    downloaded_files = set()
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )
        page = context.new_page()
        
        print("Navigating to IIP page...")
        page.goto('https://mospi.gov.in/iip', timeout=60000)
        
        print("Clicking on Data tab...")
        page.click("button:has-text('Data')")
        page.wait_for_load_state('domcontentloaded')
        page.wait_for_timeout(3000)
        
        print("Expanding all sections in Data tab...")
        for _ in range(20):
            collapsed = page.locator("li.collapsed > span").count()
            if collapsed == 0:
                break
            try:
                page.locator("li.collapsed > span").first.click()
                page.wait_for_timeout(200)
            except:
                break
        
        print("Parsing page with BeautifulSoup...")
        html = page.content()
        soup = BeautifulSoup(html, 'html.parser')
        
        # TARGET ONLY THE DATA SECTION - this is crucial!
        data_section = soup.find('div', {'id': 'Data'}) or soup.find('div', class_='tabcontent_event')
        
        if not data_section:
            print("❌ Data section not found! Looking for alternative selectors...")
            # Fallback: look for Data content by checking visible content
            data_section = soup.find('div', string=lambda text: text and 'IIP Data' in text)
            if data_section:
                data_section = data_section.find_parent('div')
        
        if not data_section:
            print("❌ Could not locate Data section specifically!")
            browser.close()
            return
        
        print("✅ Found Data section, extracting files...")
        
        # Find links ONLY within the Data section
        main_color_links = data_section.find_all('a', class_='main-color', href=True)
        data_files = []
        unique_urls = set()
        
        base_url = "https://mospi.gov.in"
        target_extensions = ['.xlsx', '.xls', '.jpg']
        
        for link in main_color_links:
            href = link.get('href', '')
            
            if any(href.lower().endswith(ext) for ext in target_extensions):
                full_url = urljoin(base_url, href)
                filename = os.path.basename(href)
                
                if full_url in unique_urls:
                    print(f"🔄 Duplicate URL skipped: {filename}")
                    continue
                
                # Additional filtering for IIP data files
                if ('/sites/default/files/iip/' in href or 
                    'indices_IIP' in href or 
                    'table' in href.lower() or
                    href.startswith('/sites/default/files/iip/')):
                    
                    unique_urls.add(full_url)
                    data_files.append({
                        'url': full_url,
                        'filename': filename,
                        'extension': os.path.splitext(filename)[1].lower(),
                        'href': href,
                        'section': 'Data'  # Mark as Data section
                    })
                    print(f"Found Data section file: {filename}")
        
        print(f"\n>>> Files found ONLY in Data section: {len(data_files)}")
        
        # Group by file type for summary
        by_type = {}
        for file_info in data_files:
            ext = file_info['extension']
            by_type[ext] = by_type.get(ext, 0) + 1
        
        for ext, count in by_type.items():
            print(f"  {ext}: {count} files")
        
        # Download all data files
        successful_downloads = 0
        skipped_files = 0
        
        for i, file_info in enumerate(data_files):
            print(f"\nProcessing {i+1}/{len(data_files)}: {file_info['filename']} [Data section]")
            
            if download_file(file_info['url'], 'IIP_Data_Files', file_info['filename'], downloaded_files):
                successful_downloads += 1
            else:
                skipped_files += 1
        
        print(f"\n=== Download Summary (Data section only) ===")
        print(f"Total files found in Data section: {len(data_files)}")
        print(f"Successfully downloaded: {successful_downloads}")
        print(f"Skipped (existing/duplicates): {skipped_files}")
        print(f"Files processed in this session: {len(downloaded_files)}")
        print('✅ IIP Data section scraping finished successfully')
        
        browser.close()

if __name__ == "__main__":
    iip_data_scraper()
