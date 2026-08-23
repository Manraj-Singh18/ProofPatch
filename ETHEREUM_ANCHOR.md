# PatchProof Ethereum proof anchor

PatchProof can optionally publish the SHA-256 commitment of an accepted or rejected proof report to Ethereum. The blockchain is a public timestamp/notary layer; it does **not** decide whether the code is correct. Local deterministic verification remains the source of the verdict.

For this demo, use **Ethereum Sepolia**, the public Ethereum testnet recommended for application development. Do not use a mainnet-funded wallet. Ethereum's current network guidance recommends Sepolia for application testing and recommends testing contracts on a testnet before mainnet deployment.

## 1. Deploy the anchor contract

`contracts/PatchProofAnchor.sol` contains the small contract. Deploy it to Sepolia first. Keep the deployer/signer wallet separate from production funds and never commit its private key.

The contract exposes:

```solidity
function anchor(bytes32 evidenceHash, bool accepted) external
```

and emits `ProofAnchored`, containing the commitment, verdict, timestamp, and submitting address.

You can deploy with Remix, Hardhat, Foundry, or another Solidity tool. The contract requires Solidity `^0.8.20`.

After deployment, save the contract address. The Sepolia chain ID is `11155111`.

## 2. Install the optional Python dependency

```bash
pip install -e '.[ethereum]'
```

## 3. Configure the signer

Copy `.env.example` to a local `.env` if you want to use environment tooling, or export the variables directly in the shell running the PatchProof API:

```bash
export PATCHPROOF_ETH_RPC_URL="https://YOUR-SEPOLIA-RPC"
export PATCHPROOF_ETH_PRIVATE_KEY="0xYOUR_TESTNET_PRIVATE_KEY"
export PATCHPROOF_ETH_CONTRACT_ADDRESS="0xYOUR_DEPLOYED_CONTRACT"
export PATCHPROOF_ETH_NETWORK="Ethereum Sepolia"
export PATCHPROOF_ETH_EXPLORER_URL="https://sepolia.etherscan.io"
```

Optional gas settings:

```bash
export PATCHPROOF_ETH_GAS_LIMIT="100000"
export PATCHPROOF_ETH_MAX_FEE_GWEI="20"
export PATCHPROOF_ETH_PRIORITY_FEE_GWEI="1"
export PATCHPROOF_ETH_RECEIPT_TIMEOUT="120"
```

Do not put private keys in Git, screenshots, proof reports, or shared configuration. `.env` is ignored by Git in this repository.

## 4. Run PatchProof

```bash
python -m proofpatch.http_api
```

When a proof report completes, PatchProof anchors its existing `commitment`. The API waits for the transaction receipt and only reports the anchor as successful when the receipt status is successful. If Ethereum is not configured, verification continues normally and the UI says the anchor is unavailable.

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

## Demo flow

1. Deploy `PatchProofAnchor.sol` to Sepolia.
2. Fund the testnet signer with Sepolia ETH from a faucet.
3. Configure the three required `PATCHPROOF_ETH_*` values.
4. Run an accepted calculator fix through the UI.
5. Open the displayed Sepolia transaction.
6. Compare the transaction's `evidenceHash` event value with the proof report's `commitment`.
7. Run an adversarial/rejected case and show that it produces a different commitment.
