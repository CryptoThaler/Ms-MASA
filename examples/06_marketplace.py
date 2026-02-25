"""
Example 6: Marketplace Integration

Demonstrates three paths for trading Ms-MASA skills as value:
1. On-chain registry (OLAS/Autonolas)
2. Agent marketplace (A2A discovery + metered billing)
3. Skill NFTs (composable agent configurations)
"""

import json

from ms_masa.marketplace import (
    MarketplaceAdapter,
    OnChainServiceDescriptor,
    SKILL_NFT_TEMPLATES,
    INSTALLATION_GUIDE,
)
from ms_masa.skill_manifest import MANIFEST


def demo_marketplace_advertisement():
    """Show what other agents see when discovering Ms-MASA."""
    print("=== Marketplace Advertisement ===\n")
    adapter = MarketplaceAdapter()
    ad = adapter.advertise()

    print(f"Agent: {ad['agent']['name']} v{ad['agent']['version']}")
    print(f"Protocols: {', '.join(ad['protocols'])}")
    print(f"\nSkills ({len(ad['skills'])}):")
    for name, info in ad["skills"].items():
        print(f"  [{info['pricing']}] {name}: {info['description'][:50]}...")
    print()


def demo_usage_metering():
    """Show how skill usage is tracked for billing."""
    print("=== Usage Metering ===\n")
    adapter = MarketplaceAdapter()

    # Register a caller
    adapter.authorize_caller("agent-123", tier="metered")

    # Simulate usage
    adapter.record_usage("scan_markets", "agent-123", duration_ms=120)
    adapter.record_usage("detect_signals", "agent-123", duration_ms=450)
    adapter.record_usage("explain", "agent-123", duration_ms=5)

    summary = adapter.billing_summary("agent-123")
    print(f"Total calls: {summary['total_calls']}")
    print(f"By skill: {summary['by_skill']}")
    print()


def demo_olas_registration():
    """Show OLAS autonomous service registration."""
    print("=== OLAS Service Registration ===\n")
    descriptor = OnChainServiceDescriptor()

    print("Service calldata:")
    calldata = descriptor.registration_calldata()
    print(f"  Contract: {calldata['contract']}")
    print(f"  Method: {calldata['method']}")
    print()

    print("Component registrations:")
    for comp in descriptor.component_registration()[:3]:
        print(f"  - {comp['metadata']['name']}: {comp['metadata']['description'][:50]}...")
    print(f"  ... and {len(descriptor.component_registration()) - 3} more")
    print()

    print("Staking parameters:")
    staking = descriptor.staking_parameters()
    for key, val in staking.items():
        print(f"  {key}: {val}")
    print()


def demo_skill_nfts():
    """Show composable Skill NFT configurations."""
    print("=== Skill NFT Templates ===\n")
    for name, nft in SKILL_NFT_TEMPLATES.items():
        metadata = nft.to_erc721_metadata()
        rarity = next(
            (a["value"] for a in metadata["attributes"] if a["trait_type"] == "Rarity"),
            "Unknown",
        )
        print(f"  [{rarity}] {metadata['name']}")
        print(f"    Skills: {', '.join(metadata['properties']['skills'])}")
        print(f"    Agent Type: {metadata['properties']['agent_type']}")
        print()


def demo_installation_guide():
    """Show installation directions for all platforms."""
    print("=== Installation Guide ===\n")
    for key, guide in list(INSTALLATION_GUIDE.items())[:4]:
        print(f"  {guide['title']}:")
        print(f"    {guide['steps'][0]}")
        print(f"    ...")
        print()


if __name__ == "__main__":
    demo_marketplace_advertisement()
    demo_usage_metering()
    demo_olas_registration()
    demo_skill_nfts()
    demo_installation_guide()
