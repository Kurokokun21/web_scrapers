# 📊 Indian Government Data Scraper Suite

This repository contains multiple scripts to scrape data from various Indian government data portals like **MOSPI**, **MCA**, **Commerce Ministry**, **IMF**, etc. These scrapers collect important datasets such as **CPI**, **WPI**, **GDP**, **IIP**, and more. The scripts primarily use **Python + Playwright**, and some use `requests`, `pandas`, and `BeautifulSoup`.

---

## 📁 Files and Their Purpose

### `cpi_all_india.py`
Scrapes All-India CPI (Consumer Price Index) data from MOSPI’s CPI portal for the latest available values.

### `cpi_all_india_item.py`
Selects all available CPI items and scrapes their index values for the selected month/year. Saves the downloaded `.xls` file.

### `cpi_timeseries_statewise.py`
Generates time-series CPI data for every Indian state by iterating through state-wise dropdown options. Extracted files are organized by state.

### `DCA_scraper.py`
Goes to the Ministry of Corporate Affairs (MCA) website and downloads the circulars section page. Waits for 10 seconds on each circular link page and saves the full HTML source in a text file for each.

### `GDP_scraper.py`
Navigates to the GDP page on MOSPI, scrapes and downloads multiple GDP-related Excel files, reports, and press releases.

### `IIP_data_scrapper.py`
Scrapes Index of Industrial Production data from the MOSPI portal, automating selections for year/month and downloading Excel files.

### `IIP_press_release_scrapper.py`
Iterates through the IIP Press Release archive and downloads all available PDF files. Supports pagination and handles file naming to avoid overwrite.

### `IMF_WEO_scraper.py`
Scrapes the World Economic Outlook (WEO) report data from the International Monetary Fund (IMF) site. Downloads available Excel datasets.

### `PLFS_scrapper.py`
Scrapes Periodic Labour Force Survey (PLFS) data including Excel or PDF downloads available from the MOSPI PLFS page.

### `WPI_scraper.py`
Scrapes Wholesale Price Index data by navigating to eaindustry.nic.in. It iterates over commodities and downloads their data files.

### `commerce_gov.py`
Navigates to the commerce.gov.in Trade Statistics section, downloads available reports and policy documents in PDF or Excel formats.

---

## ▶️ How to Run

1. Install dependencies:
```bash
pip install -r requirements.txt
```

Or manually:
```bash
pip install playwright requests pandas beautifulsoup4
playwright install
```

2. Run any script:
```bash
python script_name.py
```

Example:
```bash
python cpi_all_india_item.py
```

---

## 📦 Output

All output files (PDFs, Excel files, scraped HTMLs) are saved in a folder named `downloads/`, organized by script or scheme.  

Each subfolder may contain:
- `.xls` or `.xlsx` (Excel files)
- `.pdf` (Press releases or documents)
- `.html` or `.txt` (circular pages, raw HTML)

---

## 🧠 Features

- Built using Playwright for robust browser automation.
- Fully headful scraping (`headless=False`) for transparent execution.
- Includes sleep delays where necessary to simulate human interaction.
- Uses dropdown and button interactions for dynamic content.
- Scrapes across multiple months/years and paginated archives.

---

## 📍 Notes

- The browser opens visibly and waits on each page for 10 seconds (or more in some scripts).
- File naming is consistent to avoid overwriting.
- Some files are downloaded manually using click simulation in Playwright.
- Data is sourced from public government websites and intended for academic/research use only.

---

## 💻 Sample Script Logic – CPI Scraper

Steps from `cpi_all_india_item.py`:
1. Go to [https://cpi.mospi.gov.in](https://cpi.mospi.gov.in)
2. Hover over *All India Item Index*
3. Click on the link for Combined Index (2012 base)
4. Select all items from the listbox
5. Choose the latest year and month from dropdowns
6. Click *View Indices* → Export to Excel
7. Save the file

---

## 🛠 Requirements

- Python 3.8+
- Playwright
- pandas
- requests
- beautifulsoup4

Run the following to install:
```bash
pip install -r requirements.txt
playwright install
```

---

## 🧑‍💻 Maintainer

**Rahul Sharma**  
BITS Pilani, Computer Science  
GitHub: [@Kurokokun21](https://github.com/Kurokokun21)

---

## 🔗 Useful Links

- [MOSPI CPI Portal](https://cpi.mospi.gov.in)
- [MOSPI GDP Page](https://mospi.gov.in)
- [IMF WEO](https://www.imf.org/en/Publications/WEO)
- [MCA Circulars](https://www.mca.gov.in/content/mca/global/en/notifications-tender/circulars.html)
- [Commerce Ministry](https://commerce.gov.in)
- [WPI Portal](https://eaindustry.nic.in)

---

## 📜 License

This codebase is for educational and research purposes only. Respect site terms of use and avoid overwhelming government servers.
