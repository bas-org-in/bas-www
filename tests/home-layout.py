"""Browser tests of the home page layout, contents list and event images.

They check AT-52 to AT-55 and the home page part of AT-57 of
docs/style-system-acceptance-tests.md in bas-org-in/bas-site-ops
(requirements ST-80 to ST-83). They send requests only.

Usage:
  uv run --no-project --with playwright==1.55.0 python -I tests/home-layout.py HOME_URL

HOME_URL is the home page, for example https://bas.org.in/. For a site
behind a password prompt, set BAS_TEST_HTTP_USER and
BAS_TEST_HTTP_PASSWORD. Set BAS_TEST_CHROME to a Chrome binary to use it
instead of the Playwright browser.
"""

import os
import sys

from playwright.sync_api import sync_playwright

LAYOUT_JS = """() => {
  const box = s => { const e = document.querySelector(s);
    if (!e || getComputedStyle(e).display === 'none') return null;
    const r = e.getBoundingClientRect();
    return {x: r.left, y: r.top + scrollY, w: r.width, h: r.height, right: r.right}; };
  const sections = [...document.querySelectorAll('[data-bas-toc-root] :is(h1, h2)')]
    .filter(h => h.textContent.trim()).map(h => h.getBoundingClientRect().left);
  return {toc: box('.bas-page-toc__list'), tocNav: box('nav.bas-page-toc'), button: box('.bas-page-toc__button'),
          main: box('[data-bas-toc-root]'), events: box('.bas-home-events'),
          brand: box('.bas-site-nav__brand'), toggle: box('.bas-theme-toggle'),
          sections, overflow: document.documentElement.scrollWidth - innerWidth};
}"""

TOC_JS = """() => {
  const nav = document.querySelector('nav.bas-page-toc');
  if (!nav) return null;
  const links = [...nav.querySelectorAll('.bas-page-toc__list a')].map(a => ({
    text: a.textContent.trim(), href: a.getAttribute('href')}));
  const heads = [...document.querySelectorAll('[data-bas-toc-root] :is(h1, h2)')]
    .filter(h => h.textContent.trim() && !h.closest('.bas-home-events, .bas-post-card'))
    .map(h => ({text: h.textContent.trim(), id: h.id}));
  return {label: nav.getAttribute('aria-label'), links, heads};
}"""

IMAGES_JS = """() => [...document.querySelectorAll('.bas-event-card img')].map(img => {
  const r = img.getBoundingClientRect(), card = img.closest('.bas-event-card').getBoundingClientRect();
  const s = getComputedStyle(img);
  return {w: r.width, h: r.height, nw: img.naturalWidth, nh: img.naturalHeight, fit: s.objectFit,
          cardW: card.width, cardX: card.left, x: r.left, top: r.top,
          venue: [...img.closest('.bas-event-card').querySelectorAll('.bas-event-card__venue')]
                   .some(v => getComputedStyle(v).display !== 'none'),
          title: img.closest('.bas-event-card').querySelector('.bas-post-card__title').getBoundingClientRect().left};
})"""

CONTRAST_JS = """() => {
  const rgba = s => (s.match(/[\\d.]+/g) || []).map(Number).concat([1]).slice(0, 4);
  const bg = e => { for (; e; e = e.parentElement) { const c = rgba(getComputedStyle(e).backgroundColor);
    if (c[3] > 0.5) return c; } return [255, 255, 255, 1]; };
  return [...document.querySelectorAll('.bas-page-toc a, .bas-page-toc__title, .bas-page-toc__button')]
    .filter(e => e.getBoundingClientRect().width > 0)
    .map(e => ({text: e.textContent.trim(), fg: rgba(getComputedStyle(e).color), bg: bg(e),
                border: e.matches('button') ? rgba(getComputedStyle(e).borderTopColor) : null}));
}"""

failures = 0


def check(test, name, ok, detail=""):
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


def near(a, b, tol=1):
    return a is not None and b is not None and abs(a - b) <= tol


