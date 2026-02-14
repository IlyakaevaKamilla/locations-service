# src/main.py
from contextlib import asynccontextmanager
from fastapi import FastAPI
import logging.config

from config import settings
from app.utils.logging import LOGGING_CONFIG

logging.config.dictConfig(LOGGING_CONFIG)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logging.info("Service is starting up...")
    
    yield
    
    logging.info("Service is shutting down...")

def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        debug=settings.DEBUG,
        lifespan=lifespan,
    )
    
    return app

app = create_app()