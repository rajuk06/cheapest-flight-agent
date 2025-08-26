import os, re, requests
from typing import List, Dict, Optional
from dotenv import load_dotenv

load_dotenv()

DRY_RUN = os.getenv("DRY_RUN", "true").lower() in ("1","true","yes")
AMADEUS_KEY = os.getenv("AMADEUS_KEY", "")
AMADEUS_SECRET = os.getenv("AMADEUS_SECRET", "")
DEFAULT_CURRENCY = "GBP"

def mock_search(origins: List[str], destinations: List[str], depart_date: str):
    rows: List[Dict] = []
    for o in origins:
        for d in destinations:
            rows.append({
                "origin": o, "destination": d,
                "out_date": depart_date, "return_date": None,
                "stops": 1, "duration_minutes": 600,
                "price": 399.0, "currency": "GBP",
                "provider": "mock", "raw": None
            })
    return rows

def _amadeus_token() -> str:
    url = "https://test.api.amadeus.com/v1/security/oauth2/token"
    r = requests.post(url, data={
        "grant_type": "client_credentials",
        "client_id": AMADEUS_KEY,
        "client_secret": AMADEUS_SECRET
    }, timeout=30)
    r.raise_for_status()
    return r.json()["access_token"]

def _amadeus_search(token: str, origin: str, dest: str, depart: str,
                    ret: Optional[str], adults: int = 1, max_results: int = 30):
    url = "https://test.api.amadeus.com/v2/shopping/flight-offers"
    params = {
        "originLocationCode": origin,
        "destinationLocationCode": dest,
        "departureDate": depart,
        "adults": adults,
        "currencyCode": DEFAULT_CURRENCY,
        "nonStop": "false",
        "max": max_results
    }
    if ret: params["returnDate"] = ret
    r = requests.get(url, headers={"Authorization": f"Bearer {token}"}, params=params, timeout=45)
    r.raise_for_status()
    return r.json().get("data", [])

def _parse_duration_minutes(iso: str) -> int:
    if not iso or not iso.startswith("PT"): return 0
    m = re.search(r"PT(?:(\d+)H)?(?:(\d+)M)?", iso)
    h = int(m.group(1) or 0) if m else 0
    mnt = int(m.group(2) or 0) if m else 0
    return h*60 + mnt

def _normalize_amadeus(offer) -> Dict:
    its = offer.get("itineraries", [])
    out = its[0] if its else {}
    segs = out.get("segments", [])
    origin = segs[0]["departure"]["iataCode"] if segs else ""
    dest = segs[-1]["arrival"]["iataCode"] if segs else ""
    out_date = segs[0]["departure"]["at"][:10] if segs else ""
    stops = max(0, len(segs)-1)
    duration = _parse_duration_minutes(out.get("duration", "PT0M"))
    price = float(offer.get("price", {}).get("grandTotal", 0.0))
    ret_date = None
    if len(its) > 1 and its[1].get("segments"):
        ret_date = its[1]["segments"][0]["departure"]["at"][:10]
    return {
        "origin": origin, "destination": dest,
        "out_date": out_date, "return_date": ret_date,
        "stops": stops, "duration_minutes": duration,
        "price": price, "currency": DEFAULT_CURRENCY,
        "provider": "amadeus", "raw": offer
    }

def live_search(origins: List[str], destinations: List[str], depart_date: str,
                return_date: Optional[str], adults: int, limit_per_route: int):
    token = _amadeus_token()
    results: List[Dict] = []
    for o in origins:
        for d in destinations:
            offers = _amadeus_search(token, o, d, depart_date, return_date, adults=adults, max_results=limit_per_route)
            for off in offers:
                try:
                    results.append(_normalize_amadeus(off))
                except Exception:
                    pass
    # sort by price then duration
    results.sort(key=lambda r: (r["price"], r["duration_minutes"]))
    return results

def search_entry(origins: List[str], destinations: List[str], depart_date: str,
                 return_date: Optional[str], adults: int, limit_per_route: int):
    if DRY_RUN or not (AMADEUS_KEY and AMADEUS_SECRET):
        return mock_search(origins, destinations, depart_date)
    return live_search(origins, destinations, depart_date, return_date, adults, limit_per_route)
from typing import List, Optional, Dict
from agent_uk_india import UK_AIRPORTS, INDIA_AIRPORTS, expand_dates, pareto_price_duration

def uk_india_grid_search(
    depart_date: str,
    return_date: Optional[str],
    days_flex: int,
    adults: int,
    limit_per_route: int,
    live: bool
) -> List[Dict]:
    results: List[Dict] = []
    dep_dates = expand_dates(depart_date, days_flex)
    ret_dates = expand_dates(return_date, days_flex) if return_date else [None]

    for o in UK_AIRPORTS:
        for d in INDIA_AIRPORTS:
            for dep in dep_dates:
                for ret in ret_dates:
                    if live:
                        results.extend(live_search([o], [d], dep, ret, adults, limit_per_route))
                    else:
                        results.extend(mock_search([o], [d], dep))
    # dedupe rough duplicates (same route+date+price)
    seen = set()
    uniq = []
    for r in results:
        key = (r.get("origin"), r.get("destination"), r.get("out_date"), int(r.get("price",0)))
        if key not in seen:
            uniq.append(r); seen.add(key)
    # Pareto filter + sort by cheapest then shortest
    pareto = pareto_price_duration(uniq)
    pareto.sort(key=lambda r: (r.get("price",1e9), r.get("duration_minutes",1e9)))
    return pareto

