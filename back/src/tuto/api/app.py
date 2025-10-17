from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from tuto.api.router import v0_1_0, v0_1_1
from tuto.auth.auth_helper import OAuth2PasswordOTPBearerUsingCookie
from tuto.versioning.fastapi import (
    CustomHeaderVersionMiddleware,
)
from tuto.versioning.openapi import doc_generation
from tuto.versioning.routing import (
    HeaderVersionedAPIRouter,
    VersionedAPIRouter,
)

app = FastAPI(title="Tuto API", description="API for Tuto application")

# API Versioning Examples
# Added path-based versioning functionality to tikon93's header versioning code
# https://github.com/tikon93/fastapi-header-versioning

# Path Versioning
root_router = VersionedAPIRouter(default_version="1.0")

# Header Versioning
# root_router = HeaderVersionedAPIRouter(default_version="1")
# app.add_middleware(CustomHeaderVersionMiddleware, version_header="x-api-version")

# version 0.1 routes
root_router.include_router(v0_1_0.version_router, tags=["sys"], version="0.1")
root_router.include_router(v0_1_0.healthcheck_router, tags=["sys"], version="0.1")
root_router.include_router(
    v0_1_0.auth_router, prefix="/auth", tags=["auth"], version="0.1"
)
root_router.include_router(
    v0_1_0.user_router, prefix="/api", tags=["users"], version="0.1"
)

# version 0.2 routes
root_router.include_router(v0_1_1.version_router, tags=["sys"], version="0.1.1")
root_router.include_router(v0_1_1.healthcheck_router, tags=["sys"], version="0.1.1")
root_router.include_router(
    v0_1_1.auth_router, prefix="/auth", tags=["auth"], version="0.1.1"
)
root_router.include_router(
    v0_1_1.user_router, prefix="/api", tags=["users"], version="0.1.1"
)

app.router = root_router
app = doc_generation(app)


# Yet another simple way of doing Path Versioning using code from DeanWay
# https://github.com/DeanWay/fastapi-versioning

# from tuto.versioning.path_versioning.versioning import VersionedFastAPI
# from tuto.api.router import (v1_0, v1_1)
# app = FastAPI(title="Tuto API", description="API for Tuto application")
# app.include_router(healthcheck_router, tags=["healthcheck"])
# app.include_router(auth_router, prefix="/auth", tags=["auth"])
# app.include_router(user_router, prefix="/api", tags=["users"])
# app.include_router(v1_0.version_router)
# app.include_router(v1_1.version_router)
# app = VersionedFastAPI(app, enable_latest=True)


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
