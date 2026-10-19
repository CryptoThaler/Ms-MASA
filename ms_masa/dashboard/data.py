"""
Data sources for the dashboard.

Both sources run markets through the same MarketAnalyzer and SignalEngine
the agent uses; they differ only in where markets and order books come from.
"""

from __future__ import annotations

import random
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Callable, Optional

from ms_masa.analysis.market_analyzer import MarketAnalyzer
from ms_masa.analysis.signals import SignalEngine
from ms_masa.api.data_pipe import DataPipeline
from ms_masa.models import Market, MarketSnapshot, OrderBook, OrderBookLevel

SORTS = ("volume", "liquidity", "certainty", "uncertainty")
TAGS = ("politics", "crypto", "sports", "science", "pop-culture")


class NotFound(Exception):
    pass


class UpstreamError(Exception):
    pass


class TTLCache:
    """Small thread-safe cache so repeated dashboard loads don't re-hit the API."""

    def __init__(self, ttl: float = 30.0, max_entries: int = 256):
        self._ttl = ttl
        self._max = max_entries
        self._data: dict[Any, tuple[float, Any]] = {}
        self._lock = threading.Lock()

    def get_or_compute(self, key: Any, fn: Callable[[], Any]) -> Any:
        now = time.monotonic()
        with self._lock:
            hit = self._data.get(key)
            if hit and now - hit[0] < self._ttl:
                return hit[1]
        value = fn()
        with self._lock:
            if len(self._data) >= self._max:
                self._data.pop(min(self._data, key=lambda k: self._data[k][0]))
            self._data[key] = (now, value)
        return value


class DashboardSource:
    """Shared dashboard logic; subclasses supply markets and order books."""

    mode = "base"

    def __init__(self, cache_ttl: float = 30.0):
        self.analyzer = MarketAnalyzer()
        self.engine = SignalEngine()
        self.cache = TTLCache(cache_ttl)

    # Subclass hooks
    def _list_markets(self, tag: Optional[str], limit: int) -> list[Market]:
        raise NotImplementedError

    def _get_market(self, market_id: str) -> Market:
        raise NotImplementedError

    def _get_book(self, token_id: str) -> Optional[OrderBook]:
        raise NotImplementedError

    # Public API
    def summarize(self, m: Market) -> dict:
        info = self.analyzer.characterize_market(m)
        info["end_date"] = m.end_date
        info["has_book"] = bool(m.yes_token)
        return info

    def markets(self, tag: Optional[str] = None, sort: str = "volume",
                limit: int = 25, query: str = "") -> list[dict]:
        def compute():
            ms = self._list_markets(tag, max(limit * 2, 50))
            if query:
                q = query.lower()
                ms = [m for m in ms if q in m.question.lower()]
            ms = self.analyzer.rank_markets(ms, by=sort)[:limit]
            return [self.summarize(m) for m in ms]
        return self.cache.get_or_compute(("markets", tag, sort, limit, query), compute)

    def _snapshot(self, m: Market) -> MarketSnapshot:
        book = None
        if m.yes_token:
            try:
                book = self._get_book(m.yes_token)
            except UpstreamError:
                book = None
        return MarketSnapshot(
            market=m,
            order_book=book,
            volume_24h=m.volume,
            liquidity_score=DataPipeline._compute_liquidity_score(book),
        )

    @staticmethod
    def _signal_dicts(signals) -> list[dict]:
        return [
            # Ask-heavy imbalance is reported as negative strength; the sign is already in the type.
            {"type": s.signal_type, "strength": round(min(abs(s.strength), 1.0), 4), "desc": s.description}
            for s in signals
        ]

    def market_detail(self, market_id: str) -> dict:
        def compute():
            m = self._get_market(market_id)
            snap = self._snapshot(m)
            analysis = self.analyzer.analyze_snapshot(snap)
            analysis["market"] = self.summarize(m)
            analysis["market"]["description"] = m.description
            analysis["signals"] = self._signal_dicts(self.engine.generate_signals(snap))
            book = snap.order_book
            analysis["levels"] = {
                "bids": sorted(([b.price, b.size] for b in book.bids), reverse=True) if book else [],
                "asks": sorted([a.price, a.size] for a in book.asks) if book else [],
            }
            return analysis
        return self.cache.get_or_compute(("detail", market_id), compute)

    def signals(self, limit: int = 25) -> list[dict]:
        def compute():
            ms = self._list_markets(None, limit)[:limit]
            with ThreadPoolExecutor(max_workers=8) as pool:
                snaps = list(pool.map(self._snapshot, ms))
            rows = []
            for snap in snaps:
                for sig in self._signal_dicts(self.engine.generate_signals(snap)):
                    rows.append({
                        "market_id": snap.market.id,
                        "question": snap.market.question,
                        "yes_price": snap.market.yes_price,
                        **sig,
                    })
            rows.sort(key=lambda r: -r["strength"])
            return rows
        return self.cache.get_or_compute(("signals", limit), compute)


class LiveSource(DashboardSource):
    """Live data from Polymarket's Gamma and CLOB APIs."""

    mode = "live"

    def __init__(self, cache_ttl: float = 30.0):
        super().__init__(cache_ttl)
        from ms_masa.config import MsMasaConfig
        self.pipeline = DataPipeline(MsMasaConfig.from_env())

    def _call(self, fn, *args, **kwargs):
        import httpx
        try:
            return fn(*args, **kwargs)
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                raise NotFound() from e
            raise UpstreamError(f"Polymarket API returned {e.response.status_code}") from e
        except httpx.HTTPError as e:
            raise UpstreamError("Polymarket API unreachable") from e

    def _list_markets(self, tag, limit):
        if tag:
            return self._call(self.pipeline.scan_markets_by_tag, tag, limit=limit)
        return self._call(self.pipeline.gamma.get_tradeable_markets, limit=limit)

    def _get_market(self, market_id):
        from ms_masa.api.gamma import GammaClient
        return GammaClient._parse_market(self._call(self.pipeline.gamma.get_market, market_id))

    def _get_book(self, token_id):
        try:
            return self._call(self.pipeline.clob.get_order_book, token_id)
        except NotFound:
            return None


