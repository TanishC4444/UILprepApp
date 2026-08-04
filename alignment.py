"""
UIL Alignment Link Scraper
---------------------------
Scrapes the UIL academics alignment page and pulls out the current
links to the 6 conference PDFs (1A-6A). It does NOT download or parse
the PDFs — it just finds the links and writes them out so the "Get
Started" page can link straight to the live, up-to-date PDFs instead
of hardcoded URLs that go stale whenever UIL reorganizes districts.

Usage:
    python alignment.py
    python alignment.py --out-dir alignments
    python alignment.py --open        # also pop each PDF link open in browser

Output:
    <out-dir>/links.json  - [{ "conference": "1A", "text": ..., "href": ... }, ...]
    <out-dir>/links.js    - window.UIL_ALIGNMENT_LINKS = { "1A": "https://...pdf", ... };
                            Loaded directly by info.html via a <script> tag so the
                            conference buttons pick up the real links, no fetch()
                            needed (works offline, from file://, from GitHub Pages).

Key logic (unchanged from the original scraper):
  • find_content_div tries several common wrapper IDs/classes before
    falling back to the full page.
  • get_first_six_links iterates every <ul> in the content div and picks
    the first one that actually contains .pdf hrefs, skipping nav/menu
    lists that appear before the real link list, and filters non-PDF
    <a> tags within that list.
  • Links are sorted 1A -> 6A using the conference digit found in the
    link text or href.
"""

import argparse
import json
import re
import sys
import time
import webbrowser
from pathlib import Path
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

URL = "https://www.uiltexas.org/alignments/category/align-academics"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

CONF_RANK_RE = re.compile(r"(\d)[Aa]")  # matches "1A", "2a", etc. in text or href

# ─────────────────────────────────────────────────────────────
# SCRAPE
# ─────────────────────────────────────────────────────────────

def fetch_page(url: str) -> str:
    response = requests.get(url, headers=HEADERS, timeout=15)
    response.raise_for_status()
    return response.text


def find_content_div(soup: BeautifulSoup):
    """Try several common content-wrapper selectors before falling back."""
    for selector in [
        {"id": "content"},
        {"class": "content"},
        {"id": "main"},
        {"class": "main"},
        {"id": "page-content"},
        {"class": "entry-content"},
    ]:
        div = soup.find("div", selector)
        if div:
            return div
    print("Warning: no content wrapper found; scanning full page.", file=sys.stderr)
    return soup


def _ul_has_pdf_links(ul) -> bool:
    return any(".pdf" in a.get("href", "").lower() for a in ul.find_all("a", href=True))


def _conf_label(link: dict) -> str:
    """Return e.g. '1A' for a link, based on its text or href. 'UNK' if not found."""
    m = CONF_RANK_RE.search(link["text"]) or CONF_RANK_RE.search(link["href"])
    return f"{m.group(1)}A" if m else "UNK"


def get_first_six_links(content_div, base_url: str):
    """
    Find the first <ul> inside content_div that contains PDF hrefs.
    Skips navigation/menu lists that appear before the real link list.
    Within the found list, only PDF hrefs are collected.
    """
    target_ul = None
    for ul in content_div.find_all("ul"):
        if _ul_has_pdf_links(ul):
            target_ul = ul
            break

    if target_ul is None:
        raise RuntimeError(
            "No <ul> with PDF links found inside the content div. "
            "The page structure may have changed."
        )

    links = []
    for a_tag in target_ul.find_all("a", href=True):
        href_raw = a_tag["href"]
        if ".pdf" not in href_raw.lower():
            continue
        text = a_tag.get_text(strip=True)
        href = urljoin(base_url, href_raw)
        links.append({"text": text, "href": href})
        if len(links) == 6:
            break

    if len(links) < 6:
        print(f"Warning: only found {len(links)} PDF link(s), expected 6.", file=sys.stderr)

    # Sort 1A → 6A using the conference digit found in the link text or href.
    # Links whose conference cannot be determined are pushed to the end.
    def _conf_rank(link: dict) -> int:
        m = CONF_RANK_RE.search(link["text"]) or CONF_RANK_RE.search(link["href"])
        return int(m.group(1)) if m else 99

    links.sort(key=_conf_rank)

    for link in links:
        link["conference"] = _conf_label(link)

    return links


def scrape_links():
    print(f"Scraping {URL} ...")
    html = fetch_page(URL)
    soup = BeautifulSoup(html, "html.parser")
    content_div = find_content_div(soup)
    links = get_first_six_links(content_div, URL)
    for i, link in enumerate(links, start=1):
        print(f"   {i}. [{link['conference']}] {link['text'] or '(no text)'} -> {link['href']}")
    return links


# ─────────────────────────────────────────────────────────────
# OUTPUT
# ─────────────────────────────────────────────────────────────

def write_outputs(links: list, out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)

    # links.json — raw record of what was scraped
    json_path = out_dir / "links.json"
    json_path.write_text(json.dumps(links, indent=2))
    print(f"\nWrote {json_path}")

    # links.js — window.UIL_ALIGNMENT_LINKS = { "1A": "https://...pdf", ... };
    # info.html loads this directly with a <script> tag, no fetch() required,
    # so it works from file://, GitHub Pages, or anywhere else.
    conf_map = {link["conference"]: link["href"] for link in links if link["conference"] != "UNK"}
    js_path = out_dir / "links.js"
    js_path.write_text(
        "window.UIL_ALIGNMENT_LINKS = " + json.dumps(conf_map, indent=2) + ";\n"
    )
    print(f"Wrote {js_path}")


# ─────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Scrape the 6 current UIL alignment PDF links (no download/parse)."
    )
    parser.add_argument("--out-dir", default="alignments", help="Where to write links.json / links.js.")
    parser.add_argument("--open", action="store_true", help="Also open each PDF link in your browser.")
    args = parser.parse_args()

    links = scrape_links()

    if args.open:
        print("\nOpening links in your browser...")
        for link in links:
            webbrowser.open_new_tab(link["href"])
            time.sleep(1)

    write_outputs(links, Path(args.out_dir))

    print("\nDone.")


if __name__ == "__main__":
    main()