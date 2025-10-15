from fastapi import APIRouter

# from tuto.versioning.path_versioning.routing import versioned_api_route

# router = APIRouter(route_class=versioned_api_route(1, 1))
router = APIRouter()


@router.get("/version", summary="", description="", response_description="")
async def version() -> str:
    return "v0.1.1"
