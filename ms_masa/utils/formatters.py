"""
Output formatters for Ms-MASA agent.

Provides compact, token-efficient formatting for market data,
analysis results, and agent outputs.
"""

from __future__ import annotations

import json
from typing import Any


class Formatter:
    """Compact output formatters optimized for low token usage."""

    @staticmethod
    def compact_market(market: dict) -> str:
        """One-line market summary."""
        q = market.get("question", "?")[:60]
        yp = market.get("yes_price", "?")
        vol = market.get("volume", 0)
        liq = market.get("liquidity", 0)
        return f"{q} | Y:{yp} | V:{vol:.0f} L:{liq:.0f}"

    @staticmethod
    def compact_markets(markets: list[dict]) -> str:
        """Compact multi-line market list."""
        lines = [Formatter.compact_market(m) for m in markets]
        return "\n".join(lines)

    @staticmethod
    def compact_book(book_analysis: dict) -> str:
        """Compact order book summary."""
        if book_analysis.get("status") == "empty":
            return "EMPTY BOOK"
        return (
            f"Bid:{book_analysis.get('best_bid',0):.4f} "
            f"Ask:{book_analysis.get('best_ask',0):.4f} "
            f"Spread:{book_analysis.get('spread',0):.4f} "
            f"Mid:{book_analysis.get('midpoint',0):.4f} "
            f"Depth B:{book_analysis.get('bid_depth',0):.0f} "
            f"A:{book_analysis.get('ask_depth',0):.0f} "
            f"Imbal:{book_analysis.get('imbalance',0):+.4f}"
        )

    @staticmethod
    def compact_signals(signals: list[dict]) -> str:
        """Compact signal list."""
        if not signals:
            return "No signals"
        lines = []
        for s in signals:
            lines.append(f"  [{s['type']}] str:{s['strength']:.2f} {s['desc']}")
        return "\n".join(lines)

    @staticmethod
    def compact_json(data: Any) -> str:
        """Minimal JSON output."""
        return json.dumps(data, separators=(",", ":"), default=str)

    @staticmethod
    def table(rows: list[dict], columns: list[str]) -> str:
        """Simple text table from list of dicts."""
        if not rows:
            return "(empty)"

        # Calculate widths
        widths = {c: len(c) for c in columns}
        for row in rows:
            for c in columns:
                val = str(row.get(c, ""))
                widths[c] = max(widths[c], len(val))

        # Header
        header = " | ".join(c.ljust(widths[c]) for c in columns)
        separator = "-+-".join("-" * widths[c] for c in columns)
        lines = [header, separator]

        # Rows
        for row in rows:
            line = " | ".join(str(row.get(c, "")).ljust(widths[c]) for c in columns)
            lines.append(line)

        return "\n".join(lines)
