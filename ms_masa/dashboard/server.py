"""
Ms-MASA Web Dashboard server (stdlib only).

Run:
    python -m ms_masa.dashboard                   # live data on http://127.0.0.1:8050
    python -m ms_masa.dashboard --sample-data     # offline, clearly labeled sample data
    MS_MASA_AUTH_TOKEN=... python -m ms_masa.dashboard --host 0.0.0.0
                                                  # remote: API requires a bearer token
"""

from __future__ import annotations

import json
import logging
import re
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from importlib import resources
from urllib.parse import parse_qs, urlparse

from ms_masa import __version__
from ms_masa.dashboard.data import SORTS, TAGS, DashboardSource, LiveSource, NotFound, SampleSource, UpstreamError
from ms_masa.security import (
    DEFAULT_HOST, bearer_matches, enforce_bind_policy, is_loopback, load_auth_token, public_error,
)

logger = logging.getLogger("ms_masa.dashboard")

DEFAULT_PORT = 8050
MARKET_ID_RE = re.compile(r"^[A-Za-z0-9-]{1,80}$")
TOPIC_RE = re.compile(r"^[a-z_]{1,40}$")
MAX_QUERY_LENGTH = 100

STATIC_FILES = {
    "/": ("index.html", "text/html; charset=utf-8"),
    "/app.js": ("app.js", "text/javascript; charset=utf-8"),
    "/app.css": ("app.css", "text/css; charset=utf-8"),
}

SECURITY_HEADERS = {
    "Content-Security-Policy": (
        "default-src 'self'; script-src 'self'; style-src 'self' https://fonts.googleapis.com; "
        "font-src https://fonts.gstatic.com; img-src 'self' data:; "
        "connect-src 'self'; base-uri 'none'; form-action 'none'; frame-ancestors 'none'"
    ),
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "no-referrer",
    "Cache-Control": "no-store",
}


class BadRequest(Exception):
    pass


def _load_static() -> dict[str, tuple[bytes, str]]:
    pkg = resources.files("ms_masa.dashboard") / "static"
    return {route: ((pkg / name).read_bytes(), ctype) for route, (name, ctype) in STATIC_FILES.items()}


def _int_param(params: dict, name: str, default: int, lo: int, hi: int) -> int:
    raw = params.get(name, [str(default)])[0]
    try:
        return max(lo, min(int(raw), hi))
    except ValueError:
        raise BadRequest(f"{name} must be an integer") from None


def handle_api(source: DashboardSource, path: str, params: dict, auth_required: bool) -> tuple[int, object]:
    """Route an API request. Returns (status, json-able body)."""
    if path == "/api/status":
        return 200, {"version": __version__, "mode": source.mode, "auth_required": auth_required,
                     "tags": list(TAGS), "sorts": list(SORTS)}

    if path == "/api/markets":
        tag = params.get("tag", [""])[0] or None
        if tag is not None and tag not in TAGS:
            raise BadRequest("unknown tag")
        sort = params.get("sort", ["volume"])[0]
        if sort not in SORTS:
            raise BadRequest("unknown sort")
        query = params.get("q", [""])[0].strip()
        if len(query) > MAX_QUERY_LENGTH:
            raise BadRequest("query too long")
        limit = _int_param(params, "limit", 25, 1, 100)
        return 200, source.markets(tag=tag, sort=sort, limit=limit, query=query)

    if path.startswith("/api/markets/"):
        market_id = path[len("/api/markets/"):]
        if not MARKET_ID_RE.match(market_id):
            raise BadRequest("invalid market id")
        return 200, source.market_detail(market_id)

    if path == "/api/signals":
        return 200, source.signals(limit=_int_param(params, "limit", 25, 1, 60))

    if path == "/api/topics":
        from ms_masa.knowledge.polymarket_kb import PolymarketKB
        return 200, PolymarketKB.topics()

    if path.startswith("/api/explain/"):
        topic = path[len("/api/explain/"):]
        if not TOPIC_RE.match(topic):
            raise BadRequest("invalid topic")
        from ms_masa.knowledge.polymarket_kb import PolymarketKB
        result = PolymarketKB.lookup(topic)
        if result is None:
            raise NotFound()
        return 200, result

    raise NotFound()


def make_handler(source: DashboardSource, token: str | None, host: str, port: int):
    static = _load_static()
    loopback = is_loopback(host)
    allowed_hosts = {f"{h}:{port}" for h in ("127.0.0.1", "localhost", "[::1]")}

    class DashboardHandler(BaseHTTPRequestHandler):
        timeout = 30
        server_version = "ms-masa-dashboard"
        sys_version = ""

        def _send(self, status: int, body: bytes, ctype: str, extra: dict | None = None):
            self.send_response(status)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body)))
            for k, v in {**SECURITY_HEADERS, **(extra or {})}.items():
                self.send_header(k, v)
            self.end_headers()
            self.wfile.write(body)

        def _json(self, status: int, payload: object, extra: dict | None = None):
            self._send(status, json.dumps(payload, default=str).encode(), "application/json", extra)

        def do_GET(self):
            # Unauthenticated loopback mode: reject foreign Host headers (DNS rebinding).
            if loopback and token is None and self.headers.get("Host") not in allowed_hosts:
                self._json(421, {"error": "misdirected request"})
                return

            url = urlparse(self.path)
            if url.path in static:
                body, ctype = static[url.path]
                self._send(200, body, ctype)
                return
            if not url.path.startswith("/api/"):
                self._json(404, {"error": "not found"})
                return
            if not bearer_matches(self.headers.get("Authorization"), token):
                self._json(401, {"error": "unauthorized"}, {"WWW-Authenticate": "Bearer"})
                return

            try:
                status, payload = handle_api(source, url.path, parse_qs(url.query), token is not None)
            except BadRequest as e:
                status, payload = 400, {"error": str(e)}
            except NotFound:
                status, payload = 404, {"error": "not found"}
            except UpstreamError as e:
                status, payload = 502, {"error": str(e)}
            except Exception as e:
                status, payload = 500, {"error": public_error(e, f"dashboard {url.path}")}
            self._json(status, payload)

        def log_message(self, format, *args):
            logger.debug("%s - %s", self.address_string(), format % args)

    return DashboardHandler


