from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from tuto.api.router import (
    auth_router,
    healthcheck_router,
    healthcheck_router_v2,
    user_router,
    v1_0,
    v1_1,
)
from tuto.versioning.fastapi import (
    CustomHeaderVersionMiddleware,
)
from tuto.versioning.openapi import doc_generation
from tuto.versioning.path_versioning.versioning import VersionedFastAPI
from tuto.versioning.routing import (
    HeaderVersionedAPIRouter,
    VersionedAPIRouter,
)

# PATH ベースのバージョニング
"""
app = FastAPI(title="Tuto API", description="API for Tuto application")
app.include_router(healthcheck_router, tags=["healthcheck"])
app.include_router(auth_router, prefix="/auth", tags=["auth"])
app.include_router(user_router, prefix="/api", tags=["users"])
app.include_router(v1_0.healthcheck_router, prefix="/api", tags=["users"])
app.include_router(v1_1.healthcheck_router, prefix="/api", tags=["users"])
app = VersionedFastAPI(app, enable_latest=True)
"""

# ヘッダーベースバージョニング
# app = FastAPI(title="Tuto API", description="API for Tuto application")
# app.add_middleware(CustomHeaderVersionMiddleware, version_header="x-api-version")
# root_router = HeaderVersionedAPIRouter(default_version="1")
# root_router.include_router(healthcheck_router, tags=["healthcheck"], version="1")
# root_router.include_router(auth_router, prefix="/auth", tags=["auth"], version="1")
# root_router.include_router(user_router, prefix="/api", tags=["users"], version="1")
# root_router.include_router(healthcheck_router_v2, tags=["healthcheck"], version="2")

# パスベースのバージョニング
app = FastAPI(title="Tuto API", description="API for Tuto application")
root_router = VersionedAPIRouter(default_version="1")
root_router.include_router(healthcheck_router, tags=["healthcheck"], version="1")
root_router.include_router(auth_router, prefix="/auth", tags=["auth"], version="1")
root_router.include_router(user_router, prefix="/api", tags=["users"], version="1")
root_router.include_router(healthcheck_router_v2, tags=["healthcheck"], version="2")

app.router = root_router
app = doc_generation(app)


origins = [
    "http://192.168.88.214:15173",
    "http://192.168.88.214:18000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
