"""
UIL Alignment Pipeline
------------------------
One script, three steps:
  1. SCRAPE  - pull the first 6 links out of the first <ul> in the UIL
               academics alignment page (the current 1A-6A PDFs).
  2. DOWNLOAD - save each PDF locally.
  3. PARSE    - turn each PDF into structured JSON
               (Conference -> Regions -> Districts -> Schools).

Usage:
    python alignment.py
    python alignment.py --pdf-dir data/pdfs --json-dir data/json
    python alignment.py --no-parse      # scrape + download only
    python alignment.py --open          # also pop each PDF link open in browser

Key fixes vs. the original:
  SCRAPE
  ------
  • find_content_div tries several common wrapper IDs/classes before
    falling back to the full page.
  • get_first_six_links now iterates every <ul> in the content div and picks
    the first one that actually contains .pdf hrefs, skipping nav/menu lists.
    It also filters non-PDF <a> tags within that list.

  PARSE
  -----
  • Root cause of broken district parsing: the PDF renders "District" and its
    number as two words on *slightly different* y-positions (≈0.73 px apart).
    With the old y_tolerance=3 and no column awareness, they merged with words
    from neighbouring columns producing garbage lines like
    "District 1 District 5 District 9 …".
  • Fix: words are first bucketed into one of 8 physical columns (boundaries
    at x midpoints between the known District-word anchors), then lines are
    grouped *within* each column with y_tolerance=2. This guarantees words
    from different columns never share a line and the 0.73 px offset is
    bridged cleanly.
  • Column-to-region mapping: cols 0+1 → Region 1, cols 2+3 → Region 2, etc.
    Within each region, districts are read left-column-first, top-to-bottom,
    then right-column, top-to-bottom.
"""

import argparse
import json
import re
import sys
import time
import webbrowser
from collections import defaultdict
from pathlib import Path
from urllib.parse import urljoin

import pdfplumber
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

DISTRICT_RE  = re.compile(r"^District\s+(\d+)$", re.IGNORECASE)
CONFERENCE_RE = re.compile(r"CONFERENCE\s+(\S+)", re.IGNORECASE)
REGION_RE    = re.compile(r"^Region\s+(\d+)$",   re.IGNORECASE)
CONF_RANK_RE = re.compile(r"(\d)[Aa]")   # matches "1A", "2a", etc. in text or href

# ─────────────────────────────────────────────────────────────
# STEP 1 — SCRAPE
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
    return links


def scrape_links():
    print(f"[1/3] Scraping {URL} ...")
    html = fetch_page(URL)
    soup = BeautifulSoup(html, "html.parser")
    content_div = find_content_div(soup)
    links = get_first_six_links(content_div, URL)
    for i, link in enumerate(links, start=1):
        print(f"   {i}. {link['text'] or '(no text)'} -> {link['href']}")
    return links


# ─────────────────────────────────────────────────────────────
# STEP 2 — DOWNLOAD
# ─────────────────────────────────────────────────────────────

def download_pdf(url: str, out_dir: Path) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    filename = url.split("/")[-1].split("?")[0] or "alignment.pdf"
    if not filename.lower().endswith(".pdf"):
        filename += ".pdf"
    dest = out_dir / filename
    resp = requests.get(url, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    dest.write_bytes(resp.content)
    return dest


def download_all(links, pdf_dir: Path):
    print(f"\n[2/3] Downloading {len(links)} PDF(s) to ./{pdf_dir}/ ...")
    downloaded = []
    for link in links:
        try:
            dest = download_pdf(link["href"], pdf_dir)
            print(f"   Saved: {dest}")
            downloaded.append({**link, "path": dest})
        except requests.RequestException as e:
            print(f"   Failed to download {link['href']}: {e}", file=sys.stderr)
    return downloaded


# ─────────────────────────────────────────────────────────────
# STEP 3 — PARSE
# ─────────────────────────────────────────────────────────────

def is_bold(word: dict) -> bool:
    return "bold" in word.get("fontname", "").lower()


def line_text(line: list) -> str:
    return " ".join(w["text"] for w in line).strip()


def extract_words(pdf_path) -> list:
    all_words = []
    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages):
            words = page.extract_words(
                extra_attrs=["fontname", "size"],
                use_text_flow=False,
                keep_blank_chars=False,
            )
            for w in words:
                w["page"] = page_num
            all_words.extend(words)
    return all_words


