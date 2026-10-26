"""Browser tests of the home page photo lightbox.

They check AT-39 to AT-42 of docs/style-system-acceptance-tests.md in
bas-org-in/bas-site-ops (requirements ST-67 to ST-70).

Usage:
  uv run --no-project --with playwright==1.55.0 python -I tests/home-photo-lightbox.py \\
      HOME_URL ARTICLE_URL OUTPUT_DIR

HOME_URL is the home page. On the local copy that tests/serve-local.sh
serves, imgur and Google Photos refuse some photos, because they refuse
the local referer, so AT-42 fails there; run the full test on staging.
ARTICLE_URL is a rendered article page with
images, for example a preview link of a review draft; the test compares
its lightbox markup with the copy on the home page. OUTPUT_DIR receives
the screenshots. For a site behind a password prompt, such as staging,
set BAS_TEST_HTTP_USER and BAS_TEST_HTTP_PASSWORD.
"""

import os
import re
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

HOME, ARTICLE, OUT = sys.argv[1], sys.argv[2], Path(sys.argv[3])
# Set BAS_TEST_CHROME to use another browser; without it, Google Chrome on
# Linux, else the Chromium of Playwright.
CHROME = os.environ.get("BAS_TEST_CHROME") or ("/usr/bin/google-chrome" if os.path.exists("/usr/bin/google-chrome") else None)
PLUGIN = "/wp/wp-content/plugins/bas-gallery-publisher/"
LIGHTBOX_FILES = ["lightbox.js", "article-lightbox.js", "assets/bas-lightbox.css"]
# Card photos have alternative text; video thumbnails have an empty alt.
# bas-lazy-media.js removes data-src once an image loads, so the address
# is data-src before loading and src after.
PHOTOS = "img.bas-lazy-media:not([alt=''])"
VIDEOS = "img.bas-lazy-media[alt='']"
MODAL = "[data-bas-article-lightbox]"

failures = 0


def check(name, condition, detail=""):
    global failures
    print(("ok   " if condition else "FAIL ") + name + (f" ({detail})" if detail and not condition else ""))
    if not condition:
        failures += 1


def normalise(html):
    return re.sub(r">\s+<", "><", re.sub(r"\s+", " ", html)).strip()


def modal_markup(page):
    return normalise(page.eval_on_selector(MODAL, "m => m.outerHTML"))


def photo_info(page):
    return page.eval_on_selector_all(
        PHOTOS,
        """imgs => imgs.map(i => ({
            role: i.getAttribute('role'),
            tabindex: i.getAttribute('tabindex'),
            label: i.getAttribute('aria-label') || '',
            alt: i.alt,
            src: i.getAttribute('data-bas-lightbox-src') ? new URL(i.getAttribute('data-bas-lightbox-src'), location.href).href : '',
            dataSrc: new URL(i.getAttribute('data-src') || i.getAttribute('src'), location.href).href,
            lines: i.parentElement.innerText.split('\\n').map(s => s.trim()).filter(Boolean),
            caption: i.getAttribute('data-bas-lightbox-caption') || '',
        }))""",
    )


def shown(page):
    return page.evaluate(
        """() => { const m = document.querySelector('[data-bas-article-lightbox]');
        if (!m || m.hidden) return null;
        const img = m.querySelector('[data-bas-public-gallery-modal-image]');
        const cap = m.querySelector('[data-bas-public-gallery-modal-caption]');
        const orig = m.querySelector('[data-bas-public-gallery-original]');
        return { src: img.src, caption: cap.textContent, original: orig.href,
                 focus: document.activeElement.getAttribute('aria-label') }; }"""
    )


def boxes(page):
    return page.eval_on_selector_all(
        PHOTOS,
        "imgs => imgs.map(i => { const r = i.getBoundingClientRect(); return [Math.round(r.x + scrollX), Math.round(r.y + scrollY), Math.round(r.width), Math.round(r.height)]; })",
    )


