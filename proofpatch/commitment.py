from __future__ import annotations

import hashlib
import json
from typing import Any


def canonicalize(value: Any) -> str:
    """Serialize evidence deterministically using canonical JSON."""
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def evidence_commitment(evidence: Any) -> str:
    """Return a SHA-256 commitment over canonical evidence JSON."""
    payload = canonicalize(evidence).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()
