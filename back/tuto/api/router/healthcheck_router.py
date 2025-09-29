from fastapi import APIRouter

router = APIRouter(tags=["HealthCheckRouter"])

@router.get(
    "/healthcheck",
    summary="",
    description="",
    response_description="")
async def healthcheck() -> str:
    return "O.K."
