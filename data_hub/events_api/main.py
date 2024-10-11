import os
import uvicorn
from uuid import uuid4
from typing import Optional, Any
from fastapi import FastAPI, Depends, APIRouter
from asgi_correlation_id import CorrelationIdMiddleware
from fastapi.middleware.cors import CORSMiddleware


from fastapi import HTTPException, Body, status, Request
from fastapi.responses import JSONResponse
from fastapi.exception_handlers import http_exception_handler
from asgi_correlation_id import correlation_id

import sys
from pathlib import Path
base_dir = Path(__file__).resolve().parent.parent
sys.path.append(str(base_dir))


from events_api.routers import event_endpoint
from events_api.config import celery_utils

def create_app() -> FastAPI:
    tags_metadata = [
        {
            "name": "Waste DB Writer Routing API",
            "description": "Waste DB Writer asynchronious processing with celery and RabbitMQ Broker"
        }
    ]

    app = FastAPI(
        openapi_tags=tags_metadata,
        debug=True,
        title="Asynchronous tasks processing with Celery and RabbitMQ",
        summary="",
        version="0.0.1",
        contact={
            "name": "Tannous Geagea",
            "url": "https://wasteant.com",
            "email": "tannous.geagea@wasteant.com",
        },
        openapi_url="/openapi.json",
    )

    origins = [
        "http://localhost:8080",
    ]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_methods=["*"],
        allow_headers=["X-Requested-With", "X-Request-ID"],
        expose_headers=["X-Request-ID"],
    )


    app.celery_app = celery_utils.create_celery()
    app.include_router(event_endpoint.router)
    return app

app = create_app()
celery = app.celery_app

@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    description = exc.args[0]
    return await http_exception_handler(
        request,
        HTTPException(
            500,
            {"code": "generic_exception", "message": description},
            headers={"X-Request-ID": correlation_id.get() or ""},
        ),
    )
    
if __name__ == "__main__":

    uvicorn.run("main:app", host="0.0.0.0", port=int(os.environ.get('EVENT_API_PORT')), log_level="debug", reload=True)
