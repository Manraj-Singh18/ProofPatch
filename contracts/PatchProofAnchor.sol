// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/// @title PatchProof Anchor
/// @notice Permanently records the commitment of a PatchProof verification report.
contract PatchProofAnchor {
    event ProofAnchored(
        bytes32 indexed evidenceHash,
        bool accepted,
        uint256 timestamp,
        address indexed submitter
    );

    function anchor(bytes32 evidenceHash, bool accepted) external {
        emit ProofAnchored(evidenceHash, accepted, block.timestamp, msg.sender);
    }
}
