"""截取前端界面截图。"""
import asyncio
from playwright.async_api import async_playwright
from pathlib import Path

OUT_DIR = Path(__file__).parent / "docs"


async def main():
    OUT_DIR.mkdir(exist_ok=True)

    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(viewport={"width": 1280, "height": 900})

        await page.goto("http://localhost:5173", wait_until="networkidle")
        await page.fill("textarea", "晋商的票号制度是如何运作的？")
        await page.click("button.btn-primary")
        await page.wait_for_selector(".answer-box", timeout=15000)
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await page.screenshot(path=OUT_DIR / "screenshot-03-sources.png", full_page=True)
        print("Saved: docs/screenshot-03-sources.png")

        await browser.close()


asyncio.run(main())
