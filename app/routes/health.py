from fastapi import APIRouter, status

from app.utils import ResponseMessages

router = APIRouter()

@router.get("/health", status_code=status.HTTP_200_OK)
def health_check():
    return {"status": ResponseMessages.HEALTH_OK}