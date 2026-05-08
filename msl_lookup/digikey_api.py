"""DigiKey API v4 integration for MSL lookups."""
import os
import re
import time
import requests
import threading
import urllib.parse
from requests.adapters import HTTPAdapter

DIGIKEY_CLIENT_ID = "YCMOyT9X5pvXIsj8xWsb3gUEFV4DJHHs5SuiGzJxOmwgh8Bc"
DIGIKEY_CLIENT_SECRET = "FQmFxwtFKU3fe1fFITk4FVLF9ddHLZjjzYKzzYG89EB0oMYkuGhIf7VwkumypZHq"
DIGIKEY_SITE = "US"
DIGIKEY_LANGUAGE = "en"
DIGIKEY_CURRENCY = "USD"
TIMEOUT = 30

# Persistent session with connection pooling
_session = requests.Session()
_adapter = HTTPAdapter(pool_connections=10, pool_maxsize=10)
_session.mount("https://", _adapter)
_session.mount("http://", _adapter)

# Token cache
_token_cache = {"token": None, "expires_at": 0}
_token_lock = threading.Lock()


class DigiKeyAPIError(Exception):
    pass


def get_access_token(client_id: str, client_secret: str) -> str:
    """Get OAuth2 access token from DigiKey with caching (tokens valid ~3600s)."""
    now = time.time()

    with _token_lock:
        if _token_cache["token"] and now < _token_cache["expires_at"] - 60:
            return _token_cache["token"]

    token_url = "https://api.digikey.com/v1/oauth2/token"

    resp = _session.post(
        token_url,
        data={
            "client_id": client_id,
            "client_secret": client_secret,
            "grant_type": "client_credentials"
        },
        timeout=TIMEOUT
    )

    if resp.status_code != 200:
        raise DigiKeyAPIError(f"Token failed: {resp.status_code}")

    data = resp.json()
    token = data.get("access_token", "")

    with _token_lock:
        _token_cache["token"] = token
        _token_cache["expires_at"] = now + 3600

    return token


def search_part(mpn: str) -> dict:
    if not DIGIKEY_CLIENT_ID or not DIGIKEY_CLIENT_SECRET:
        raise DigiKeyAPIError("DIGIKEY_CLIENT_ID and DIGIKEY_CLIENT_SECRET must be set")

    mpn_clean = re.sub(r"\s+", "", mpn.strip()).upper()
    encoded_mpn = urllib.parse.quote(mpn_clean)

    access_token = get_access_token(DIGIKEY_CLIENT_ID, DIGIKEY_CLIENT_SECRET)
    if not access_token:
        raise DigiKeyAPIError("Failed to get access token")

    headers = {
        "X-DIGIKEY-Client-Id": DIGIKEY_CLIENT_ID,
        "Authorization": f"Bearer {access_token}",
        "X-DIGIKEY-Locale-Site": DIGIKEY_SITE,
        "X-DIGIKEY-Locale-Language": DIGIKEY_LANGUAGE,
        "X-DIGIKEY-Locale-Currency": DIGIKEY_CURRENCY,
        "Accept": "application/json"
    }

    # Try encoded URL first
    product_url = f"https://api.digikey.com/products/v4/search/{encoded_mpn}/productdetails"
    resp = _session.get(product_url, headers=headers, timeout=TIMEOUT)

    # Fallback to direct URL (no encoding) if encoded fails
    if resp.status_code != 200:
        product_url = f"https://api.digikey.com/products/v4/search/{mpn_clean}/productdetails"
        resp = _session.get(product_url, headers=headers, timeout=TIMEOUT)

    if resp.status_code != 200:
        raise DigiKeyAPIError(f"Product search failed: {resp.status_code}")

    data = resp.json()

    # API may return "Product" (exact), "Products" (list), or "ExactMatches" (list)
    product = data.get("Product") or {}
    if not product:
        for key in ("ExactMatches", "Products"):
            lst = data.get(key) or []
            if lst:
                product = lst[0]
                break

    # MSL is in Classifications.MoistureSensitivityLevel or Parameters array
    msl_text = (
        product.get("Classifications", {})
               .get("MoistureSensitivityLevel")
    )
    if not msl_text:
        for param in product.get("Parameters", []):
            name = param.get("ParameterText", "").lower()
            if "moisture" in name or "msl" in name:
                msl_text = param.get("ValueText", "")
                break

    msl = None
    if msl_text:
        match = re.search(r"\d+", str(msl_text))
        if match:
            msl = int(match.group())

    return {
        "msl": msl,
        "package": "",
        "manufacturer": product.get("Manufacturer", {}).get("Name", ""),
        "description": product.get("Description", {}).get("ProductDescription", ""),
    }


def search_part_retry(mpn: str, retries: int = 3, delay: float = 1.0) -> dict:
    for attempt in range(retries):
        try:
            return search_part(mpn)
        except DigiKeyAPIError as e:
            if attempt < retries - 1:
                time.sleep(delay)
            else:
                raise
