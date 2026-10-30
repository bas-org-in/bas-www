"""Browser tests of the home page welcome banner.

They check AT-47 and AT-48 of docs/style-system-acceptance-tests.md in
bas-org-in/bas-site-ops (requirements ST-75 and ST-76). They send
requests only.

Usage:
  uv run --no-project --with playwright==1.55.0 python -I tests/home-banner.py HOME_URL

HOME_URL is the home page, for example https://bas.org.in/ or the local
copy that tests/serve-local.sh serves. For a site behind a password
prompt, set BAS_TEST_HTTP_USER and BAS_TEST_HTTP_PASSWORD. Set
BAS_TEST_CHROME to a Chrome binary to use it instead of the Playwright
browser.
"""

import os
import sys

from playwright.sync_api import sync_playwright

BANNER_JS = """() => {
  const rgba = s => (s.match(/[\\d.]+/g) || []).map(Number).concat([1]).slice(0, 4);
  const token = name => { const d = document.createElement('div');
    d.style.color = `var(${name})`; document.body.append(d);
    const c = getComputedStyle(d).color; d.remove(); return c; };
  const banner = document.querySelector('.bas-home-banner');
  if (!banner) return null;
  const inner = banner.querySelector('.bas-home-banner__inner') || banner;
  const logo = banner.querySelector('img');
  const text = banner.querySelector('p');
  const layout = document.querySelector('.bas-home-layout');
  const box = e => e.getBoundingClientRect();
  const bs = getComputedStyle(banner), is = getComputedStyle(inner), ts = getComputedStyle(text);
  return {
    height: box(banner).height, bg: bs.backgroundColor,
    rule: is.borderBottomWidth !== '0px' ? is.borderBottomColor : bs.borderBottomColor,
    ruleToken: token('--bas-rule'), brs: banner.querySelectorAll('br').length,
    logo: [box(logo).left, box(logo).top, box(logo).width, box(logo).height],
    text: [box(text).left, box(text).top, box(text).width, box(text).height],
    size: ts.fontSize, weight: Number(ts.fontWeight), fg: rgba(ts.color),
    page: rgba(getComputedStyle(document.body).backgroundColor),
    layout: layout ? box(layout).left : null,
    scrollWidth: document.documentElement.scrollWidth,
  };
}"""

failures = 0


def check(name, ok, detail="", test="AT-47"):
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


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    url = sys.argv[1]
    user, password = os.environ.get("BAS_TEST_HTTP_USER"), os.environ.get("BAS_TEST_HTTP_PASSWORD")
    credentials = {"username": user, "password": password} if user else None
    chrome = os.environ.get("BAS_TEST_CHROME")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, executable_path=chrome) if chrome else p.chromium.launch(headless=True)
        for scheme in ("light", "dark"):
            page = browser.new_page(viewport={"width": 1280, "height": 900}, color_scheme=scheme,
                                    http_credentials=credentials)
            page.goto(url, wait_until="networkidle")
            b = page.evaluate(BANNER_JS)
            if b is None:
                check(f"{scheme}: the page has .bas-home-banner", False, "not found")
                page.close()
                continue
            check(f"{scheme}: banner is {b['height']:.0f} px high", b["height"] <= 160, "at most 160")
            check(f"{scheme}: banner has no background", b["bg"] in ("rgba(0, 0, 0, 0)", "transparent"), b["bg"])
            check(f"{scheme}: banner has the --bas-rule bottom border", b["rule"] == b["ruleToken"], b["rule"])
            check(f"{scheme}: banner has no <br>", b["brs"] == 0, str(b["brs"]))
            check(f"{scheme}: logo is {b['logo'][2]:.0f} px wide", abs(b["logo"][2] - 120) < 1, "needs 120")
            centre = abs((b["logo"][1] + b["logo"][3] / 2) - (b["text"][1] + b["text"][3] / 2))
            check(f"{scheme}: logo and text centres differ by {centre:.0f} px", centre <= 4, "at most 4")
            check(f"{scheme}: text is {b['size']} at weight {b['weight']}", b["size"] == "20px" and b["weight"] >= 400)
            ratio = contrast(b["fg"], b["page"])
            check(f"{scheme}: text contrast {ratio:.1f}:1", ratio >= 4.5, "needs 4.5")
            if b["layout"] is not None:
                offset = abs(b["logo"][0] - b["layout"])
                check(f"{scheme}: logo is {offset:.0f} px from the left edge of the layout", offset <= 2, "at most 2")
            page.close()
        for width in (1407, 1280, 1024):
            page = browser.new_page(viewport={"width": width, "height": 900}, http_credentials=credentials)
            page.goto(url, wait_until="networkidle")
            edges = page.evaluate("""() => { const r = s => document.querySelector(s).getBoundingClientRect();
              return {brand: r('.bas-site-nav__brand').left, toggle: r('.bas-theme-toggle').right,
                      left: r('.bas-home-banner__inner').left, right: r('.bas-home-banner__inner').right,
                      layout: document.querySelector('.bas-home-layout').getBoundingClientRect().left}; }""")
            centre = (edges["left"] + edges["right"]) / 2 - width / 2
            check(f"{width} px: content is {centre:+.0f} px from the centre", abs(centre) <= 1, "at most 1", "AT-48")
            check(f"{width} px: content starts {edges['left'] - edges['brand']:+.0f} px from the nav name",
                  abs(edges["left"] - edges["brand"]) <= 1, "at most 1", "AT-48")
            check(f"{width} px: content ends {edges['right'] - edges['toggle']:+.0f} px from the toggle",
                  abs(edges["right"] - edges["toggle"]) <= 1, "at most 1", "AT-48")
            check(f"{width} px: the layout starts {edges['layout'] - edges['left']:+.0f} px from the banner",
                  abs(edges["layout"] - edges["left"]) <= 1, "at most 1", "AT-48")
            page.close()
        page = browser.new_page(viewport={"width": 390, "height": 900}, http_credentials=credentials)
        page.goto(url, wait_until="networkidle")
        b = page.evaluate(BANNER_JS)
        if b is not None:
            logo_centre = b["logo"][0] + b["logo"][2] / 2
            text_centre = b["text"][0] + b["text"][2] / 2
            check("390 px: logo is above the text", b["logo"][1] + b["logo"][3] <= b["text"][1])
            check(f"390 px: logo is centred over the text ({abs(logo_centre - text_centre):.0f} px off)",
                  abs(logo_centre - text_centre) <= 4, "at most 4")
            check(f"390 px: page is {b['scrollWidth']} px wide", b["scrollWidth"] <= 390, "no overflow")
        page.close()
        browser.close()
    print(f"{failures} failure(s)")
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
