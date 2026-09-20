from fastapi import APIRouter, HTTPException
from ..models.stock import AnalyzeRequest, HypothesisRequest
from ..services.analysis import run_full_analysis, get_analysis, rerun_hypothesis

router = APIRouter()

@router.post("/analyze")
def analyze(req: AnalyzeRequest):
    try:
        return run_full_analysis(req.symbol, req.start, req.end, req.mu0, req.alpha, req.alternative,
                                 investing_pair_id=req.investing_pair_id, stock_name=req.stock_name)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Market data could not be retrieved. Please try again in a moment.")

@router.post("/analyze/hypothesis")
def hypothesis(req: HypothesisRequest):
    try:
        return rerun_hypothesis(req.analysis_id, req.mu0, req.alpha, req.alternative)
    except KeyError:
        raise HTTPException(status_code=404, detail="Unknown analysis_id")
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

@router.get("/data/{analysis_id}")
def data(analysis_id: str):
    b = get_analysis(analysis_id)
    if not b:
        raise HTTPException(status_code=404, detail="Unknown analysis_id")
    return b
