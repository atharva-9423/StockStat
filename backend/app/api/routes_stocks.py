from fastapi import APIRouter, Query
from ..config import settings
from ..services.market_data.factory import get_provider

router = APIRouter()

@router.get("/stocks/search")
def search(q: str = Query(min_length=1)):
    provider = get_provider(settings.data_provider)
    try:
        results = provider.search_symbol(q)
    except Exception:
        return {"query": q, "results": [], "error": "Market data could not be retrieved. Please try again in a moment."}
    if not results:
        return {"query": q, "results": [], "message": "We couldn't find a matching NSE-listed stock."}
    return {"query": q, "results": [{"symbol": r.symbol, "name": r.name, "exchange": r.exchange,
                                       "investing_pair_id": r.investing_pair_id} for r in results]}
