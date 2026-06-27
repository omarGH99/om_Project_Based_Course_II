"""Diagnostic v2: try full browser-like headers to get past the 415 block."""
import requests, re
from bs4 import BeautifulSoup
from urllib.parse import urljoin

BASE = "https://govarametin.com"
HEADERS = {
    "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                   "AppleWebKit/537.36 (KHTML, like Gecko) "
                   "Chrome/126.0.0.0 Safari/537.36"),
    "Accept": ("text/html,application/xhtml+xml,application/xml;q=0.9,"
               "image/avif,image/webp,*/*;q=0.8"),
    "Accept-Language": "en-US,en;q=0.9,ku;q=0.8,ar;q=0.7",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
}

for url in [BASE + "/", f"{BASE}/category/gutar/", f"{BASE}/gutar/5037/"]:
    print("=" * 70)
    print("FETCHING:", url)
    try:
        r = requests.get(url, headers=HEADERS, timeout=20)
        r.encoding = "utf-8"
        print("status:", r.status_code, "| length:", len(r.text))
    except Exception as e:
        print("ERROR:", e); continue
    if r.status_code != 200:
        print("  (non-200 — still blocked)"); continue
    soup = BeautifulSoup(r.text, "html.parser")
    hrefs = [urljoin(BASE, a["href"]) for a in soup.find_all("a", href=True)
             if "govarametin.com" in urljoin(BASE, a["href"])]
    print("internal links:", len(hrefs))
    seen = set()
    for h in hrefs:
        path = h.split("govarametin.com")[-1]
        shape = re.sub(r"\d+", "N", path)
        if shape not in seen:
            seen.add(shape)
            print("  ", path[:80])
        if len(seen) >= 25:
            break