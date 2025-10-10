from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from tuto.api.router import auth_router, healthcheck_router, user_router

app = FastAPI()
app.include_router(healthcheck_router, tags=["healthcheck"])
app.include_router(auth_router, prefix="/auth", tags=["auth"])
app.include_router(user_router, prefix="/api", tags=["users"])


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
