"""
Ms-MASA: Polymarket Agent Specialist
=====================================
A low-token, high-performance agent framework for building
autonomous systems on Polymarket's prediction market platform.

NOT for financial advice or trading. Focused on agent architecture,
API integration, and understanding the Polymarket ecosystem.
"""

__version__ = "0.1.0"
__codename__ = "MS-MASA"

from ms_masa.agent import MsMasaAgent
from ms_masa.config import MsMasaConfig

__all__ = ["MsMasaAgent", "MsMasaConfig", "__version__"]


def mcp_tools():
    """Shortcut: get MCP tool definitions for Ms-MASA."""
    from ms_masa.mcp_server import TOOLS
    return TOOLS


def skill_manifest():
    """Shortcut: get the agent skill manifest."""
    from ms_masa.skill_manifest import MANIFEST
    return MANIFEST
