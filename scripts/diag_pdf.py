# Diagnose why a PDF extracts 0 text: is it scanned (image) or just different?
import sys
from pypdf import PdfReader
path = sys.argv[1]
r = PdfReader(path)
print("pages:", len(r.pages))
for i in range(min(5, len(r.pages))):
    pg = r.pages[i]
    txt = (pg.extract_text() or "")
    imgs = 0
    try:
        imgs = len(pg.images)
    except Exception:
        pass
    print(f"page {i}: text_chars={len(txt)}  images={imgs}")
    if txt.strip():
        print("   sample:", repr(txt[:120]))
