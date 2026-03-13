"""Tests for ms_masa.builder."""

import tempfile
from pathlib import Path

from ms_masa.builder.agent_builder import AgentBuilder
from ms_masa.builder.templates import AgentTemplates


# ── Template Tests ────────────────────────────────────────────────────


def test_list_templates():
    templates = AgentTemplates.list_templates()
    assert "market_monitor" in templates
    assert "signal_scanner" in templates
    assert "data_collector" in templates
    assert "llm_analyst" in templates
    assert "autonomous_loop" in templates


def test_market_monitor_template():
    code = AgentTemplates.market_monitor()
    assert "class MarketMonitor" in code
    assert "from ms_masa import MsMasaAgent" in code
    assert "def run(self)" in code


def test_signal_scanner_template():
    code = AgentTemplates.signal_scanner()
    assert "class SignalScanner" in code
    assert "def full_scan" in code


def test_data_collector_template():
    code = AgentTemplates.data_collector()
    assert "class DataCollector" in code
    assert "def snapshot_all_markets" in code


def test_llm_analyst_template():
    code = AgentTemplates.llm_analyst()
    assert "class LLMAnalyst" in code
    assert "def analyze" in code


# ── Builder Tests ─────────────────────────────────────────────────────


def test_builder_list_templates():
    builder = AgentBuilder()
    templates = builder.list_templates()
    assert len(templates) >= 4


def test_builder_generate_no_write():
    builder = AgentBuilder()
    code = builder.generate("market_monitor", write=False)
    assert "class MarketMonitor" in code


def test_builder_generate_all_templates():
    builder = AgentBuilder()
    for name in ["market_monitor", "signal_scanner", "data_collector", "llm_analyst", "autonomous_loop"]:
        code = builder.generate(name, write=False)
        assert len(code) > 100, f"Template {name} too short"


def test_autonomous_loop_template():
    code = AgentTemplates.autonomous_loop()
    assert "class AutonomousLoop" in code
    assert "LOOP FOREVER" in code
    assert "def scan" in code
    assert "def evaluate" in code
    assert "def decide" in code
    assert "def record" in code


def test_builder_generate_invalid_template():
    builder = AgentBuilder()
    try:
        builder.generate("nonexistent", write=False)
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "Unknown template" in str(e)


def test_builder_generate_writes_file():
    with tempfile.TemporaryDirectory() as tmpdir:
        builder = AgentBuilder(output_dir=tmpdir)
        code = builder.generate("market_monitor", write=True)
        path = Path(tmpdir) / "market_monitor_agent.py"
        assert path.exists()
        assert path.read_text() == code


def test_builder_scaffold():
    builder = AgentBuilder()
    files = builder.scaffold_project("test_agent")
    assert "test_agent/agent.py" in files
    assert "test_agent/config.json" in files
    assert "test_agent/.env.example" in files
    assert "test_agent/requirements.txt" in files


def test_builder_scaffold_class_name():
    assert AgentBuilder._to_class_name("my_cool_agent") == "MyCoolAgent"
    assert AgentBuilder._to_class_name("test-agent") == "TestAgent"


def test_builder_list_agent_patterns():
    builder = AgentBuilder()
    patterns = builder.list_agent_patterns()
    assert "read_only_agent" in patterns
    assert "analytical_agent" in patterns
