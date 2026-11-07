"""Browser tests of the topic links on /blogs/ (AAT-40 and AAT-41).

They check AA-30 to AA-32 of docs/article-addresses.md in bas-org-in/bas-site-ops,
with a fake WordPress REST API, so they need no live data.

Usage:
  uv run --no-project --with playwright==1.55.0 python -I tests/blogs-topics.py BLOGS_URL

BLOGS_URL is the /blogs/ page, for example the local copy that tests/serve-local.sh
serves. Set BAS_TEST_CHROME to a Chrome binary to use it instead of the Playwright
browser.
"""

import json
import os
import sys
from urllib.parse import parse_qs, urlparse

from playwright.sync_api import sync_playwright

CATEGORIES = [{"id": 5, "slug": "blogs"}, {"id": 9, "slug": "gallery"}]
TAGS = {"awe": 11, "star-party": 12}
POSTS = {
    11: [{"id": 1, "title": {"rendered": "AWE report"}, "link": "https://bas.org.in/blogs/awe-x/", "date": "2025-11-15"}],
    12: [{"id": 2, "title": {"rendered": "Star party report"}, "link": "https://bas.org.in/blogs/sp-x/", "date": "2023-12-09"}],
}
failures = 0


def check(name, ok, detail="", test="AAT-41"):
    global failures
    print(("ok   " if ok else "FAIL ") + test + " " + name + (f" ({detail})" if detail and not ok else ""))
    if not ok:
        failures += 1


def fake_api(route, asked):
    url = urlparse(route.request.url)
    query = {k: v[0] for k, v in parse_qs(url.query).items()}
    if url.path.endswith("/categories"):
        body = CATEGORIES
    elif url.path.endswith("/tags"):
        body = [{"id": TAGS[s], "slug": s} for s in query.get("slug", "").split(",") if s in TAGS]
    elif url.path.endswith("/posts"):
        asked.append(query)
        tag = int(query["tags"]) if "tags" in query else None
        body = POSTS[tag] if tag else POSTS[11] + POSTS[12]
    else:
        return route.abort()
    route.fulfill(status=200, content_type="application/json", body=json.dumps(body))


def open_topic(browser, url, topic):
    page = browser.new_page()
    asked = []
    page.route("**/wp-json/**", lambda route: fake_api(route, asked))
    page.goto(url + (f"?topic={topic}" if topic else ""), wait_until="networkidle")
    titles = page.eval_on_selector_all(".bas-post-card__title", "e => e.map(x => x.textContent.trim())")
    links = page.eval_on_selector_all(".bas-topic-links a", "e => e.map(x => [x.textContent.trim(), x.getAttribute('href'), x.getAttribute('aria-current')])")
    status = page.eval_on_selector_all(".bas-wp-posts__status", "e => e.map(x => x.textContent.trim())")
    page.close()
    return titles, links, status, asked


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    url = sys.argv[1].split("?")[0]
    chrome = os.environ.get("BAS_TEST_CHROME")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, executable_path=chrome) if chrome else p.chromium.launch(headless=True)
        titles, links, status, asked = open_topic(browser, url, None)
        names = [x[0] for x in links]
        check("three topic links in order", names == ["All", "AWE workshops", "Star parties"], names, "AAT-40")
        check("their addresses", [x[1] for x in links] == ["/blogs/", "/blogs/?topic=awe", "/blogs/?topic=star-party"],
              [x[1] for x in links], "AAT-40")
        check("All is current", [x[2] for x in links] == ["page", None, None], [x[2] for x in links], "AAT-40")
        check("all articles without a topic", titles == ["AWE report", "Star party report"], titles)
        check("no tag in the request", all("tags" not in q for q in asked), asked)

        titles, links, status, asked = open_topic(browser, url, "awe")
        check("AWE workshops is current", [x[2] for x in links] == [None, "page", None], [x[2] for x in links], "AAT-40")
        check("awe asks for tag 11", any(q.get("tags") == "11" and q.get("categories") == "5" for q in asked), asked)
        check("awe shows only its article", titles == ["AWE report"], titles)

        titles, links, status, asked = open_topic(browser, url, "star-party")
        check("star-party shows only its article", titles == ["Star party report"], titles)

        titles, links, status, asked = open_topic(browser, url, "nonsense")
        check("unknown topic shows all", titles == ["AWE report", "Star party report"], titles)
        check("unknown topic marks All", [x[2] for x in links] == ["page", None, None], [x[2] for x in links])

        POSTS[12] = []
        titles, links, status, asked = open_topic(browser, url, "star-party")
        check("a topic with no articles says so", titles == [] and status == ["No articles on this topic yet."], status)
        browser.close()
    print(f"{failures} failure(s)")
    sys.exit(1 if failures else 0)


main()
