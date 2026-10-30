"""Browser tests of the Events section of the home page.

They check AT-51 of docs/style-system-acceptance-tests.md in
bas-org-in/bas-site-ops (requirement ST-79). They send requests only.

Usage:
  uv run --no-project --with playwright==1.55.0 python -I tests/home-events.py HOME_URL

HOME_URL is the home page, for example https://bas.org.in/. The test
reads the expected events from the same REST API as the page. For a site
behind a password prompt, set BAS_TEST_HTTP_USER and
BAS_TEST_HTTP_PASSWORD. Set BAS_TEST_CHROME to a Chrome binary to use it
instead of the Playwright browser.
"""

import os
import sys
from itertools import pairwise
from urllib.parse import urljoin

from playwright.sync_api import sync_playwright

API = "/wp-json/tribe/events/v1/events"

CARDS_JS = """() => {
  const box = e => { const r = e.getBoundingClientRect(); return [r.left, r.top, r.width, r.height]; };
  const section = document.querySelector('[data-bas-events]');
  if (!section) return null;
  const social = document.querySelector('.fa-telegram').closest('.row');
  const whatWeDo = [...document.querySelectorAll('h2')].find(h => h.textContent.trim() === 'What we do');
  const all = section.querySelector('.bas-home-events__head a');
  return {
    heading: section.querySelector('h2').textContent.trim(), allHref: all && all.getAttribute('href'),
    top: box(section)[1], bottom: box(section)[1] + box(section)[3],
    socialBottom: box(social)[1] + box(social)[3], whatWeDoTop: box(whatWeDo)[1],
    currentEvent: !!document.getElementById('currentEvent'),
    scrollWidth: document.documentElement.scrollWidth,
    cards: [...section.querySelectorAll('.bas-event-card')].map(c => ({
      label: c.querySelector('.bas-event-card__label').textContent.trim(),
      title: c.querySelector('.bas-post-card__title').textContent.trim(),
      href: c.querySelector('.bas-post-card__title a').href,
      date: c.querySelector('.bas-post-card__meta').textContent.trim(),
      venue: (c.querySelector('.bas-event-card__venue') || {}).textContent || '',
      image: !!(c.querySelector('img') && c.querySelector('img').complete && c.querySelector('img').naturalWidth),
      box: box(c)})),
  };
}"""

COLOURS_JS = """() => {
  const rgba = s => (s.match(/[\\d.]+/g) || []).map(Number).concat([1]).slice(0, 4);
  return [...document.querySelectorAll('.bas-event-card')].flatMap(c => {
    const bg = rgba(getComputedStyle(c).backgroundColor);
    return [...c.querySelectorAll('.bas-event-card__label, .bas-post-card__meta, .bas-post-card__title a, .bas-event-card__venue')]
      .map(e => [e.className || e.parentElement.className + ' a', rgba(getComputedStyle(e).color), bg]);
  });
}"""

failures = 0


def check(name, ok, detail=""):
    global failures
    print(("ok   " if ok else "FAIL ") + "AT-51 " + name + (f" ({detail})" if detail and not ok else ""))
    if not ok:
        failures += 1


def luminance(rgb):
    def channel(c):
        c = c / 255
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (channel(c) for c in rgb[:3])
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(fg, bg):
    hi, lo = sorted([luminance(fg), luminance(bg)], reverse=True)
    return (hi + 0.05) / (lo + 0.05)


