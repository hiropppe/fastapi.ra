from fastapi import APIRouter

router = APIRouter()


@router.get("/healthcheck", summary="", description="", response_description="")
async def healthcheck() -> str:
    return "O.K."