def detect_column_boundaries(words: list) -> list[float]:
    """
    Detect 8-column layout boundaries as midpoints between adjacent
    'District'-word x0 anchors.  Falls back gracefully if fewer columns
    are present (e.g. 1A has 8 cols, but some conferences may differ).
    """
    district_words = [w for w in words if w["text"].lower() == "district" and is_bold(w)]
    anchors = sorted(set(round(w["x0"]) for w in district_words))

    if len(anchors) < 2:
        # Cannot detect — return a single boundary that splits nothing
        return []

    # Midpoints between consecutive anchors
    boundaries = [(anchors[i] + anchors[i + 1]) / 2 for i in range(len(anchors) - 1)]
    return boundaries


def assign_column(x0: float, boundaries: list[float]) -> int:
    """Return the column index for an x0 coordinate given the boundary list."""
    for i, b in enumerate(boundaries):
        if x0 < b:
            return i
    return len(boundaries)   # last column


def group_lines_in_column(col_words: list, y_tolerance: float = 2.0) -> list[list]:
    """
    Group words from a *single* column into lines by vertical proximity.
    y_tolerance=2 is tight enough to split actual rows yet wide enough to
    bridge the ~0.73 px offset between 'District' and its number glyph.
    """
    if not col_words:
        return []
    sorted_words = sorted(col_words, key=lambda w: (w["page"], w["top"]))

    lines: list[list] = []
    current_line: list = [sorted_words[0]]
    current_top: float = sorted_words[0]["top"]
    current_page: int  = sorted_words[0]["page"]

    for w in sorted_words[1:]:
        if w["page"] != current_page or abs(w["top"] - current_top) > y_tolerance:
            lines.append(sorted(current_line, key=lambda x: x["x0"]))
            current_line = [w]
            current_top  = w["top"]
            current_page = w["page"]
        else:
            current_line.append(w)

    if current_line:
        lines.append(sorted(current_line, key=lambda x: x["x0"]))

    return lines


HEADER_TOKENS = frozenset({"ACADEMICS", "CONFERENCE", "OFFICIAL", "ALIGNMENT"})


def is_header_line(line: list) -> bool:
    """True for the title / conference / region-header rows."""
    tokens = {w["text"].upper() for w in line}
    return bool(tokens & HEADER_TOKENS)


