from __future__ import annotations

from proofpatch.ethereum_anchor import anchor_configured


def test_ethereum_anchor_is_opt_in(monkeypatch) -> None:
    for name in (
        "PATCHPROOF_ETH_RPC_URL",
        "PATCHPROOF_ETH_PRIVATE_KEY",
        "PATCHPROOF_ETH_CONTRACT_ADDRESS",
    ):
        monkeypatch.delenv(name, raising=False)
    assert anchor_configured() is False


def test_ethereum_anchor_requires_all_settings(monkeypatch) -> None:
    monkeypatch.setenv("PATCHPROOF_ETH_RPC_URL", "http://localhost:8545")
    monkeypatch.setenv("PATCHPROOF_ETH_PRIVATE_KEY", "0xdeadbeef")
    monkeypatch.delenv("PATCHPROOF_ETH_CONTRACT_ADDRESS", raising=False)
    assert anchor_configured() is False
