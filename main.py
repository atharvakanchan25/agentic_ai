"""
Main application entry point
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import logging
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import config
from src.database.database import init_db
from src.api.routes import router

# Logging
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format=config.LOG_FORMAT
)
logger = logging.getLogger(__name__)

# App
app = FastAPI(
    title="Timetable AI - Multi-Agent Scheduling System",
    description="University timetable generation using multi-agent AI and constraint programming",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)

@app.on_event("startup")
def startup():
    logger.info("Initializing database...")
    init_db()
    logger.info("Timetable AI system started")

@app.get("/")
def root():
    return {
        "name": "Timetable AI",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs"
    }

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=config.API_HOST,
        port=config.API_PORT,
        reload=config.API_RELOAD
    )
