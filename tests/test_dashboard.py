"""Tests for the web dashboard API and server."""

import json
import os
import socket
import threading
import unittest
import urllib.error
import urllib.request
from unittest import mock

from ms_masa import security
from ms_masa.dashboard.data import SampleSource, UpstreamError
from ms_masa.dashboard.server import BadRequest, create_server, handle_api

TOKEN = "d" * 32


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


class SampleSourceTests(unittest.TestCase):
    source = SampleSource()

    def test_markets_filter_sort_and_search(self):
        crypto = self.source.markets(tag="crypto", limit=100)
        self.assertTrue(crypto and all("crypto" in m["tags"] for m in crypto))
        vols = [m["volume"] for m in self.source.markets(sort="volume", limit=100)]
        self.assertEqual(vols, sorted(vols, reverse=True))
        self.assertTrue(all("btc" in m["question"].lower() for m in self.source.markets(query="BTC")))

    def test_detail_has_levels_and_signals(self):
        mid = self.source.markets(limit=1)[0]["id"]
        d = self.source.market_detail(mid)
        self.assertTrue(d["levels"]["bids"] and d["levels"]["asks"])
        self.assertGreater(d["levels"]["bids"][0][0], d["levels"]["bids"][-1][0])
        self.assertLess(d["levels"]["asks"][0][0], d["levels"]["asks"][-1][0])
        self.assertIn("spread", d["order_book"])

    def test_signal_strengths_are_unit_interval(self):
        rows = self.source.signals(limit=60)
        self.assertTrue(any(r["type"] == "imbalance_ask_heavy" for r in rows))
        self.assertTrue(all(0 <= r["strength"] <= 1 for r in rows))
        self.assertTrue(all(r["strength"] > 0 for r in rows if r["type"] == "imbalance_ask_heavy"))


class HandleApiTests(unittest.TestCase):
    source = SampleSource()

    def test_rejects_bad_parameters(self):
        for path, params in [
            ("/api/markets", {"tag": ["nope"]}),
            ("/api/markets", {"sort": ["__class__"]}),
            ("/api/markets", {"q": ["x" * 101]}),
            ("/api/markets", {"limit": ["ten"]}),
            ("/api/markets/../events", {}),
            ("/api/explain/../config", {}),
        ]:
            with self.subTest(path=path, params=params), self.assertRaises(BadRequest):
                handle_api(self.source, path, params, False)

    def test_unknown_topic_is_not_found(self):
        from ms_masa.dashboard.data import NotFound
        with self.assertRaises(NotFound):
            handle_api(self.source, "/api/explain/__init__", {}, False)

    def test_limit_is_clamped(self):
        _, rows = handle_api(self.source, "/api/markets", {"limit": ["100000"]}, False)
        self.assertLessEqual(len(rows), 100)


class DashboardServerTests(unittest.TestCase):
    def _start(self, token=None, source=None):
        port = _free_port()
        server = create_server(source or SampleSource(), "127.0.0.1", port, token)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        self.addCleanup(server.server_close)
        self.addCleanup(server.shutdown)
        return port

    def _get(self, port, path, headers=None):
        req = urllib.request.Request(f"http://127.0.0.1:{port}{path}", headers=headers or {})
        try:
            with urllib.request.urlopen(req, timeout=5) as r:
                return r.status, dict(r.headers), r.read()
        except urllib.error.HTTPError as e:
            return e.code, dict(e.headers), e.read()

    def test_static_page_and_security_headers(self):
        port = self._start()
        status, headers, body = self._get(port, "/")
        self.assertEqual(status, 200)
        self.assertIn(b"app.js", body)
        self.assertIn("frame-ancestors 'none'", headers["Content-Security-Policy"])
        self.assertEqual(headers["X-Content-Type-Options"], "nosniff")
        self.assertEqual(self._get(port, "/app.js")[0], 200)
        self.assertEqual(self._get(port, "/../setup.py")[0], 404)

    def test_rejects_foreign_host_without_token(self):
        port = self._start()
        self.assertEqual(self._get(port, "/api/status", {"Host": f"attacker.example:{port}"})[0], 421)
        self.assertEqual(self._get(port, "/api/status")[0], 200)

    def test_token_required_for_api_not_static(self):
        port = self._start(token=TOKEN)
        self.assertEqual(self._get(port, "/")[0], 200)
        self.assertEqual(self._get(port, "/api/status")[0], 401)
        status, _, body = self._get(port, "/api/status", {"Authorization": f"Bearer {TOKEN}"})
        self.assertEqual(status, 200)
        self.assertTrue(json.loads(body)["auth_required"])

    def test_upstream_and_internal_errors(self):
        source = SampleSource()
        port = self._start(source=source)
        with mock.patch.object(source, "markets", side_effect=UpstreamError("Polymarket API unreachable")):
            self.assertEqual(self._get(port, "/api/markets")[0], 502)
        with mock.patch.object(source, "signals", side_effect=RuntimeError("/srv/secret")), \
                self.assertLogs("ms_masa.security", level="ERROR"):
            status, _, body = self._get(port, "/api/signals")
        self.assertEqual(status, 500)
        self.assertNotIn(b"/srv/secret", body)
        self.assertEqual(self._get(port, "/api/markets/999")[0], 404)

    def test_public_bind_requires_token(self):
        with mock.patch.dict(os.environ, {}, clear=False):
            os.environ.pop(security.AUTH_TOKEN_ENV, None)
            with self.assertRaises(SystemExit):
                create_server(SampleSource(), "0.0.0.0", _free_port(), None)


if __name__ == "__main__":
    unittest.main()


class StaticExportTests(unittest.TestCase):
    def test_snapshot_covers_every_view(self):
        from ms_masa.dashboard.server import build_snapshot
        snap = build_snapshot(SampleSource(), limit=10)
        self.assertEqual(len(snap["markets"]), 10)
        self.assertEqual(set(snap["details"]), {m["id"] for m in snap["markets"]})
        self.assertEqual(set(snap["explain"]), set(snap["topics"]))
        self.assertEqual(snap["status"]["mode"], "sample")

    def test_market_text_cannot_break_out_of_script(self):
        from ms_masa.dashboard.server import build_snapshot, render_static
        source = SampleSource()
        evil = "</script><script>alert(1)</script>"
        next(iter(source._markets.values())).question = evil
        for standalone in (True, False):
            html = render_static(build_snapshot(source, limit=40), standalone=standalone)
            self.assertNotIn(evil, html)
            self.assertEqual(html.count("</script>"), 2)
        self.assertTrue(html.startswith("<title>"))