def create_server(source: DashboardSource, host: str = DEFAULT_HOST, port: int = DEFAULT_PORT,
                  token: str | None = None) -> ThreadingHTTPServer:
    enforce_bind_policy(host, token)
    ThreadingHTTPServer.daemon_threads = True
    return ThreadingHTTPServer((host, port), make_handler(source, token, host, port))


def build_snapshot(source: DashboardSource, limit: int = 60) -> dict:
    """Capture everything the UI needs so it can run without a server."""
    from concurrent.futures import ThreadPoolExecutor
    from datetime import datetime, timezone
    from ms_masa.knowledge.polymarket_kb import PolymarketKB

    markets = source.markets(sort="volume", limit=limit)
    with ThreadPoolExecutor(max_workers=8) as pool:
        details = dict(zip((m["id"] for m in markets), pool.map(lambda m: source.market_detail(m["id"]), markets)))
    topics = PolymarketKB.topics()
    return {
        "status": {
            "version": __version__,
            "mode": "sample" if source.mode == "sample" else "snapshot",
            "snapshot_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "auth_required": False,
            "tags": list(TAGS),
            "sorts": list(SORTS),
        },
        "markets": markets,
        "details": details,
        "signals": source.signals(limit=min(limit, 60)),
        "topics": topics,
        "explain": {t: PolymarketKB.lookup(t) for t in topics},
    }


def render_static(snapshot: dict, standalone: bool = True) -> str:
    """Inline the dashboard and a snapshot into one HTML document (or a body fragment)."""
    pkg = resources.files("ms_masa.dashboard") / "static"
    page = (pkg / "index.html").read_text()
    css = (pkg / "app.css").read_text()
    js = (pkg / "app.js").read_text()
    body = page[page.index("<body>") + len("<body>"):page.index("</body>")]
    fonts = re.findall(r'\s*<link rel="(?:preconnect|stylesheet)" href="https://fonts[^>]*>', page)
    # Escape "<" so no market text can close the script element early.
    data = json.dumps(snapshot, default=str).replace("<", "\\u003c")
    head = (
        "<title>Ms-MASA Dashboard</title>\n"
        '<meta name="claude:viewport-fit-sides" content="cover">\n'
        + "".join(f.strip() + "\n" for f in fonts)
        + f"<style>\n{css}\n</style>\n"
    )
    safe_js = js.replace("</script", "<\\/script")
    scripts = (
        f'<script type="application/json" id="ms-masa-snapshot">{data}</script>\n'
        f"<script>\n{safe_js}\n</script>\n"
    )
    if not standalone:
        return head + body + scripts
    return (
        '<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
        + head + "</head>\n<body>" + body + scripts + "</body>\n</html>\n"
    )


def main(argv: list[str] | None = None):
    import argparse
    from ms_masa.security import AUTH_TOKEN_ENV

    logging.basicConfig(level=logging.INFO, stream=sys.stderr)
    parser = argparse.ArgumentParser(
        prog="python -m ms_masa.dashboard",
        description="Ms-MASA web dashboard",
        epilog=f"Binding a non-loopback host requires {AUTH_TOKEN_ENV} to be set.",
    )
    parser.add_argument("--host", default=DEFAULT_HOST, help=f"Bind address (default: {DEFAULT_HOST})")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help=f"Port (default: {DEFAULT_PORT})")
    parser.add_argument("--sample-data", action="store_true",
                        help="Serve built-in fictional sample markets instead of live Polymarket data")
    parser.add_argument("--open", action="store_true", help="Open the dashboard in a browser")
    parser.add_argument("--export", metavar="FILE",
                        help="Write a self-contained HTML snapshot (for static hosting) and exit")
    args = parser.parse_args(argv)

    source = SampleSource() if args.sample_data else LiveSource()
    if args.export:
        from pathlib import Path
        try:
            html = render_static(build_snapshot(source))
        except UpstreamError as e:
            raise SystemExit(f"Export failed: {e}. Use --sample-data to export offline.")
        Path(args.export).write_text(html, encoding="utf-8")
        print(f"Wrote {args.export} ({len(html) // 1024} KB, {source.mode} data)", file=sys.stderr)
        return

    token = load_auth_token()
    server = create_server(source, args.host, args.port, token)
    shown = "127.0.0.1" if args.host in ("0.0.0.0", "::") else args.host
    url = f"http://{shown}:{args.port}/"
    print(f"Ms-MASA dashboard ({source.mode} data) at {url}  "
          f"[auth: {'bearer token' if token else 'none, loopback only'}]", file=sys.stderr)
    if args.open:
        import webbrowser
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
