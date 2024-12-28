from fastapi import FastAPI, Depends
from contextlib import asynccontextmanager
from requests import Request
from .database.db import create_db_and_tables
from .routers.auth_router import auth_router
from .users import User, current_active_user
from app.routers.homepage_router import homepage_router
from fastapi.middleware.cors import CORSMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_db_and_tables()
    yield

app = FastAPI(title="TEDU SageAI",
              description="An AI-powered learning assistant integrated with LMS.",
              version="0.0.1",
              lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(auth_router)
app.include_router(homepage_router)


# """
# This route demonstrates how we restrict access to authenticated users.
# The Depends(current_active_user) ensures that only users with valid tokens
# can access this endpoint, enforcing security throughout our API."
# """
@app.get("/protected-route")
async def protected_route(user=Depends(current_active_user)):
    return {"message": f"Welcome, {user.email}!"}



