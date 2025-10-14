from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from tuto.api.router import auth_router, healthcheck_router, user_router, v1_0, v1_1
from tuto.versioning.header_versioning.fastapi import HeaderRoutingFastAPI
from tuto.versioning.header_versioning.openapi import doc_generation
from tuto.versioning.header_versioning.routing import HeaderVersionedAPIRouter
from tuto.versioning.path_versioning.versioning import VersionedFastAPI

# PATH ベースのバージョニング
app = FastAPI(title="Tuto API", description="API for Tuto application")
app.include_router(healthcheck_router, tags=["healthcheck"])
app.include_router(auth_router, prefix="/auth", tags=["auth"])
app.include_router(user_router, prefix="/api", tags=["users"])
app.include_router(v1_0.healthcheck_router, prefix="/api", tags=["users"])
app.include_router(v1_1.healthcheck_router, prefix="/api", tags=["users"])
app = VersionedFastAPI(app, enable_latest=True)

# ヘッダーベースのバージョニング
"""
app = HeaderRoutingFastAPI(
    version_header="x-api-version",
    title="Tuto API",
    description="API for Tuto application",
)

root_router = HeaderVersionedAPIRouter(default_version="1")
root_router.include_router(healthcheck_router, tags=["healthcheck"], version="1")
root_router.include_router(auth_router, prefix="/auth", tags=["auth"], version="1")
root_router.include_router(user_router, prefix="/api", tags=["users"], version="1")

root_router.include_router(healthcheck_router, tags=["healthcheck"], version="2")

app.include_router(root_router)
app = doc_generation(app)
"""

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