SAMPLE_QUESTIONS = {
    "politics": [
        "Will the incumbent party win the next national election?",
        "Will the senate confirm the nominee before the recess?",
        "Will voter turnout exceed 60% in the general election?",
        "Will the trade bill pass the lower house this session?",
        "Will a third-party candidate poll above 10% nationally?",
        "Will the governor sign the budget by the deadline?",
        "Will the referendum on electoral reform pass?",
        "Will the coalition government survive a confidence vote?",
    ],
    "crypto": [
        "Will BTC close above $150k by year end?",
        "Will ETH flip its previous all-time high this quarter?",
        "Will a spot SOL ETF be approved this year?",
        "Will total stablecoin supply exceed $400B?",
        "Will a top-10 exchange halt withdrawals this month?",
        "Will BTC dominance stay above 55% through the quarter?",
        "Will a major L2 launch a token before July?",
        "Will ETH gas average under 5 gwei next month?",
    ],
    "sports": [
        "Will the defending champions reach the final?",
        "Will the league MVP be a first-time winner?",
        "Will any team finish the regular season unbeaten?",
        "Will the home side win the derby this weekend?",
        "Will the world record in the 100m be broken this year?",
        "Will the transfer fee record be broken this window?",
        "Will the underdog win the title fight?",
        "Will the season opener draw over 20M viewers?",
    ],
    "science": [
        "Will a crewed lunar landing happen before 2028?",
        "Will a room-temperature superconductor be replicated?",
        "Will the next Starship flight reach orbit?",
        "Will global average temperature set a new annual record?",
        "Will a new frontier AI model top the main leaderboard?",
        "Will the fusion facility report net energy gain again?",
        "Will a new interstellar object be detected this year?",
        "Will the gene therapy trial meet its primary endpoint?",
    ],
    "pop-culture": [
        "Will the summer blockbuster gross over $1B worldwide?",
        "Will the debut album top the charts in its first week?",
        "Will the streaming finale break viewership records?",
        "Will the festival headliner be announced before March?",
        "Will the reunion tour add a second leg?",
        "Will the best picture winner be a sequel?",
        "Will the viral game sell 10M copies this year?",
        "Will the award show ratings rise year over year?",
    ],
}


class SampleSource(DashboardSource):
    """Deterministic, clearly fictional sample data for offline demos and UI work."""

    mode = "sample"

    def __init__(self, seed: int = 7, cache_ttl: float = 30.0):
        super().__init__(cache_ttl)
        rng = random.Random(seed)
        self._markets: dict[str, Market] = {}
        self._books: dict[str, OrderBook] = {}
        n = 0
        for tag, questions in SAMPLE_QUESTIONS.items():
            for q in questions:
                n += 1
                mid = str(500000 + n)
                yes = rng.choice([
                    rng.uniform(0.02, 0.98),
                    rng.uniform(0.46, 0.54),
                    rng.choice([rng.uniform(0.005, 0.04), rng.uniform(0.96, 0.995)]),
                ])
                yes = round(yes, 3)
                token = f"sample-{mid}-yes"
                self._markets[mid] = Market(
                    id=mid,
                    question=q,
                    description="Fictional sample market for the dashboard demo. Resolves YES if the "
                                "event in the question happens before the end date; otherwise NO.",
                    slug=f"sample-{mid}",
                    outcomes=["Yes", "No"],
                    outcome_prices=[yes, round(1 - yes, 3)],
                    clob_token_ids=[token, f"sample-{mid}-no"],
                    volume=round(rng.lognormvariate(12, 1.4), 2),
                    liquidity=round(rng.lognormvariate(9.5, 1.2), 2),
                    end_date=f"2027-{rng.randint(1, 12):02d}-{rng.randint(1, 28):02d}T00:00:00Z",
                    category=tag,
                    tags=[tag],
                )
                self._books[token] = self._make_book(rng, yes)

    @staticmethod
    def _make_book(rng: random.Random, mid: float) -> OrderBook:
        half_spread = rng.choice([0.005, 0.01, 0.01, 0.02, 0.04, 0.08])
        skew = rng.uniform(0.4, 2.2)
        scale = rng.choice([150, 600, 2500])
        bids, asks = [], []
        for i in range(12):
            bp = round(mid - half_spread - i * 0.01, 3)
            ap = round(mid + half_spread + i * 0.01, 3)
            if 0.001 <= bp < 1:
                bids.append(OrderBookLevel(bp, round(rng.uniform(0.3, 1.6) * scale * skew, 2)))
            if 0 < ap <= 0.999:
                asks.append(OrderBookLevel(ap, round(rng.uniform(0.3, 1.6) * scale / skew, 2)))
        return OrderBook(bids=bids, asks=asks, tick_size="0.001")

    def _list_markets(self, tag, limit):
        ms = [m for m in self._markets.values() if not tag or tag in m.tags]
        return ms[:limit]

    def _get_market(self, market_id):
        try:
            return self._markets[market_id]
        except KeyError:
            raise NotFound() from None

    def _get_book(self, token_id):
        return self._books.get(token_id)