def open_page(browser, url, credentials, width, height=900, scheme="light", js=True):
    page = browser.new_page(viewport={"width": width, "height": height}, color_scheme=scheme,
                            http_credentials=credentials, java_script_enabled=js)
    errors = []
    # Cloudflare adds its analytics beacon to the page; the site does not
    # load it. Networks that block analytics refuse it, so it is not counted.
    beacon = "cloudflareinsights.com"
    page.on("console", lambda m: errors.append(m.text)
            if m.type == "error" and beacon not in (m.location or {}).get("url", "") else None)
    page.on("requestfailed", lambda r: errors.append("failed " + r.url) if beacon not in r.url else None)
    page.goto(url, wait_until="networkidle")
    page.wait_for_timeout(300)
    return page, errors


def check_wide(browser, url, credentials):
    page, errors = open_page(browser, url, credentials, 1280)
    lay = page.evaluate(LAYOUT_JS)
    toc, main, events = lay["toc"], lay["main"], lay["events"]
    check("AT-52", "1280 px: contents list, main content and events exist", bool(toc and main and events))
    if toc and main and events:
        check("AT-52", f"1280 px: contents list is {toc['w']:.0f} px wide", near(toc["w"], 184), "needs 184")
        check("AT-52", f"1280 px: events column is {events['w']:.0f} px wide", near(events["w"], 280), "needs 280")
        check("AT-52", f"1280 px: gaps are {main['x'] - toc['right']:.0f} and {events['x'] - main['right']:.0f} px",
              near(main["x"] - toc["right"], 32) and near(events["x"] - main["right"], 32), "needs 32")
        check("AT-52", "1280 px: list, main and events are side by side",
              toc["right"] < main["x"] and main["right"] < events["x"] and near(lay["tocNav"]["y"], events["y"], 4))
        check("AT-52", "1280 px: outer edges line up with the nav brand and toggle",
              near(toc["x"], lay["brand"]["x"]) and near(events["right"], lay["toggle"]["right"]))
        check("AT-52", "1280 px: the sections stand one above the other",
              all(near(x, main["x"], 2) for x in lay["sections"]), str(sorted(set(round(x) for x in lay["sections"]))))
    check("AT-52", "1280 px: no 'On this page' button", lay["button"] is None)

    t = page.evaluate(TOC_JS)
    check("AT-53", "contents list is a nav labelled 'On this page'", bool(t) and t["label"] == "On this page")
    if t:
        expected = [{"text": h["text"], "href": "#" + h["id"]} for h in t["heads"]]
        check("AT-53", f"contents list has the {len(expected)} section headings in order",
              t["links"] == expected and len(expected) >= 4, str(t["links"]))
        check("AT-53", "the Events heading is not in the list", all(x["text"] != "Events" for x in t["links"]))
        last = t["links"][-1]["href"] if t["links"] else "#"
        page.click(f'.bas-page-toc__list a[href="{last}"]')
        page.wait_for_timeout(600)
        top = page.evaluate(f"document.getElementById({last[1:]!r}).getBoundingClientRect().top")
        check("AT-53", f"following the last link scrolls its heading into view (top {top:.0f})", 0 <= top < 900)
    page.evaluate("window.scrollTo(0, 2000)")
    page.wait_for_timeout(200)
    r = page.evaluate("(() => { const e = document.querySelector('.bas-page-toc__list'); if (!e) return [-1, -1];"
                      " const b = e.getBoundingClientRect(); return [b.top, b.bottom]; })()")
    check("AT-53", f"after a 2000 px scroll the list is in view ({r[0]:.0f} to {r[1]:.0f})", 0 <= r[0] and r[1] <= 900)

    imgs = page.evaluate(IMAGES_JS)
    check("AT-55", f"1280 px: {len(imgs)} event image(s)", len(imgs) >= 1)
    for i, m in enumerate(imgs):
        ratio_ok = m["nw"] and abs((m["w"] / m["h"]) - (m["nw"] / m["nh"])) / (m["nw"] / m["nh"]) <= 0.01
        capped = m["h"] >= 359
        check("AT-55", f"1280 px: image {i + 1} is {m['w']:.0f} x {m['h']:.0f}, source {m['nw']} x {m['nh']}",
              (ratio_ok or capped) and m["h"] <= 361 and m["fit"] != "cover" and near(m["w"], m["cardW"], 2),
              f"fit {m['fit']}")
    page.close()
    check("AT-57", "1280 px: no failed request or console error", not errors, "; ".join(errors[:3]))


