import asyncio
from playwright.async_api import async_playwright
import os

DOWNLOAD_DIR = os.path.join(os.getcwd(), "downloads")

async def run():
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(accept_downloads=True)
        page = await context.new_page()

        await page.goto("https://www.bseindia.com/markets/PublicIssues/Bond_Issuances.aspx")

        # Select "All Financial Year"
        await page.select_option("#ctl00_ContentPlaceHolder1_drpFinanceYear", "All Financial Year")

        # Click the Search button
        await page.click("#ctl00_ContentPlaceHolder1_btnSubmit")

        # Wait for results to load (you can adjust timeout based on speed)
        await page.wait_for_timeout(3000)

        # Click the download button and handle download
        async with page.expect_download() as download_info:
            await page.click("#ctl00_ContentPlaceHolder1_lnkdownload")
        download = await download_info.value
        save_path = os.path.join(DOWNLOAD_DIR, download.suggested_filename)
        await download.save_as(save_path)
        print(f"Downloaded to {save_path}")

        await browser.close()

asyncio.run(run())
