from fastapi import APIRouter
from app.db.crud import get_defect_metrics

router = APIRouter()

@router.get("/", summary="Get defect metrics")
def get_metrics():
    return get_defect_metrics()
