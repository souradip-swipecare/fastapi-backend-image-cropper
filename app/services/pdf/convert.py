import fitz  # PyMuPDF
import io
from PIL import Image


def pdf_to_image_bytes(pdf_bytes: bytes) -> bytes:
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    page = doc.load_page(0)

    pix = page.get_pixmap(dpi=200)
    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=95)

    return buf.getvalue()
