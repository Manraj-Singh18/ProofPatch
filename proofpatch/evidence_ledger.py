from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Sequence

from .commitment import evidence_commitment
from .edit_loop import FileEdit
from .models import EvidenceItem


def file_hashes(repo: str | Path, paths: Sequence[str]) -> dict[str, str]:
    root = Path(repo).resolve()
    result: dict[str, str] = {}
    for relative in sorted(set(paths)):
        target = (root / relative).resolve()
        if root == target or root not in target.parents or not target.is_file():
            continue
        result[relative] = hashlib.sha256(target.read_bytes()).hexdigest()
    return result


def patch_hash(edits: Sequence[FileEdit]) -> str:
    payload = "".join(f"{edit.path}\0{edit.content}\0" for edit in sorted(edits, key=lambda e: e.path))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def build_ledger(
    repo: str | Path,
    edits: Sequence[FileEdit],
    before: dict[str, str],
    after: dict[str, str],
    raw_model_response: str | None = None,
) -> tuple[EvidenceItem, ...]:
    items = [
        EvidenceItem(
            kind="patch",
            source="proofpatch-edit-ledger",
            value={"files": [edit.path for edit in edits], "sha256": patch_hash(edits)},
        ),
        EvidenceItem(
            kind="file-hashes",
            source="sha256",
            value={"before": before, "after": after},
        ),
    ]
    if raw_model_response is not None:
        items.append(
            EvidenceItem(
                kind="model-response",
                source="provider",
                value={
                    "sha256": hashlib.sha256(raw_model_response.encode("utf-8")).hexdigest(),
                    "raw": raw_model_response,
                },
            )
        )
    return tuple(items)


def commitment_for_report(claims: Sequence[dict], evidence: Sequence[EvidenceItem]) -> str:
    return evidence_commitment(
        {
            "claims": list(claims),
            "evidence": [
                {"kind": item.kind, "source": item.source, "value": item.value}
                for item in evidence
            ],
        }
    )
