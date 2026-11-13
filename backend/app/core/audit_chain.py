import hashlib
import json
from typing import Any, Dict, Optional


def calculate_record_hash(
    prev_hash: str,
    record_id: Any,
    event_type: str,
    actor_id: Optional[str],
    timestamp_iso: str,
    metadata: Dict[str, Any]
) -> str:
    """
    Computes SHA-256 hash for a block in the tamper-evident audit log chain:
    H_n = SHA-256(H_{n-1} || id || event_type || actor_id || timestamp || canonical_metadata_json)
    """
    canonical_meta = json.dumps(metadata, sort_keys=True, default=str)
    raw_payload = f"{prev_hash}|{record_id}|{event_type}|{actor_id or 'SYSTEM'}|{timestamp_iso}|{canonical_meta}"
    return hashlib.sha256(raw_payload.encode("utf-8")).hexdigest()

