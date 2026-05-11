"""
Sanos y Salvos — Match Microservice
Motor de coincidencias con algoritmo de scoring ponderado.
"""

import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from sqlalchemy import text

from app.api.routes import router
from app.config import Base, engine
from app.models import match
from app.events.consumer import start_consumer
from app.events.publisher import publisher

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("match-service")

async def init_database():
    """Create service schema and tables when running in a fresh database."""
    async with engine.begin() as conn:
        await conn.execute(text("CREATE SCHEMA IF NOT EXISTS match_service"))
        await conn.run_sync(Base.metadata.create_all)



@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_database()
    logger.info("Match Microservice starting...")
    await publisher.connect()
    # Start RabbitMQ consumer in background
    asyncio.create_task(start_consumer())
    yield
    await publisher.close()
    logger.info("Match Microservice shutting down...")


app = FastAPI(
    title="Sanos y Salvos — Motor de Coincidencias",
    description="Microservicio que analiza reportes y detecta coincidencias entre mascotas perdidas y encontradas",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.get("/health")
def health():
    return {"status": "healthy", "service": "match-service"}
