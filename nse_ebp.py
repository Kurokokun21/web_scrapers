import asyncio
from playwright.async_api import async_playwright
import os

URL = "https://www.nse-ebp.com/ebp/rest/placement?pub=true"
DOWNLOAD_DIR = os.path.join(os.getcwd(), "nse-ebp")

async def run():
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(accept_downloads=True)
        page = await context.new_page()

        await page.goto(URL)

        # Wait for 5 seconds
        await page.wait_for_timeout(5000)

        # Click on download (the a tag with javascript:downloadPlacements(this))
        async with page.expect_download() as download_info:
            await page.click("a[href^='javascript:downloadPlacements']")

        download = await download_info.value
        save_path = os.path.join(DOWNLOAD_DIR, download.suggested_filename)
        await download.save_as(save_path)
        print(f"Downloaded to {save_path}")

        await browser.close()

asyncio.run(run())
