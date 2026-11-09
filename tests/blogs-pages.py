"""Browser tests of the pages of the /blogs/ listing (AAT-42).

They check AA-33 and AA-34 of docs/article-addresses.md in bas-org-in/bas-site-ops,
with a fake WordPress REST API of 30 articles.

Usage:
  uv run --no-project --with playwright==1.55.0 python -I tests/blogs-pages.py BLOGS_URL

Set BAS_TEST_CHROME to a Chrome binary to use it instead of the Playwright browser.
"""

import json
import os
import sys
from urllib.parse import parse_qs, urlparse

from playwright.sync_api import sync_playwright

ARTICLES = [{"id": i, "title": {"rendered": f"Article {i}"}, "link": f"https://bas.org.in/blogs/a-{i}/",
             "date": "2025-01-01"} for i in range(1, 31)]
failures = 0


def check(name, ok, detail=""):
    global failures
    print(("ok   " if ok else "FAIL ") + "AAT-42 " + name + (f" ({detail})" if detail and not ok else ""))
    if not ok:
        failures += 1


def fake_api(route, asked):
    url = urlparse(route.request.url)
    query = {k: v[0] for k, v in parse_qs(url.query).items()}
    headers = {}
    if url.path.endswith("/categories"):
        body = [{"id": 5, "slug": "blogs"}]
    elif url.path.endswith("/tags"):
        body = [{"id": 11, "slug": "awe"}]
    elif url.path.endswith("/posts"):
        asked.append(query)
        size, page = int(query.get("per_page", 12)), int(query.get("page", 1))
        pages = -(-len(ARTICLES) // size)
        if page > pages:
            return route.fulfill(status=400, content_type="application/json", body=json.dumps({"code": "rest_post_invalid_page_number"}))
        body = ARTICLES[(page - 1) * size: page * size]
        headers = {"X-WP-Total": str(len(ARTICLES)), "X-WP-TotalPages": str(pages)}
    else:
        return route.abort()
    route.fulfill(status=200, content_type="application/json", headers=headers, body=json.dumps(body))


def open_page(browser, url):
    page = browser.new_page()
    asked = []
    page.route("**/wp-json/**", lambda route: fake_api(route, asked))
    page.goto(url, wait_until="networkidle")
    titles = page.eval_on_selector_all(".bas-post-card__title", "e => e.map(x => x.textContent.trim())")
    links = page.eval_on_selector_all(".bas-wp-posts__pages a", "e => e.map(x => [x.textContent.trim(), x.getAttribute('href')])")
    status = page.eval_on_selector_all(".bas-wp-posts__status", "e => e.map(x => x.textContent.trim())")
    page.close()
    return titles, links, status, asked


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    base = sys.argv[1].split("?")[0]
    chrome = os.environ.get("BAS_TEST_CHROME")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, executable_path=chrome) if chrome else p.chromium.launch(headless=True)
        titles, links, _, asked = open_page(browser, base)
        check("page 1 shows 12", len(titles) == 12 and titles[0] == "Article 1", titles[:2])
        check("page 1 links to page 2 only", links == [["Older articles", "/blogs/?page=2"]], links)

        titles, links, _, asked = open_page(browser, base + "?page=2")
        check("page 2 asks for page 2", any(q.get("page") == "2" for q in asked), asked)
        check("page 2 shows 12", len(titles) == 12 and titles[0] == "Article 13", titles[:2])
        check("page 2 links both ways", links == [["Newer articles", "/blogs/"], ["Older articles", "/blogs/?page=3"]], links)

        titles, links, _, _ = open_page(browser, base + "?page=3")
        check("page 3 shows 6", len(titles) == 6, len(titles))
        check("page 3 links to newer only", links == [["Newer articles", "/blogs/?page=2"]], links)

        titles, links, _, asked = open_page(browser, base + "?topic=awe&page=2")
        check("topic is kept in the request", any(q.get("tags") == "11" and q.get("page") == "2" for q in asked), asked)
        check("topic is kept in the links", links == [["Newer articles", "/blogs/?topic=awe"],
                                                      ["Older articles", "/blogs/?topic=awe&page=3"]], links)

        titles, links, _, asked = open_page(browser, base + "?page=x")
        check("a bad page shows page 1", len(titles) == 12 and titles[0] == "Article 1", titles[:2])

        titles, links, status, _ = open_page(browser, base + "?page=9")
        check("a page past the last shows the message and the newer link",
              titles == [] and status == ["No articles are published yet."] and links == [["Newer articles", "/blogs/?page=8"]],
              [status, links])
        browser.close()
    print(f"{failures} failure(s)")
    sys.exit(1 if failures else 0)


main()
