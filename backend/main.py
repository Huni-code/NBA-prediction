from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from database import engine, Base
from routers import teams_router, games_router, predictions_router
from etl.pipeline import run_full_pipeline


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await run_full_pipeline()
    yield


app = FastAPI(
    title="🏀 NBA Win Predictor API",
    version="3.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(teams_router,       prefix="/api/teams",       tags=["Teams"])
app.include_router(games_router,       prefix="/api/games",       tags=["Games"])
app.include_router(predictions_router, prefix="/api/predictions", tags=["Predictions"])


@app.get("/")
async def root():
    return {
        "status": "online",
        "docs":   "http://localhost:8000/docs",
        "예측 예시": "http://localhost:8000/api/predictions/predict?home=BOS&away=LAL",
    }


@app.post("/api/etl/seed", tags=["ETL"])
async def manual_seed():
    await run_full_pipeline()
    return {"status": "완료"}
