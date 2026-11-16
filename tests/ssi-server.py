"""Serve a folder on 127.0.0.1 and run the SSI directives of the static pages.

The live server runs server-side includes in .html and .htm files (ST-88 and
SA-36 in bas-org-in/bas-site-ops). This preview server runs the directives
that the pages use: set var, include virtual, and if expr="$VAR = value"
with endif. It runs no programs.

Usage:
  python3 -I tests/ssi-server.py ROOT [PORT]
"""

import http.server
import re
import sys
from functools import partial
from io import BytesIO
from pathlib import Path

DIRECTIVE = re.compile(r"<!--#(\w+)((?:\s+\w+=\"[^\"]*\")*)\s*-->")
ATTR = re.compile(r'(\w+)="([^"]*)"')
CONDITION = re.compile(r"^\$(\w+) = (\w+)$")


def render(text: str, root: Path, env: dict[str, str], depth: int = 0) -> str:
    """Return text with its SSI directives run."""
    out: list[str] = []
    showing = [True]
    pos = 0
    for match in DIRECTIVE.finditer(text):
        if all(showing):
            out.append(text[pos : match.start()])
        pos = match.end()
        name, attrs = match.group(1), dict(ATTR.findall(match.group(2)))
        if name == "if":
            cond = CONDITION.match(attrs.get("expr", ""))
            showing.append(bool(cond) and env.get(cond.group(1)) == cond.group(2))
        elif name == "endif" and len(showing) > 1:
            showing.pop()
        elif not all(showing):
            continue
        elif name == "set":
            env[attrs["var"]] = attrs["value"]
        elif name == "include" and depth < 5:
            path = (root / attrs["virtual"].lstrip("/")).resolve()
            if root in path.parents and path.is_file():
                out.append(render(path.read_text(encoding="utf-8"), root, env, depth + 1))
            else:
                out.append("[an error occurred while processing this directive]")
    if all(showing):
        out.append(text[pos:])
    return "".join(out)


class Handler(http.server.SimpleHTTPRequestHandler):
    def send_head(self):
        path = Path(self.translate_path(self.path))
        if path.is_dir():
            path = path / "index.html"
        if path.suffix not in {".html", ".htm"} or not path.is_file():
            return super().send_head()
        root = Path(self.directory).resolve()
        text = path.read_bytes().decode("utf-8", errors="surrogateescape")
        body = render(text, root, {}).encode("utf-8", errors="surrogateescape")
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        return BytesIO(body)


def main() -> int:
    if len(sys.argv) not in (2, 3):
        print(__doc__, file=sys.stderr)
        return 2
    root = Path(sys.argv[1]).resolve()
    port = int(sys.argv[2]) if len(sys.argv) == 3 else 8765
    handler = partial(Handler, directory=str(root))
    with http.server.ThreadingHTTPServer(("127.0.0.1", port), handler) as server:
        print(f"Serving {root} on http://127.0.0.1:{port}/")
        server.serve_forever()
    return 0


if __name__ == "__main__":
    sys.exit(main())
