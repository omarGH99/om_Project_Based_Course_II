"""
Scrape Badini (Arabic-script Kurmanji) article text from Govara Metin
(govarametin.com), a Duhok cultural/literary magazine, and append the cleaned
sentences to the project corpus.

Respectful crawling:
  - reads and obeys robots.txt
  - identifies itself with a clear User-Agent
  - sleeps between requests (default 2s) so it doesn't hammer the server
  - only fetches public article pages
Use the text for a non-commercial academic project; cite the source.

Pipeline: fetch article -> extract main text -> sentence-split ->
script-filter (Arabic) -> normalize -> Badini-letter check -> dedupe -> append.

Usage:
    pip install requests beautifulsoup4
    python scripts/scrape_govarametin.py --max-articles 300 \
        --out data/clean/badini_govarametin.txt
Then merge into the main corpus:
    python scripts/merge_corpus.py
"""

import argparse
import os
import re
import sys
import time
import urllib.robotparser as robotparser
from urllib.parse import urljoin, urlparse

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from badini_gec.normalize import normalize

import requests
from bs4 import BeautifulSoup

BASE = "https://govarametin.com"
UA = "BadiniGEC-AcademicCrawler/1.0 (MSc AI project; contact: student)"

# article URL patterns observed on the site
ARTICLE_PAT = re.compile(r"/(gutar|vekolin|hevpeyvin|sergotar|dosten-kurdan|"
                         r"kurt-u-kirmanc-kurtiya-pertukan)/\d+/?$")
# category pages to harvest article links from
CATEGORIES = ["gutar", "vekolin", "hevpeyvin", "sergotar",
              "dosten-kurdan", "kurt-u-kirmanc-kurtiya-pertukan"]

ARABIC = re.compile(r"[\u0600-\u06FF]")
LATIN = re.compile(r"[A-Za-z]")
SENT = re.compile(r"[.!?\u061F\u06D4\n]+")
STRONG_KURDISH = set("ێۆڕڤگچپ")  # Kurdish-only letters → not Arabic, not Sorani-only
ARABIC_MARKERS = ["الدین", "دار ", "بیروت", "صفحة", "الجز"]


def can_fetch(rp, url):
    try:
        return rp.can_fetch(UA, url)
    except Exception:
        return True


def get(url):
    r = requests.get(url, headers={"User-Agent": UA}, timeout=20)
    r.raise_for_status()
    r.encoding = "utf-8"
    return r.text


def collect_article_links(rp, max_pages_per_cat=5, delay=2.0):
    links = set()
    for cat in CATEGORIES:
        for page in range(1, max_pages_per_cat + 1):
            url = f"{BASE}/category/{cat}/" + (f"page/{page}/" if page > 1 else "")
            if not can_fetch(rp, url):
                continue
            try:
                html = get(url)
            except Exception as e:
                print(f"  skip {url}: {e}")
                break
            soup = BeautifulSoup(html, "html.parser")
            found = 0
            for a in soup.find_all("a", href=True):
                href = urljoin(BASE, a["href"])
                if urlparse(href).netloc.endswith("govarametin.com") and ARTICLE_PAT.search(href):
                    if href not in links:
                        links.add(href); found += 1
            print(f"  {cat} p{page}: +{found} links (total {len(links)})")
            time.sleep(delay)
            if found == 0:
                break
    return list(links)


def extract_text(html):
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
        tag.decompose()
    # WordPress article body is usually in .entry-content / article / .post-content
    node = (soup.select_one(".entry-content") or soup.select_one("article")
            or soup.select_one(".post-content") or soup.body)
    return node.get_text("\n") if node else ""


def is_badini(sent):
    if not any(ch in STRONG_KURDISH for ch in sent):
        return False
    if any(m in sent for m in ARABIC_MARKERS):
        return False
    return True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="data/clean/badini_govarametin.txt")
    ap.add_argument("--max-articles", type=int, default=300)
    ap.add_argument("--delay", type=float, default=2.0, help="seconds between requests")
    ap.add_argument("--min-words", type=int, default=4)
    ap.add_argument("--max-words", type=int, default=60)
    args = ap.parse_args()

    # robots.txt
    rp = robotparser.RobotFileParser()
    rp.set_url(f"{BASE}/robots.txt")
    try:
        rp.read()
        print("robots.txt read.")
    except Exception:
        print("robots.txt unreadable; proceeding politely.")

    print("Collecting article links...")
    links = collect_article_links(rp, delay=args.delay)
    print(f"Found {len(links)} article links.")
    links = links[: args.max_articles]

    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    seen = set()
    kept = words = 0
    with open(args.out, "w", encoding="utf-8") as out:
        for i, url in enumerate(links, 1):
            if not can_fetch(rp, url):
                continue
            try:
                html = get(url)
            except Exception as e:
                print(f"  [{i}] skip {url}: {e}")
                continue
            text = extract_text(html)
            for chunk in SENT.split(text):
                c = chunk.strip()
                if not c:
                    continue
                a, l = len(ARABIC.findall(c)), len(LATIN.findall(c))
                if a + l == 0 or a / (a + l) < 0.8:
                    continue
                if not is_badini(c):
                    continue
                n = normalize(c)
                w = len(n.split())
                if not (args.min_words <= w <= args.max_words):
                    continue
                key = n[:80]
                if key in seen:
                    continue
                seen.add(key)
                out.write(n + "\n"); kept += 1; words += w
            if i % 10 == 0:
                print(f"  [{i}/{len(links)}] kept {kept} sentences so far")
            time.sleep(args.delay)

    print(f"\nDONE. Kept {kept} Badini sentences ({words} words) -> {args.out}")


if __name__ == "__main__":
    main()
