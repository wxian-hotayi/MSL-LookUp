"""Core MSL lookup logic combining API and local cache."""
import re
from typing import Optional

from local_db import cache_msl, get_cached_msl, log_lookup
from digikey_api import search_part_retry, DigiKeyAPIError


def normalize_mpn(mpn: str) -> str:
    """Normalize MPN for consistent matching."""
    return re.sub(r'\s+', '', mpn.strip()).upper()


def find_msl(mpn: str, use_cache: bool = True) -> Optional[dict]:
    """
    Find MSL for a given MPN.

    1. Check local cache first
    2. Query DigiKey API if not cached
    3. Cache and return result
    """
    mpn_normalized = normalize_mpn(mpn)

    # Check cache first
    if use_cache:
        cached = get_cached_msl(mpn_normalized)
        if cached:
            log_lookup(mpn, "cache_hit")
            return {
                "msl": cached[0],
                "package": cached[1],
                "manufacturer": cached[2],
                "description": cached[3],
                "source": "cache",
            }

    # Query DigiKey API
    try:
        result = search_part_retry(mpn)
        if result:
            # Cache the result
            cache_msl(
                mpn_normalized,
                result.get("msl", ""),
                result.get("package"),
                result.get("manufacturer"),
                result.get("description"),
            )
            log_lookup(mpn, "success")
            result["source"] = "api"
            return result
    except DigiKeyAPIError as e:
        log_lookup(mpn, "error", str(e))

    log_lookup(mpn, "not_found")
    return None


def find_msl_batch(mpns: list, progress_callback=None) -> dict:
    """
    Batch lookup MSL for multiple MPNs.

    Returns dict mapping MPN -> MSL result (or None if not found)
    """
    results = {}
    total = len(mpns)

    for i, mpn in enumerate(mpns):
        results[mpn] = find_msl(mpn)
        if progress_callback:
            progress_callback((i + 1) / total * 100)

    return results
