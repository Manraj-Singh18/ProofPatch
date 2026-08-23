from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any


ABI = [
    {
        "inputs": [
            {"internalType": "bytes32", "name": "evidenceHash", "type": "bytes32"},
            {"internalType": "bool", "name": "accepted", "type": "bool"},
        ],
        "name": "anchor",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function",
    }
]


@dataclass(frozen=True)
class AnchorResult:
    network: str
    contract: str
    transaction_hash: str
    explorer_url: str | None = None
    block_number: int | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "network": self.network,
            "contract": self.contract,
            "transaction_hash": self.transaction_hash,
            "explorer_url": self.explorer_url,
            "block_number": self.block_number,
        }


def anchor_configured() -> bool:
    return all(
        os.getenv(name)
        for name in (
            "PATCHPROOF_ETH_RPC_URL",
            "PATCHPROOF_ETH_PRIVATE_KEY",
            "PATCHPROOF_ETH_CONTRACT_ADDRESS",
        )
    )


def anchor_proof(commitment: str, accepted: bool) -> AnchorResult:
    """Anchor a PatchProof commitment on Ethereum.

    This is deliberately opt-in: no private key is read and no transaction is
    attempted unless all PATCHPROOF_ETH_* settings are present.
    """
    if not anchor_configured():
        raise RuntimeError("Ethereum anchoring is not configured")

    evidence_hash = bytes.fromhex(commitment.removeprefix("0x"))
    if len(evidence_hash) != 32:
        raise ValueError("Proof commitment must be a 32-byte SHA-256 hex value")

    try:
        from web3 import Web3
    except ImportError as exc:  # pragma: no cover - exercised only when configured
        raise RuntimeError("Install the optional Ethereum dependency with: pip install web3") from exc

    rpc_url = os.environ["PATCHPROOF_ETH_RPC_URL"]
    private_key = os.environ["PATCHPROOF_ETH_PRIVATE_KEY"]
    contract_address = os.environ["PATCHPROOF_ETH_CONTRACT_ADDRESS"]
    network = os.getenv("PATCHPROOF_ETH_NETWORK", "Ethereum testnet")
    explorer_base = os.getenv("PATCHPROOF_ETH_EXPLORER_URL", "").rstrip("/")

    w3 = Web3(Web3.HTTPProvider(rpc_url))
    if not w3.is_connected():
        raise RuntimeError(f"Unable to connect to Ethereum RPC: {rpc_url}")

    account = w3.eth.account.from_key(private_key)
    contract = w3.eth.contract(address=Web3.to_checksum_address(contract_address), abi=ABI)

    nonce = w3.eth.get_transaction_count(account.address, "pending")
    chain_id = w3.eth.chain_id
    tx = contract.functions.anchor(evidence_hash, accepted).build_transaction(
        {
            "from": account.address,
            "nonce": nonce,
            "chainId": chain_id,
            "gas": int(os.getenv("PATCHPROOF_ETH_GAS_LIMIT", "100000")),
            "maxFeePerGas": w3.to_wei(os.getenv("PATCHPROOF_ETH_MAX_FEE_GWEI", "20"), "gwei"),
            "maxPriorityFeePerGas": w3.to_wei(os.getenv("PATCHPROOF_ETH_PRIORITY_FEE_GWEI", "1"), "gwei"),
        }
    )
    signed = account.sign_transaction(tx)
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    receipt = w3.eth.wait_for_transaction_receipt(
        tx_hash,
        timeout=int(os.getenv("PATCHPROOF_ETH_RECEIPT_TIMEOUT", "120")),
    )
    if receipt.status != 1:
        raise RuntimeError(f"Ethereum anchor transaction reverted: {w3.to_hex(tx_hash)}")

    tx_hex = w3.to_hex(tx_hash)
    explorer_url = f"{explorer_base}/tx/{tx_hex}" if explorer_base else None
    return AnchorResult(
        network=network,
        contract=contract_address,
        transaction_hash=tx_hex,
        explorer_url=explorer_url,
        block_number=receipt.blockNumber,
    )
