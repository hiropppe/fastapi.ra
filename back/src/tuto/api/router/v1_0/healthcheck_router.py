from fastapi import APIRouter

from tuto.versioning.path_versioning.routing import versioned_api_route

router = APIRouter(route_class=versioned_api_route(1, 0))


@router.get("/healthcheck", summary="", description="", response_description="")
async def healthcheck() -> str:
    return "O.K."