def expected(request, url):
    """The cards the page should show: upcoming soonest first, then past most recent first."""
    def get(query):
        response = request.get(urljoin(url, API) + "?" + query)
        return response.json() if response.ok else {}
    upcoming = get("ends_after=now&per_page=3").get("events", [])
    cards = [("Upcoming", e) for e in upcoming[:3]]
    if len(cards) < 3:
        first = get("ends_before=now&start_date=2000-01-01&per_page=50")
        events = first.get("events", [])
        pages = first.get("total_pages") or 1
        if pages > 1:
            previous = events if pages == 2 else get(f"ends_before=now&start_date=2000-01-01&per_page=50&page={pages - 1}").get("events", [])
            events = previous + get(f"ends_before=now&start_date=2000-01-01&per_page=50&page={pages}").get("events", [])
        cards += [("Past", e) for e in list(reversed(events))[: 3 - len(cards)]]
    return [(label, e["url"], e.get("venue") or {}) for label, e in cards]


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    url = sys.argv[1]
    user, password = os.environ.get("BAS_TEST_HTTP_USER"), os.environ.get("BAS_TEST_HTTP_PASSWORD")
    credentials = {"username": user, "password": password} if user else None
    chrome = os.environ.get("BAS_TEST_CHROME")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, executable_path=chrome) if chrome else p.chromium.launch(headless=True)
        ctx = browser.new_context(viewport={"width": 1280, "height": 900}, http_credentials=credentials)
        want = expected(ctx.request, url)
        print(f"     API: {len(want)} card(s) expected: {[w[0] for w in want]}")
        page = ctx.new_page()
        errors = []
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.goto(url, wait_until="networkidle")
        s = page.evaluate(CARDS_JS)
        if s is None:
            check("the home page has the Events section", False, "not found")
        else:
            check("heading is Events", s["heading"] == "Events", s["heading"])
            check("All events links to /events/", s["allHref"] == "/events/", str(s["allHref"]))
            check("section is under the social links", s["top"] >= s["socialBottom"] - 1)
            check("section is above What we do", s["bottom"] <= s["whatWeDoTop"] + 1)
            check("page has no #currentEvent", not s["currentEvent"])
            got = [(c["label"], c["href"]) for c in s["cards"]]
            check(f"cards match the API ({len(got)})", got == [(w[0], w[1]) for w in want], str(got))
            for c, w in zip(s["cards"], want, strict=False):
                check(f"card '{c['title'][:30]}' has image, date and title", c["image"] and c["date"] and c["title"],
                      f"image={c['image']} date={c['date']!r}")
                if w[2].get("venue"):
                    check(f"card '{c['title'][:30]}' has the venue", c["venue"].strip() != "", "no venue")
            tops = {round(c["box"][1]) for c in s["cards"]}
            check("cards are in one row at 1280 px", len(tops) <= 1, str(tops))
            check("no JavaScript errors", errors == [], str(errors))
        page.close()

        for scheme in ("light", "dark"):
            page = browser.new_page(viewport={"width": 1280, "height": 900}, color_scheme=scheme, http_credentials=credentials)
            page.goto(url, wait_until="networkidle")
            for cls, fg, bg in page.evaluate(COLOURS_JS):
                ratio = contrast(fg, bg)
                check(f"{scheme}: {cls.split()[0]} contrast {ratio:.1f}:1", ratio >= 4.5, "needs 4.5")
            page.close()

        page = browser.new_page(viewport={"width": 390, "height": 900}, http_credentials=credentials)
        page.goto(url, wait_until="networkidle")
        s = page.evaluate(CARDS_JS)
        if s and s["cards"]:
            stacked = all(b["box"][1] >= a["box"][1] + a["box"][3] for a, b in pairwise(s["cards"]))
            check("cards are in one column at 390 px", stacked)
            check(f"page is {s['scrollWidth']} px wide at 390 px", s["scrollWidth"] <= 390)
        page.close()

        page = browser.new_page(viewport={"width": 1280, "height": 900}, http_credentials=credentials)
        errors = []
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.route("**/wp-json/tribe/**", lambda route: route.abort())
        page.goto(url, wait_until="networkidle")
        s = page.evaluate(CARDS_JS)
        check("API blocked: heading and link stay, no cards",
              s is not None and s["heading"] == "Events" and s["allHref"] == "/events/" and s["cards"] == [])
        check("API blocked: no JavaScript errors", errors == [], str(errors))
        page.close()
        browser.close()
    print(f"{failures} failure(s)")
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
