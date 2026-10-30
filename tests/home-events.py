"""Browser tests of the Events section of the home page.

They check AT-51 and AT-58 of docs/style-system-acceptance-tests.md in
bas-org-in/bas-site-ops (requirements ST-79 and ST-85). They send
requests only.

Usage:
  uv run --no-project --with playwright==1.55.0 python -I tests/home-events.py HOME_URL

HOME_URL is the home page, for example https://bas.org.in/. The test
reads the expected events from The Events Calendar REST API. For a site
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
  const main = document.querySelector('[data-bas-toc-root]');
  const all = section.querySelector('.bas-home-events__head a');
  return {
    heading: section.querySelector('h2').textContent.trim(), allHref: all && all.getAttribute('href'),
    top: box(section)[1], bottom: box(section)[1] + box(section)[3],
    socialBottom: box(social)[1] + box(social)[3], whatWeDoTop: box(whatWeDo)[1],
    left: box(section)[0], mainRight: main ? box(main)[0] + box(main)[2] : null,
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


def check(name, ok, detail="", test="AT-51"):
    global failures
    print(("ok   " if ok else "FAIL ") + test + " " + name + (f" ({detail})" if detail and not ok else ""))
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


HOME_EVENTS = "/wp-json/bas/v1/home-events"


def check_one_request(browser, request, url, credentials, want):
    """AT-58: one early request to the home events endpoint."""
    response = request.get(urljoin(url, HOME_EVENTS))
    data = response.json() if response.ok else None
    entries = data if isinstance(data, list) else []
    check(f"{HOME_EVENTS} returns 200 and a list of at most 3", response.ok and isinstance(data, list)
          and len(entries) <= 3, f"{response.status} {str(data)[:80]}", "AT-58")
    got = [(e.get("label"), (e.get("event") or {}).get("url")) for e in entries]
    check("the endpoint's order and labels match The Events Calendar API", got == [(w[0], w[1]) for w in want],
          str(got), "AT-58")
    check("each entry has the event's url, title and start_date",
          all({"url", "title", "start_date"} <= set(e.get("event") or {}) for e in entries), "", "AT-58")

    page = browser.new_page(viewport={"width": 390, "height": 844}, http_credentials=credentials)
    api_requests = []
    page.on("request", lambda r: "/wp-json/" in r.url and api_requests.append(r.url))
    page.goto(url, wait_until="networkidle")
    preload = page.evaluate(f"""() => [...document.head.querySelectorAll('link[rel="preload"]')]
      .some(l => l.getAttribute('href') === '{HOME_EVENTS}')""")
    check("the <head> has a preload link for the endpoint", preload, "", "AT-58")
    paths = [r.split("://", 1)[-1].split("/", 1)[-1] for r in api_requests]
    check(f"the page makes exactly one /wp-json/ request, to the endpoint ({len(paths)})",
          paths == [HOME_EVENTS.lstrip("/")], str(paths), "AT-58")
    timing = page.evaluate(f"""() => {{
      const e = performance.getEntriesByType('resource').find(r => r.name.endsWith('{HOME_EVENTS}'));
      const n = performance.getEntriesByType('navigation')[0];
      return e ? [e.startTime, n.domContentLoadedEventStart] : null; }}""")
    check(f"the request starts before DOMContentLoaded ({timing})", bool(timing) and timing[0] < timing[1], "", "AT-58")
    cards = page.eval_on_selector_all(".bas-event-card .bas-post-card__title a", "els => els.map(a => a.href)")
    check(f"the {len(want)} expected card(s) show", cards == [w[1] for w in want], str(cards), "AT-58")
    page.close()


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
            check("section is in the events column, right of the main content (ST-80)",
                  s["mainRight"] is not None and s["left"] >= s["mainRight"])
            check("page has no #currentEvent", not s["currentEvent"])
            got = [(c["label"], c["href"]) for c in s["cards"]]
            check(f"cards match the API ({len(got)})", got == [(w[0], w[1]) for w in want], str(got))
            for c, w in zip(s["cards"], want, strict=False):
                check(f"card '{c['title'][:30]}' has image, date and title", c["image"] and c["date"] and c["title"],
                      f"image={c['image']} date={c['date']!r}")
                if w[2].get("venue"):
                    check(f"card '{c['title'][:30]}' has the venue", c["venue"].strip() != "", "no venue")
            stacked = all(b["box"][1] >= a["box"][1] + a["box"][3] for a, b in pairwise(s["cards"]))
            check("cards stand one above the other at 1280 px", stacked)
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
            check("section is above What we do at 390 px", s["bottom"] <= s["whatWeDoTop"] + 1)
            check(f"page is {s['scrollWidth']} px wide at 390 px", s["scrollWidth"] <= 390)
        page.close()

        page = browser.new_page(viewport={"width": 1280, "height": 900}, http_credentials=credentials)
        errors = []
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.route("**/wp-json/**", lambda route: route.abort())
        page.goto(url, wait_until="networkidle")
        s = page.evaluate(CARDS_JS)
        check("API blocked: heading and link stay, no cards",
              s is not None and s["heading"] == "Events" and s["allHref"] == "/events/" and s["cards"] == [])
        check("API blocked: no JavaScript errors", errors == [], str(errors))
        page.close()
        check_one_request(browser, ctx.request, url, credentials, want)
        browser.close()
    print(f"{failures} failure(s)")
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
