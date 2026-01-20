from fastapi import APIRouter
from engines.orderflow_histogram import OrderFlowHistogram

router = APIRouter()
histogram = OrderFlowHistogram()
ladder = PriceLadder()

@router.get("/orderflow")
def get_orderflow():
    return histogram.last_n()
    
@router.get("/orderflow/ladder")
def get_ladder():
    return ladder.snapshot()
