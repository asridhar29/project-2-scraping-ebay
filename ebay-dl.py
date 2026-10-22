#!/usr/bin/env python3
"""Scrape eBay search results into JSON or CSV."""

import argparse
import csv
import json
import re
import sys
import time
from pathlib import Path

import requests
from bs4 import BeautifulSoup

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)
BASE_URL = "https://www.ebay.com/sch/i.html"
NUM_PAGES = 10
REQUEST_DELAY = 1.0
REQUEST_TIMEOUT = 10


def fetch_page_html(search_term, page_num, pages_dir=None, session=None):
    """Return the raw HTML for one page of search results.

    When pages_dir is given, the page is read from disk (page-N.html)
    instead of being requested over the network.
    """
    if pages_dir:
        path = Path(pages_dir) / f"page-{page_num}.html"
        return path.read_text(encoding="utf-8")

    headers = {"User-Agent": USER_AGENT}
    params = {"_nkw": search_term, "_pgn": page_num}
    response = session.get(BASE_URL, params=params, headers=headers, timeout=REQUEST_TIMEOUT)
    response.raise_for_status()
    return response.text


def parse_price(text):
    """Extract a price in integer cents from text like '$54.99' or '$54.99 to $65.99'."""
    if not text:
        return None
    matches = re.findall(r"[\d,]+\.\d{2}", text)
    if not matches:
        return None
    value = matches[0].replace(",", "")
    return round(float(value) * 100)


def parse_shipping(text):
    """Extract shipping cost in integer cents. 0 for free shipping, None if unknown."""
    if not text:
        return None
    if "free" in text.lower():
        return 0
    match = re.search(r"[\d,]+\.\d{2}", text)
    if not match:
        return None
    value = match.group(0).replace(",", "")
    return round(float(value) * 100)


def parse_items_sold(text):
    """Extract an integer item-sold count from text like '123 sold'."""
    if not text:
        return None
    match = re.search(r"[\d,]+", text)
    if not match:
        return None
    return int(match.group(0).replace(",", ""))


def parse_listing(item):
    """Parse one listing (<li class="s-item">) into a dict, or None if it isn't a real listing."""
    title_tag = item.select_one(".s-item__title")
    if title_tag is None:
        return None
    name = title_tag.get_text(strip=True)
    if not name or name.lower() in ("shop on ebay", "new listing"):
        return None

    price_tag = item.select_one(".s-item__price")
    price = parse_price(price_tag.get_text(strip=True) if price_tag else None)

    status_tag = item.select_one(".SECONDARY_INFO") or item.select_one(".s-item__subtitle")
    status = status_tag.get_text(strip=True) if status_tag else None
    status = status or None

    shipping_tag = item.select_one(".s-item__shipping") or item.select_one(".s-item__logisticsCost")
    shipping = parse_shipping(shipping_tag.get_text(strip=True) if shipping_tag else None)

    free_returns = item.select_one(".s-item__free-returns") is not None

    sold_tag = item.select_one(".s-item__quantitySold")
    items_sold = parse_items_sold(sold_tag.get_text(strip=True) if sold_tag else None)

    return {
        "name": name,
        "price": price,
        "status": status,
        "shipping": shipping,
        "free_returns": free_returns,
        "items_sold": items_sold,
    }


def parse_page(html):
    """Parse a search-results page into a list of listing dicts."""
    soup = BeautifulSoup(html, "html.parser")
    listings = []
    for item in soup.select("li.s-item"):
        listing = parse_listing(item)
        if listing is not None:
            listings.append(listing)
    return listings


def scrape(search_term, pages_dir=None):
    """Scrape (or read) pages 1-10 and return the combined list of listings."""
    results = []
    session = None if pages_dir else requests.Session()

    for page_num in range(1, NUM_PAGES + 1):
        html = fetch_page_html(search_term, page_num, pages_dir=pages_dir, session=session)
        results.extend(parse_page(html))
        if not pages_dir and page_num < NUM_PAGES:
            time.sleep(REQUEST_DELAY)

    return results


def save_json(listings, search_term):
    out_path = Path(f"{search_term}.json")
    out_path.write_text(json.dumps(listings, indent=2), encoding="utf-8")
    return out_path


def save_csv(listings, search_term):
    out_path = Path(f"{search_term}.csv")
    fieldnames = ["name", "price", "status", "shipping", "free_returns", "items_sold"]
    with out_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(listings)
    return out_path


def main():
    parser = argparse.ArgumentParser(description="Scrape eBay search results into JSON or CSV.")
    parser.add_argument("--search", required=True, help="Search term, e.g. 'garden tools'")
    parser.add_argument("--pages-dir", help="Read page-1.html..page-10.html from this directory instead of the network")
    parser.add_argument("--csv", action="store_true", help="Save results as CSV instead of JSON")
    args = parser.parse_args()

    listings = scrape(args.search, pages_dir=args.pages_dir)

    if args.csv:
        out_path = save_csv(listings, args.search)
    else:
        out_path = save_json(listings, args.search)

    print(f"Saved {len(listings)} listings to {out_path}")


if __name__ == "__main__":
    main()