def parse_alignment_pdf(pdf_path) -> dict:
    words = extract_words(pdf_path)
    if not words:
        raise RuntimeError(f"No text extracted from {pdf_path} — scanned/image PDF?")

    # ── Conference label ──────────────────────────────────────────────────────
    full_text = " ".join(w["text"] for w in words)
    cm = CONFERENCE_RE.search(full_text)
    conference = cm.group(1) if cm else "Unknown"

    # ── Detect column layout ──────────────────────────────────────────────────
    boundaries = detect_column_boundaries(words)
    n_cols = len(boundaries) + 1   # number of columns

    # ── Bucket words into columns ─────────────────────────────────────────────
    col_word_buckets: list[list] = [[] for _ in range(n_cols)]
    for w in words:
        col_idx = assign_column(w["x0"], boundaries)
        col_word_buckets[col_idx].append(w)

    # ── Group lines within each column ────────────────────────────────────────
    col_lines: list[list[list]] = []
    for bucket in col_word_buckets:
        lines = group_lines_in_column(bucket, y_tolerance=2.0)
        # Drop page-header rows
        lines = [ln for ln in lines if not is_header_line(ln)]
        # Drop Region header lines — we infer regions from column pairs instead
        lines = [ln for ln in lines if not REGION_RE.match(line_text(ln))]
        col_lines.append(lines)

    # ── Determine how many regions we have (each uses 2 columns) ─────────────
    # Parse region count from the full text; fall back to n_cols // 2
    region_nums_found = sorted(
        int(m.group(1))
        for w in words
        for m in [REGION_RE.match(w["text"])]
        if m
    )
    # Region headers span two words ("Region" + "1"), pick them from region lines
    all_lines_flat = []
    for bucket in col_word_buckets:
        all_lines_flat.extend(group_lines_in_column(bucket, y_tolerance=2.0))
    region_lines = [ln for ln in all_lines_flat if REGION_RE.match(line_text(ln))]
    region_numbers = sorted(
        int(REGION_RE.match(line_text(ln)).group(1)) for ln in region_lines
    ) if region_lines else list(range(1, n_cols // 2 + 1))

    # ── Build structured output ───────────────────────────────────────────────
    regions_out = []
    for region_i, region_num in enumerate(region_numbers):
        left_col_lines  = col_lines[region_i * 2]     if region_i * 2     < n_cols else []
        right_col_lines = col_lines[region_i * 2 + 1] if region_i * 2 + 1 < n_cols else []

        districts: list[dict] = []
        current_district: dict | None = None

        for ln in left_col_lines + right_col_lines:
            txt = line_text(ln)
            m = DISTRICT_RE.match(txt)
            if m and is_bold(ln[0]):
                current_district = {"district": int(m.group(1)), "schools": []}
                districts.append(current_district)
            elif current_district is not None and txt:
                current_district["schools"].append(txt)

        regions_out.append({"region": region_num, "districts": districts})

    return {"conference": conference, "regions": regions_out}


def parse_all(downloaded: list, json_dir: Path) -> list:
    print(f"\n[3/3] Parsing {len(downloaded)} PDF(s) into ./{json_dir}/ ...")
    json_dir.mkdir(parents=True, exist_ok=True)
    results = []
    written_files = []
    for item in downloaded:
        pdf_path = item["path"]
        try:
            parsed = parse_alignment_pdf(pdf_path)
            out_path = json_dir / (pdf_path.stem + ".json")
            out_path.write_text(json.dumps(parsed, indent=2))
            written_files.append(out_path.name)
            n_schools = sum(
                len(d["schools"])
                for r in parsed["regions"]
                for d in r["districts"]
            )
            print(
                f"   {pdf_path.name} -> {out_path} "
                f"(conference {parsed['conference']}, {n_schools} schools)"
            )
            results.append(parsed)
        except Exception as e:
            print(f"   Failed to parse {pdf_path.name}: {e}", file=sys.stderr)

    # Write manifest.json (used by fetch-based fallback)
    if written_files:
        manifest_path = json_dir / "manifest.json"
        manifest_path.write_text(json.dumps({"files": sorted(written_files)}, indent=2))
        print(f"   Manifest written -> {manifest_path}")

    # Write schools.js — a self-contained JS file that assigns all school data
    # to window.UIL_SCHOOLS so info.html can load it via a plain <script> tag.
    # This works offline, from file://, from GitHub Pages — no fetch() needed.
    #
    # Format written:
    #   window.UIL_SCHOOLS = [
    #     { name, conference, region, district }, ...
    #   ];
    if results:
        schools = []
        for conf_data in results:
            conf = conf_data.get("conference", "?").upper()
            for region in conf_data.get("regions", []):
                for district in region.get("districts", []):
                    for school in district.get("schools", []):
                        if school and school.strip():
                            schools.append({
                                "name":       school.strip(),
                                "conference": conf,
                                "region":     region["region"],
                                "district":   district["district"],
                            })

        schools.sort(key=lambda s: (s["conference"], s["region"], s["district"], s["name"]))

        js_path = json_dir / "schools.js"
        js_path.write_text(
            "window.UIL_SCHOOLS = " + json.dumps(schools, separators=(",", ":")) + ";\n"
        )
        print(f"   schools.js written -> {js_path}  ({len(schools)} schools)")

    return results


# ─────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Scrape, download, and parse all 6 UIL alignment PDFs."
    )
    parser.add_argument("--pdf-dir",  default="alignments/pdfs", help="Where to save downloaded PDFs.")
    parser.add_argument("--json-dir", default="alignments/json", help="Where to save parsed JSON.")
    parser.add_argument("--no-parse", action="store_true",       help="Only scrape + download; skip parsing.")
    parser.add_argument("--open",     action="store_true",       help="Also open each PDF link in your browser.")
    args = parser.parse_args()

    links = scrape_links()

    if args.open:
        print("\nOpening links in your browser...")
        for link in links:
            webbrowser.open_new_tab(link["href"])
            time.sleep(1)

    downloaded = download_all(links, Path(args.pdf_dir))

    if not downloaded:
        print("\nNo PDFs downloaded — stopping before parse step.", file=sys.stderr)
        sys.exit(1)

    if not args.no_parse:
        parse_all(downloaded, Path(args.json_dir))

    print("\nDone.")


if __name__ == "__main__":
    main()