def check_medium(browser, url, credentials, width):
    page, errors = open_page(browser, url, credentials, width)
    lay = page.evaluate(LAYOUT_JS)
    main, events, button = lay["main"], lay["events"], lay["button"]
    check("AT-52", f"{width} px: no contents list column", lay["toc"] is None)
    check("AT-52", f"{width} px: events column is 260 px on the right",
          bool(events and main) and near(events["w"], 260) and events["x"] > main["right"],
          str(events and round(events["w"])))
    check("AT-52", f"{width} px: 'On this page' button is above the main content",
          bool(button and main) and button["y"] <= main["y"] + 8 and button["x"] < events["x"])
    check("AT-52", f"{width} px: no horizontal overflow", lay["overflow"] <= 0, str(lay["overflow"]))
    if width == 1024:
        check_button(page, width)
    page.close()
    check("AT-57", f"{width} px: no failed request or console error", not errors, "; ".join(errors[:3]))


def check_button(page, width):
    b = page.locator(".bas-page-toc__button")
    if not b.count() or not b.is_visible():
        check("AT-54", f"{width} px: the 'On this page' button shows", False)
        return
    h = b.bounding_box()["height"]
    controls = b.get_attribute("aria-controls")
    check("AT-54", f"{width} px: button is {h:.0f} px high", h >= 32, "at least 32")
    check("AT-54", f"{width} px: button is closed and controls the list",
          b.get_attribute("aria-expanded") == "false" and bool(controls)
          and page.locator(f"#{controls}").count() == 1 and not page.locator(f"#{controls}").is_visible())
    b.click()
    check("AT-54", f"{width} px: a click opens the list",
          b.get_attribute("aria-expanded") == "true" and page.locator(f"#{controls}").is_visible())
    page.keyboard.press("Escape")
    focused = page.evaluate("document.activeElement.classList.contains('bas-page-toc__button')")
    check("AT-54", f"{width} px: Escape closes the list and focus is on the button",
          b.get_attribute("aria-expanded") == "false" and focused)
    b.click()
    page.mouse.click(5, 880)
    check("AT-54", f"{width} px: a click outside closes the list", b.get_attribute("aria-expanded") == "false")
    b.click()
    link = page.locator(f"#{controls} a").nth(2)
    target = link.get_attribute("href")[1:]
    link.click()
    page.wait_for_timeout(600)
    top = page.evaluate(f"document.getElementById({target!r}).getBoundingClientRect().top")
    check("AT-54", f"{width} px: a link closes the list and scrolls to its heading (top {top:.0f})",
          b.get_attribute("aria-expanded") == "false" and 0 <= top < 900)
    page.evaluate("window.scrollTo(0, 2000)")
    page.wait_for_timeout(200)
    y = b.bounding_box()["y"]
    check("AT-54", f"{width} px: after a 2000 px scroll the button is in view (top {y:.0f})", 0 <= y < 900)


