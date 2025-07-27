import os
import time
import math
import django
from django.db import connection
from django.db.models import Q
from fastapi import status
from datetime import datetime
from datetime import timedelta
from datetime import timezone
from typing import Callable
from fastapi import Request
from fastapi import Response
from fastapi import APIRouter
from fastapi import HTTPException
from fastapi.routing import APIRoute
from pydantic import BaseModel

django.setup()
from django.core.exceptions import ObjectDoesNotExist

from tenants.models import Tenant

from metadata.models import (
    Language,
    Tag
)

class TimedRoute(APIRoute):
    def get_route_handler(self) -> Callable:
        original_route_handler = super().get_route_handler()
        async def custom_route_handler(request: Request) -> Response:
            before = time.time()
            response: Response = await original_route_handler(request)
            duration = time.time() - before
            response.headers["X-Response-Time"] = str(duration)
            print(f"route duration: {duration}")
            print(f"route response: {response}")
            print(f"route response headers: {response.headers}")
            return response

        return custom_route_handler
    

router = APIRouter(
    route_class=TimedRoute,
)

@router.api_route(
    "/tags/flat", methods=["GET"], tags=["Tags"], description="Returns a flat list of tags with localization."
)
def get_flat_tags_metadata(
    response: Response,
    language: str = "de",
    tenant_domain: str = None  # Optional: future support for tenant-based tag filtering
):
    results = {}

    try:
        # Validate language
        if not Language.objects.filter(code=language).exists():
            results = {
                "error": {
                    "status_code": "not found",
                    "status_description": f"Language '{language}' not supported",
                    "detail": f"Supported languages: {[lang.code for lang in Language.objects.all()]}"
                }
            }
            response.status_code = status.HTTP_404_NOT_FOUND
            return results

        lang = Language.objects.get(code=language)

        # Optional: Validate tenant
        if tenant_domain:
            if not Tenant.objects.filter(domain=tenant_domain).exists():
                results = {
                    "error": {
                        "status_code": "not found",
                        "status_description": f"Tenant '{tenant_domain}' not found",
                        "detail": f"Supported tenants: {[tenant.domain for tenant in Tenant.objects.all()]}"
                    }
                }
                response.status_code = status.HTTP_404_NOT_FOUND
                return results

        # Collect all tags in flat format
        flat_tags = []
        for tag in Tag.objects.all():
            tag_localization = tag.tag_localization.filter(language=lang).first()
            group = tag.group
            group_localization = group.tag_group_localization.filter(language=lang).first() if group else None

            flat_tags.append({
                "id": tag.id,
                "key": tag.name,
                "title": tag_localization.name if tag_localization else tag.name,
                "type": tag.tag_type,
                "color": tag.color,
                "description": tag_localization.description if tag_localization else tag.description,
                "group_id": group.id if group else None,
                "group_name": group_localization.name if group_localization else (group.name if group else None),
            })

        results["tags"] = flat_tags
        results["status_code"] = "ok"
        results["detail"] = "tags retrieved successfully"
        results["status_description"] = "OK"

    except Exception as e:
        results["error"] = {
            "status_code": "server-error",
            "status_description": "Internal Server Error",
            "detail": str(e),
        }
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR

    return results