def load_all(page):
    """Scrolls through the page so that every lazy photo loads."""
    height = page.evaluate("document.body.scrollHeight")
    for y in range(0, height + 900, 600):
        page.evaluate(f"window.scrollTo(0, {y})")
        page.wait_for_timeout(50)
    page.wait_for_function(
        "sel => [...document.querySelectorAll(sel)].every(i => !i.hasAttribute('data-src') && i.complete)",
        arg=PHOTOS,
    )
    page.evaluate("window.scrollTo(0, 0)")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, executable_path=CHROME)
        auth = None
        if os.environ.get("BAS_TEST_HTTP_USER"):
            auth = {"username": os.environ["BAS_TEST_HTTP_USER"], "password": os.environ.get("BAS_TEST_HTTP_PASSWORD", "")}
        context = browser.new_context(viewport={"width": 1280, "height": 900}, http_credentials=auth)
        page = context.new_page()
        errors, failed, statuses = [], [], {}
        page.on("console", lambda m: m.type == "error" and errors.append(m.text))
        page.on("pageerror", lambda e: errors.append(str(e)))
        # A request that the page cancels, for example when the viewer
        # moves to the next photo before the last one loaded, is not a failure.
        page.on("requestfailed", lambda r: r.failure != "net::ERR_ABORTED" and failed.append(f"{r.url} {r.failure}"))
        page.on("response", lambda r: statuses.__setitem__(r.url, r.status))
        page.goto(HOME, wait_until="networkidle")

        # AT-39
        photos = photo_info(page)
        check("AT-39 the home page has 9 card photos", len(photos) == 9, str(len(photos)))
        for n, ph in enumerate(photos, 1):
            check(
                f"AT-39 photo {n} is a button that opens the viewer",
                ph["role"] == "button" and ph["tabindex"] == "0"
                and ph["label"].startswith("Open image viewer") and ph["alt"] in ph["label"],
                str(ph),
            )
            check(f"AT-39 photo {n} full-size address is the card photo address", ph["src"] == ph["dataSrc"], ph["src"])
            check(f"AT-39 photo {n} caption holds the card text", all(line in ph["caption"] for line in ph["lines"]), ph["caption"])
        videos = page.eval_on_selector_all(VIDEOS, "v => v.filter(i => i.hasAttribute('role') || i.hasAttribute('data-bas-lightbox-src')).length")
        check("AT-39 video thumbnails do not open the viewer", videos == 0, str(videos))

        # AT-41
        for name in LIGHTBOX_FILES:
            url = next((u for u in statuses if u.endswith(PLUGIN + name) or (PLUGIN + name + "?") in u), None)
            check(f"AT-41 {name} loads from the plugin folder", url is not None and statuses[url] == 200, str(url))
        home_versions = {u.split("?ver=")[-1] for u in statuses if PLUGIN in u and "?ver=" in u}
        home_modal = modal_markup(page) if page.query_selector(MODAL) else ""
        ref = context.new_page()
        ref_versions = set()
        ref.on("response", lambda r: PLUGIN in r.url and "?ver=" in r.url and ref_versions.add(r.url.split("?ver=")[-1]))
        ref.goto(ARTICLE, wait_until="networkidle")
        ref_modal = modal_markup(ref) if ref.query_selector(MODAL) else "missing"
        ref.close()
        check("AT-41 the home page modal equals the article modal", home_modal == ref_modal, "markup differs")
        check("AT-41 the home page loads the plugin version of the article page",
              len(home_versions) == 1 and home_versions == ref_versions, f"{home_versions} != {ref_versions}")

        # AT-40
        if len(photos) == 9 and page.query_selector(MODAL):
            first = page.locator(PHOTOS).first
            first.scroll_into_view_if_needed()
            first.click()
            s = shown(page)
            check("AT-40 a click opens the viewer on the photo", s is not None and s["src"] == photos[0]["dataSrc"], str(s))
            if s:
                check("AT-40 the caption holds the card text", all(line in s["caption"] for line in photos[0]["lines"]), s["caption"])
                check("AT-40 the original-image link opens the photo", s["original"] == photos[0]["dataSrc"], s["original"])
                check("AT-40 focus is on the close button", s["focus"] == "Close image viewer", str(s["focus"]))
                page.keyboard.press("ArrowRight")
                check("AT-40 the right arrow shows the second photo", shown(page)["src"] == photos[1]["dataSrc"])
                page.click("[data-bas-article-lightbox] [data-bas-public-gallery-prev]")
                page.click("[data-bas-article-lightbox] [data-bas-public-gallery-prev]")
                check("AT-40 previous on the first photo shows the last", shown(page)["src"] == photos[-1]["dataSrc"])
                page.click("[data-bas-article-lightbox] [data-bas-public-gallery-next]")
                check("AT-40 next on the last photo shows the first", shown(page)["src"] == photos[0]["dataSrc"])
                page.wait_for_function(
                    "() => { const i = document.querySelector('[data-bas-article-lightbox] [data-bas-public-gallery-modal-image]');"
                    " return i.complete && i.naturalWidth > 0; }"
                )
                for scheme in ("light", "dark"):
                    for width in (1280, 390):
                        page.emulate_media(color_scheme=scheme)
                        page.set_viewport_size({"width": width, "height": 900})
                        page.screenshot(path=str(OUT / f"home-lightbox-{scheme}-{width}.png"))
                page.set_viewport_size({"width": 1280, "height": 900})
                page.emulate_media(color_scheme="light")
                page.keyboard.press("Escape")
                focus_back = page.evaluate("() => document.activeElement === document.querySelector('img.bas-lazy-media[role=button]')")
                check("AT-40 Escape closes the viewer", shown(page) is None)
                check("AT-40 focus returns to the photo", focus_back)
                for key in ("Enter", " "):
                    first.focus()
                    page.keyboard.press(key)
                    check(f"AT-40 {'Space' if key == ' ' else key} on a focused photo opens the viewer", shown(page) is not None)
                    page.keyboard.press("Escape")
        else:
            check("AT-40 the viewer can be tested", False, "no photos or no modal")

        # AT-42
        load_all(page)
        with_lightbox = boxes(page)
        plain = browser.new_context(viewport={"width": 1280, "height": 900}, http_credentials=auth).new_page()
        plain.route(re.compile(re.escape(PLUGIN)), lambda route: route.abort())
        plain.goto(HOME, wait_until="networkidle")
        load_all(plain)
        check("AT-42 the photo boxes are the same without the lightbox files", boxes(plain) == with_lightbox,
              f"{with_lightbox} != {boxes(plain)}")
        dead = plain.eval_on_selector_all(PHOTOS, "imgs => imgs.filter(i => i.hasAttribute('role') || i.hasAttribute('tabindex') || i.hasAttribute('aria-label')).length")
        check("AT-42 without the lightbox files the photos are plain images", dead == 0, f"{dead} photos are buttons")
        check("AT-42 no request fails", not failed, "; ".join(failed))
        check("AT-42 the console has no errors", not errors, "; ".join(errors))
        browser.close()
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