def check_phone(browser, url, credentials):
    page, errors = open_page(browser, url, credentials, 390, 844)
    lay = page.evaluate(LAYOUT_JS)
    main, events, button = lay["main"], lay["events"], lay["button"]
    check("AT-52", "390 px: events, button and main content in one column, in this order",
          bool(main and events and button) and events["y"] + events["h"] <= button["y"] <= main["y"] + 8
          and near(events["x"], main["x"], 2))
    imgs = page.evaluate(IMAGES_JS)
    for i, m in enumerate(imgs):
        ratio_ok = m["nw"] and abs((m["w"] / m["h"]) - (m["nw"] / m["nh"])) / (m["nw"] / m["nh"]) <= 0.01
        check("AT-55", f"390 px: image {i + 1} is {m['w']:.0f} x {m['h']:.0f} on the left of the text",
              near(m["w"], 120) and m["h"] <= 141 and (ratio_ok or m["h"] >= 139) and m["fit"] != "cover"
              and m["title"] > m["x"] + m["w"])
        check("AT-55", f"390 px: card {i + 1} shows no venue", not m["venue"])
    check_button(page, 390)
    page.close()
    check("AT-57", "390 px: no failed request or console error", not errors, "; ".join(errors[:3]))


def check_tall_image(browser, url, credentials):
    for width, limit in ((1280, 360), (390, 140)):
        page, _ = open_page(browser, url, credentials, width)
        m = page.evaluate("""async () => {
          const img = document.querySelector('.bas-event-card img');
          if (!img) return null;
          img.src = 'data:image/svg+xml,' + encodeURIComponent(
            '<svg xmlns="http://www.w3.org/2000/svg" width="100" height="300"><rect width="100" height="300"/></svg>');
          await img.decode();
          const r = img.getBoundingClientRect();
          return {h: r.height, fit: getComputedStyle(img).objectFit}; }""")
        check("AT-55", f"{width} px: a 1:3 test image shows whole at {limit} px high",
              bool(m) and near(m["h"], limit) and m["fit"] == "contain", str(m))
        page.close()


def check_overflow(browser, url, credentials):
    bad = []
    for width in (360, 390, 600, 767, 768, 900, 1099, 1100, 1280, 1600):
        page, _ = open_page(browser, url, credentials, width)
        if page.evaluate(LAYOUT_JS)["overflow"] > 0:
            bad.append(width)
        page.close()
    check("AT-52", "no horizontal overflow from 360 to 1600 px", not bad, str(bad))


def check_no_js(browser, url, credentials):
    page, _ = open_page(browser, url, credentials, 1280, js=False)
    r = page.evaluate("""() => { const t = document.querySelector('.bas-page-toc');
      const m = document.querySelector('[data-bas-toc-root]').getBoundingClientRect();
      const n = document.querySelector('.bas-site-nav__brand').getBoundingClientRect();
      return {toc: !!t && t.getBoundingClientRect().width > 0, left: m.left - n.left}; }""")
    check("AT-53", f"no JavaScript: no list and no empty column (main starts {r['left']:.0f} px from the brand)",
          not r["toc"] and abs(r["left"]) <= 1)
    page.close()


def check_contrast(browser, url, credentials):
    for scheme in ("light", "dark"):
        for width in (1280, 390):
            page, _ = open_page(browser, url, credentials, width, scheme=scheme)
            if width == 390 and page.locator(".bas-page-toc__button").count():
                page.click(".bas-page-toc__button")
            items = page.evaluate(CONTRAST_JS)
            low = [f"{i['text'][:20]} {contrast(i['fg'], i['bg']):.1f}" for i in items
                   if contrast(i["fg"], i["bg"]) < 4.5]
            low += [f"border {contrast(i['border'], i['bg']):.1f}" for i in items
                    if i["border"] and contrast(i["border"], i["bg"]) < 3]
            check("AT-57", f"{scheme} {width} px: contents list text 4.5:1, button border 3:1",
                  bool(items) and not low, "; ".join(low[:3]))
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
        check_wide(browser, url, credentials)
        check_medium(browser, url, credentials, 1024)
        check_medium(browser, url, credentials, 768)
        check_phone(browser, url, credentials)
        check_tall_image(browser, url, credentials)
        check_overflow(browser, url, credentials)
        check_no_js(browser, url, credentials)
        check_contrast(browser, url, credentials)
        browser.close()
    print(f"{failures} failure(s)")
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
