import asyncio
from playwright.async_api import async_playwright
from PIL import Image
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
import math
import io

# List of URLs to capture
URLS = [
    "https://aleksejgaj.cz/",
    "https://youtube.com",
    #tba
]

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(device_scale_factor=1)

        for i, url in enumerate(URLS, start=1):
            page = await context.new_page()
            await page.goto(url, wait_until="networkidle")
            #await page.wait_for_timeout(2500)
            #await page.goto(url, wait_until="load")
            #await page.wait_for_load_state("load")  # waits until the 'load' event fires
            await page.evaluate("""() => {
                const imgs = document.querySelectorAll('img');
                imgs.forEach(img => img.scrollIntoView());
            }""")
            await page.wait_for_timeout(500)  # small wait for render



            # Take full-page screenshot
            img_bytes = await page.screenshot(full_page=True)
            img = Image.open(io.BytesIO(img_bytes))

            # Convert pixels to mm for A4 sizing
            a4_width, a4_height = A4  # points (1/72 inch)
            dpi = 96  # assume screen density
            px_per_point = dpi / 72

            page_width_px = int(a4_width * px_per_point)
            page_height_px = int(a4_height * px_per_point)

            # Slice the image into A4 segments
            n_slices = math.ceil(img.height / page_height_px)

            pdf_filename = f"/wp/page_{i}.pdf"
            c = canvas.Canvas(pdf_filename, pagesize=A4)

            for j in range(n_slices):
                top = j * page_height_px
                bottom = min((j + 1) * page_height_px, img.height)
                crop = img.crop((0, top, img.width, bottom))

                # Fit slice to A4 width
                from reportlab.lib.utils import ImageReader

                # Convert PIL image directly to ImageReader
                image_reader = ImageReader(crop)
                #c.drawImage(image_reader, 0, 0, width=a4_width, height=a4_height)
                
                # Scale proportionally to fit A4 width
                # Fit slice to A4 width
                img_w, img_h = img.size
                scale = a4_width / img_w  # scale to fit A4 width
                slice_height_px = int(a4_height / scale)  # height in image pixels for 1 PDF page

                n_slices = math.ceil(img_h / slice_height_px)

                pdf_filename = f"page_{i}.pdf"
                c = canvas.Canvas(pdf_filename, pagesize=A4)

                for j in range(n_slices):
                    top = j * slice_height_px
                    bottom = min((j + 1) * slice_height_px, img_h)
                    crop = img.crop((0, top, img_w, bottom))
                    
                    image_reader = ImageReader(crop)
                    # draw image to fill A4 width and corresponding height
                    crop_h = bottom - top
                    draw_height = crop_h * scale
                    c.drawImage(image_reader, 0, a4_height - draw_height, 
                                width=a4_width, height=draw_height)
                    c.showPage()



            c.save()
            print(f"Saved {pdf_filename} from {url}")

        await browser.close()

asyncio.run(main())



from PyPDF2 import PdfMerger
import glob

# Create a PdfMerger object
merger = PdfMerger()

# Find all PDF files (adjust the pattern if needed)
pdf_files = sorted(glob.glob("page_*.pdf"))

# Append each PDF to the merger
for pdf_file in pdf_files:
    merger.append(pdf_file)

# Write out the merged PDF
merged_filename = "pagesmerged.pdf"
merger.write(merged_filename)
merger.close()

print(f"Merged {len(pdf_files)} PDFs into {merged_filename}")
