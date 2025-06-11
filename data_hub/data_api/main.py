
import os
import uvicorn
import logging
import importlib
import inspect
from uuid import uuid4
from typing import Optional, Any
from fastapi import FastAPI, Depends, APIRouter
from asgi_correlation_id import CorrelationIdMiddleware
from fastapi.middleware.cors import CORSMiddleware

from fastapi import HTTPException, Body, status, Request
from fastapi.responses import JSONResponse
from fastapi.exception_handlers import http_exception_handler
from asgi_correlation_id import correlation_id

ROUTERS_DIR = os.path.dirname(__file__) + "/routers"
ROUTERS = [
    f"data_api.routers.{f.replace('/', '.')}" 
    for f in os.listdir(ROUTERS_DIR)
    if not f.endswith('__pycache__')
    if not f.endswith('__.py')
    ]

print(ROUTERS)

def create_app() -> FastAPI:
    tags_meta = [
        {
            "name": "Tenant DataHUB API",
            "description": "tenant data hub API"
        }
    ]

    app = FastAPI(
        openapi_tags = tags_meta,
        debug=True,
        title="Tenant DataHUB API",
        summary="",
        version="0.0.1",
        contact={
            "name": "Tannous Geagea",
            "url": "https://wasteant.com",
            "email": "tannous.geagea@wasteant.com",            
        },
        openapi_url="/openapi.json"
    )

    origins = ["http//localhost:8000"]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_methods=["*"],
        allow_headers=["X-Requested-With", "X-Request-ID"],
        expose_headers=["X-Request-ID"],
    )

    for R in ROUTERS:
        try:
            module = importlib.import_module(R)
            attr = getattr(module, 'endpoint')
            if inspect.ismodule(attr):
                app.include_router(module.endpoint.router)
        except ImportError as err:
            logging.error(f'Failed to import {R}: {err}')
            
    return app

app = create_app()

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "status_code": exc.status_code,
            "status_description": exc.detail,
            "detail": exc.detail
        }
    )

@app.exception_handler(Exception)
async def internal_server_error_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={
            "status_code": 500,
            "status_description": "Internal Server Error",
            "detail": "An unexpected error occurred. Please try again later."
        }
    )


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=19095, log_level="debug", reload=True)