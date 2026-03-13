"""Tests for ms_masa.prompts."""

from ms_masa.prompts import Prompts


def test_available_modes():
    modes = Prompts.available_modes()
    assert "specialist" in modes
    assert "analyst" in modes
    assert "forecaster" in modes
    assert "architect" in modes
    assert "filter" in modes


def test_for_mode_specialist():
    prompt = Prompts.for_mode("specialist")
    assert "Ms-MASA" in prompt
    assert "Polymarket" in prompt


def test_for_mode_analyst():
    prompt = Prompts.for_mode("analyst")
    assert "analyst" in prompt.lower() or "liquidity" in prompt.lower()


def test_for_mode_forecaster():
    prompt = Prompts.for_mode("forecaster")
    assert "probability" in prompt.lower()


def test_for_mode_architect():
    prompt = Prompts.for_mode("architect")
    assert "architecture" in prompt.lower() or "agent" in prompt.lower()


def test_for_mode_filter():
    prompt = Prompts.for_mode("filter")
    assert "event" in prompt.lower() or "market" in prompt.lower()


def test_for_mode_unknown_falls_back():
    prompt = Prompts.for_mode("nonexistent")
    assert prompt == Prompts.SPECIALIST


def test_all_prompts_nonempty():
    for mode in Prompts.available_modes():
        prompt = Prompts.for_mode(mode)
        assert len(prompt) > 50, f"Prompt for {mode} too short"
