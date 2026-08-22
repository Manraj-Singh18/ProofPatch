# PatchProof Ethereum proof anchor

PatchProof can optionally publish the SHA-256 commitment of an accepted or rejected proof report to Ethereum. The blockchain is a public timestamp/notary layer; it does **not** decide whether the code is correct. Local deterministic verification remains the source of the verdict.

## 1. Deploy the anchor contract

`contracts/PatchProofAnchor.sol` contains the small contract. Deploy it to an Ethereum test network first. Keep the deployer/signer wallet separate from production funds and never commit its private key.

The contract exposes:

```solidity
function anchor(bytes32 evidenceHash, bool accepted) external
```

and emits `ProofAnchored`, containing the commitment, verdict, timestamp, and submitting address.

## 2. Install the optional Python dependency

```bash
pip install -e '.[ethereum]'
```

## 3. Configure the signer

Set these environment variables in the shell running the PatchProof API:

```bash
export PATCHPROOF_ETH_RPC_URL="https://YOUR-TESTNET-RPC"
export PATCHPROOF_ETH_PRIVATE_KEY="0xYOUR_TESTNET_PRIVATE_KEY"
export PATCHPROOF_ETH_CONTRACT_ADDRESS="0xYOUR_DEPLOYED_CONTRACT"
export PATCHPROOF_ETH_NETWORK="Ethereum testnet"
export PATCHPROOF_ETH_EXPLORER_URL="https://YOUR-EXPLORER/tx"
```

Optional gas settings:

```bash
export PATCHPROOF_ETH_GAS_LIMIT="100000"
export PATCHPROOF_ETH_MAX_FEE_GWEI="20"
export PATCHPROOF_ETH_PRIORITY_FEE_GWEI="1"
```

Do not put any of these secrets in Git, `.env` files committed to the repository, screenshots, or proof reports.

## 4. Run PatchProof

```bash
python -m proofpatch.http_api
```

When a proof report completes, PatchProof anchors its existing `commitment` value. If Ethereum is not configured, verification continues normally and the UI says the anchor is unavailable.

## What is anchored?

Only the 32-byte proof commitment is written on-chain. The full evidence report remains off-chain. Anyone with the original proof package can recompute its commitment and compare it with the Ethereum event.

This preserves the core trust boundary:

```text
AI proposes
    ↓
PatchProof verifies locally
    ↓
SHA-256 commitment
    ↓
Ethereum records the commitment
```

Ethereum provides persistence and timestampability, not correctness.
