"""Mouser API integration for MSL lookups."""
import os
import time
import requests

MOUSER_API_KEY = os.environ.get("MOUSER_API_KEY", "")
MOUSER_API_URL = "https://api.mouser.com/api/v1"
TIMEOUT = 15

_session = requests.Session()


class MouserAPIError(Exception):
    pass


def search_part(mpn: str) -> dict:
    if not MOUSER_API_KEY:
        raise MouserAPIError("MOUSER_API_KEY environment variable not set")

    headers = {
        "x-api-key": MOUSER_API_KEY,
        "Content-Type": "application/json",
    }

    payload = {"partNumber": mpn}

    try:
        resp = _session.post(
            f"{MOUSER_API_URL}/search/partnumber",
            headers=headers,
            json=payload,
            timeout=TIMEOUT,
        )
        resp.raise_for_status()
        data = resp.json()

        products = data.get("SearchResults", {}).get("Parts", [])
        if not products:
            return None

        part = products[0]

        # Extract MSL from ProductAttributes
        msl = None
        for attr in part.get("ProductAttributes", []):
            name = attr.get("AttributeName", "").lower()
            if "msl" in name or "moisture sensitivity" in name:
                msl = attr.get("AttributeValue")
                break

        return {
            "msl": msl or "",
            "package": part.get("PackageType", ""),
            "manufacturer": part.get("Manufacturer", ""),
            "description": part.get("Description", ""),
            "raw_attributes": part.get("ProductAttributes", []),
        }
    except requests.RequestException as e:
        raise MouserAPIError(f"API request failed: {e}")


def search_part_retry(mpn: str, retries: int = 3, delay: float = 1.0) -> dict:
    for attempt in range(retries):
        try:
            return search_part(mpn)
        except MouserAPIError as e:
            if attempt < retries - 1:
                time.sleep(delay)
            else:
                raise
