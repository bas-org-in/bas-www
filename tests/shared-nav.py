"""Check that the static pages take the navigation bar from one file.

It checks ST-88 of docs/style-system.md in bas-org-in/bas-site-ops
(acceptance test AT-61):

- public/includes/global-nav.html has the links of ST-78, in order, and
  marks the link of each section with aria-current="page".
- Every .html and .htm page under public/ (except includes/ and the
  vendor folders) has one pair of BAS_GLOBAL_NAV markers, and between
  them only the two SSI directives, with the section of its folder.
- No page has a copy of the bar's markup.

Usage:
  python3 -I tests/shared-nav.py public
"""

import re
import sys
from pathlib import Path

NAV_FILE = Path("includes/global-nav.html")
SKIP_DIRS = {"includes", "bootstrap", "font-awesome-4.7.0", "wp", "gallery"}
SECTIONS = ["home", "events", "tools", "policy", "historic", "pages", "gallery", "blogs"]
LINKS = [
    ("/", "Home"),
    ("/events/", "Events"),
    ("/tools/", "Tools"),
    ("/policy/", "Policy"),
    ("/historic/", "Historic"),
    ("/pages/", "Pages"),
    ("/gallery/", "Gallery"),
    ("/blogs/", "Blogs"),
]
BLOCK = re.compile(r"<!-- BAS_GLOBAL_NAV_START -->(.*?)<!-- BAS_GLOBAL_NAV_END -->", re.S)
DIRECTIVES = re.compile(
    r'\s*<!--#set var="BAS_NAV_CURRENT" value="([a-z]+)" -->'
    r'\s*<!--#include virtual="/includes/global-nav\.html" -->\s*'
)


def section_of(rel: Path) -> str:
    """Return the section of a page: its first folder, or home at the root."""
    return rel.parts[0] if len(rel.parts) > 1 else "home"


def check_nav_file(root: Path) -> list[str]:
    path = root / NAV_FILE
    if not path.is_file():
        return [f"{NAV_FILE}: missing"]
    text = path.read_text(encoding="utf-8")
    errors = []
    found = re.findall(r'<a href="([^"]*)"((?:<!--#if .*?<!--#endif -->)?)>([^<]*)</a>', text)
    found = [f for f in found if f[2] != "Bangalore Astronomical Society"]
    if [(href, label) for href, _, label in found] != LINKS:
        errors.append(f"{NAV_FILE}: links are {found}, expected {LINKS}")
    for (_, attrs, label), section in zip(found, SECTIONS, strict=False):
        want = f'<!--#if expr="$BAS_NAV_CURRENT = {section}" --> aria-current="page"<!--#endif -->'
        if attrs != want:
            errors.append(f"{NAV_FILE}: link {label} does not mark section {section!r}")
    if "<!--#exec" in text:
        errors.append(f"{NAV_FILE}: has an exec directive")
    return errors


def check_pages(root: Path) -> tuple[int, list[str]]:
    errors = []
    pages = sorted(
        p for p in root.rglob("*") if p.suffix in {".html", ".htm"} and p.is_file()
        and not (set(p.relative_to(root).parts[:-1]) & SKIP_DIRS)
    )
    for page in pages:
        rel = page.relative_to(root)
        text = page.read_text(encoding="utf-8", errors="replace")
        blocks = BLOCK.findall(text)
        if len(blocks) != 1:
            errors.append(f"{rel}: has {len(blocks)} navigation marker pairs, expected 1")
            continue
        match = DIRECTIVES.fullmatch(blocks[0])
        if not match:
            errors.append(f"{rel}: other markup between the navigation markers")
        elif match.group(1) != section_of(rel):
            errors.append(f"{rel}: section {match.group(1)!r}, expected {section_of(rel)!r}")
        if "bas-site-nav" in BLOCK.sub("", text):
            errors.append(f"{rel}: has a copy of the navigation bar markup")
    return len(pages), errors


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__, file=sys.stderr)
        return 2
    root = Path(sys.argv[1])
    errors = check_nav_file(root)
    count, page_errors = check_pages(root)
    errors += page_errors
    for error in errors[:50]:
        print(error)
    if len(errors) > 50:
        print(f"... and {len(errors) - 50} more")
    print(f"{count} pages checked, {len(errors)} problems")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
