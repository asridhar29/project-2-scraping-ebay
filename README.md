# eBay Scraper

`ebay-dl.py` is a command-line tool that scrapes eBay search results and saves
them as structured JSON (or CSV) data.

Given a search term, it fetches the first 10 pages of eBay search results
(`_nkw` for the term, `_pgn` for the page number), parses each listing out of
the HTML with BeautifulSoup, and writes out a list of dictionaries with these
keys:

- `name` — item title (string)
- `price` — price in integer cents (e.g. `$54.99` → `5499`; if a price range
  is shown, the lower value is used)
- `status` — condition string (e.g. `"Brand New"`, `"Refurbished"`)
- `shipping` — shipping cost in integer cents (`0` for free shipping)
- `free_returns` — `true`/`false`
- `items_sold` — integer count of items sold

If a field can't be found on a listing, its key is kept with a value of
`null`/`None`.

## Setup

```bash
git clone https://github.com/asridhar29/project-2-scraping-ebay.git
cd project-2-scraping-ebay
python -m pip install requests beautifulsoup4
```

## Usage

Live scrape (hits eBay over the network):

```bash
python ebay-dl.py --search "garden tools"
```

Offline / practice mode, reading `page-1.html` .. `page-10.html` from a local
directory instead of making network requests:

```bash
python ebay-dl.py --search "garden tools" --pages-dir practice-pages
```

Add `--csv` to save a `.csv` file instead of `.json`:

```bash
python ebay-dl.py --search "garden tools" --pages-dir practice-pages --csv
```

In both modes the request/parsing logic is identical — `--pages-dir` only
swaps out *where* the HTML for each page comes from, which is what lets the
tool be tested without live network access or eBay's bot/robot checks.

## Generating the deliverable files

The three JSON files and three CSV files in this repo were generated with:

```bash
python ebay-dl.py --search "garden tools" --pages-dir practice-pages
python ebay-dl.py --search "vintage camera" --pages-dir practice-pages
python ebay-dl.py --search "bluetooth speaker" --pages-dir practice-pages

python ebay-dl.py --search "garden tools" --pages-dir practice-pages --csv
python ebay-dl.py --search "vintage camera" --pages-dir practice-pages --csv
python ebay-dl.py --search "bluetooth speaker" --pages-dir practice-pages --csv
```

### Live data vs. practice data

**All six output files (`garden tools.json`, `vintage camera.json`,
`bluetooth speaker.json`, and their `.csv` counterparts) were generated from
the artificial practice pages in `practice-pages/`, not from live eBay data.**

The live-fetch code path (`requests` + a `Mozilla/5.0` User-Agent header,
`timeout=10`, a pause between requests) is implemented and was exercised
directly against `https://www.ebay.com/sch/i.html` during development — eBay
responded with `HTTP 403` ("Error Page | eBay") to requests from this
environment, which is exactly the kind of live blocking/robot check the
`--pages-dir` option exists to work around. The `practice-pages/` directory
contains 10 synthetic HTML pages built with the same CSS classes eBay's real
search-result markup uses (`s-item`, `s-item__title`, `s-item__price`,
`s-item__shipping`, `s-item__free-returns`, `s-item__quantitySold`, etc.), so
the parsing logic exercised for these deliverables is the same code that runs
against live pages — only the HTML source differs.

## Extra credit: CSV support

Pass `--csv` to write a CSV file (same column order as the JSON keys) instead
of a JSON file. See `submission.toml` for the feature flag and the `.csv`
files in this repo for example output.
