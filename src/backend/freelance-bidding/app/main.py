"""Freelance Bidding Engine — automated proposal generation and bid tracking."""

from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from shared.database import engine
from shared.models import Base
from app.routes import router


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


app = FastAPI(title="Freelance Bidding Engine", version="1.0.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(router)


@app.get("/health")
async def health():
    return {"status": "healthy", "service": "freelance-bidding"}


if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=5015, reload=True)
