#!/usr/bin/env python3
"""
Main entry point for the backend API server
Run with: python run_server.py
"""

import uvicorn
from app.core.config import settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    logger.info(f"Starting AI Crypto Trading Assistant on {settings.backend_host}:{settings.backend_port}")
    logger.info(f"Environment: {settings.environment}")
    
    uvicorn.run(
        "app.main:app",
        host=settings.backend_host,
        port=settings.backend_port,
        reload=settings.debug,
        log_level="info"
    )
