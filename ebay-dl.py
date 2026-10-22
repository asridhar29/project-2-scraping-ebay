import argparse
import csv
import json
import time

import requests
from bs4 import BeautifulSoup

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
BASE_URL = "https://www.ebay.com/sch/i.html"


def fetch_page_html(search_term, page_num, pages_dir):
    if pages_dir:
        file_name = pages_dir + "/page-" + str(page_num) + ".html"
        file = open(file_name, "r", encoding="utf-8")
        html = file.read()
        file.close()
        return html

    headers = {"User-Agent": USER_AGENT}
    params = {"_nkw": search_term, "_pgn": page_num}
    response = requests.get(BASE_URL, params=params, headers=headers, timeout=10)
    return response.text


def parse_price(text):
    if text == None or text == "":
        return None

    text = text.strip()
    if " to " in text:
        text = text.split(" to ")[0]

    text = text.replace("$", "")
    text = text.replace(",", "")
    text = text.strip()

    if text == "":
        return None

    try:
        value = float(text)
    except ValueError:
        return None

    return int(round(value * 100))


def parse_shipping(text):
    if text == None or text == "":
        return None

    text = text.strip()
    if "free" in text.lower():
        return 0

    text = text.replace("+", "")
    text = text.replace("$", "")
    text = text.replace(",", "")

    words = text.split()
    if len(words) == 0:
        return None

    try:
        value = float(words[0])
    except ValueError:
        return None

    return int(round(value * 100))


def parse_items_sold(text):
    if text == None or text == "":
        return None

    text = text.strip()
    text = text.replace(",", "")
    words = text.split()

    if len(words) == 0:
        return None

    if words[0].isdigit():
        return int(words[0])

    return None


def parse_listing(item):
    title_tag = item.select_one(".s-item__title")
    if title_tag == None:
        return None

    name = title_tag.get_text(strip=True)
    if name == "" or name.lower() == "shop on ebay":
        return None

    price_tag = item.select_one(".s-item__price")
    if price_tag == None:
        price = None
    else:
        price = parse_price(price_tag.get_text(strip=True))

    status_tag = item.select_one(".SECONDARY_INFO")
    if status_tag == None:
        status_tag = item.select_one(".s-item__subtitle")

    if status_tag == None:
        status = None
    else:
        status = status_tag.get_text(strip=True)
        if status == "":
            status = None

    shipping_tag = item.select_one(".s-item__shipping")
    if shipping_tag == None:
        shipping_tag = item.select_one(".s-item__logisticsCost")

    if shipping_tag == None:
        shipping = None
    else:
        shipping = parse_shipping(shipping_tag.get_text(strip=True))

    free_returns_tag = item.select_one(".s-item__free-returns")
    if free_returns_tag == None:
        free_returns = False
    else:
        free_returns = True

    sold_tag = item.select_one(".s-item__quantitySold")
    if sold_tag == None:
        items_sold = None
    else:
        items_sold = parse_items_sold(sold_tag.get_text(strip=True))

    listing = {
        "name": name,
        "price": price,
        "status": status,
        "shipping": shipping,
        "free_returns": free_returns,
        "items_sold": items_sold,
    }
    return listing


def parse_page(html):
    soup = BeautifulSoup(html, "html.parser")
    items = soup.select("li.s-item")

    listings = []
    for item in items:
        listing = parse_listing(item)
        if listing != None:
            listings.append(listing)

    return listings


def scrape(search_term, pages_dir):
    all_listings = []

    for page_num in range(1, 11):
        html = fetch_page_html(search_term, page_num, pages_dir)
        page_listings = parse_page(html)

        for listing in page_listings:
            all_listings.append(listing)

        if pages_dir == None and page_num < 10:
            time.sleep(1)

    return all_listings


def save_json(listings, search_term):
    file_name = search_term + ".json"
    file = open(file_name, "w", encoding="utf-8")
    json.dump(listings, file, indent=2)
    file.close()
    return file_name


def save_csv(listings, search_term):
    file_name = search_term + ".csv"
    file = open(file_name, "w", newline="", encoding="utf-8")
    writer = csv.writer(file)
    writer.writerow(["name", "price", "status", "shipping", "free_returns", "items_sold"])

    for listing in listings:
        row = [
            listing["name"],
            listing["price"],
            listing["status"],
            listing["shipping"],
            listing["free_returns"],
            listing["items_sold"],
        ]
        writer.writerow(row)

    file.close()
    return file_name


def main():
    parser = argparse.ArgumentParser(description="Scrape eBay search results into JSON or CSV.")
    parser.add_argument("--search", required=True, help="Search term, e.g. 'garden tools'")
    parser.add_argument("--pages-dir", help="Read page-1.html..page-10.html from this directory instead of the network")
    parser.add_argument("--csv", action="store_true", help="Save results as CSV instead of JSON")
    args = parser.parse_args()

    listings = scrape(args.search, args.pages_dir)

    if args.csv:
        file_name = save_csv(listings, args.search)
    else:
        file_name = save_json(listings, args.search)

    print("Saved " + str(len(listings)) + " listings to " + file_name)


if __name__ == "__main__":
    main()
