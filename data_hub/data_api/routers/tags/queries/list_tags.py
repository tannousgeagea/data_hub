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
    TagGroup
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
    "/tags", methods=["GET"], description="Returns tag groups and tags with localization."
)
def get_tags_metadata(
    response: Response,
    language: str = "de",
    tenant_domain: str = None  # Optional for future use if tags ever become tenant-scoped
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

        # Optional: Validate tenant (if tenant-scoped logic is needed later)
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

        # Build tag group + tags structure
        tag_groups = []
        for group in TagGroup.objects.all():
            group_localization = group.tag_group_localization.filter(language=lang).first()
            group_name = group_localization.name if group_localization else group.name
            group_description = group_localization.description if group_localization else group.description

            tags = []
            for tag in group.tags.all():
                tag_localization = tag.tag_localization.filter(language=lang).first()
                tag_name = tag_localization.name if tag_localization else tag.name
                tag_description = tag_localization.description if tag_localization else tag.description

                tags.append({
                    "id": tag.id,
                    "key": tag.name,
                    "title": tag_name,
                    "type": tag.tag_type,
                    "color": tag.color,
                    "description": tag_description,
                })

            tag_groups.append({
                "group_id": group.id,
                "group_key": group.name,
                "title": group_name,
                "description": group_description,
                "tags": tags,
            })

        results["tags"] = tag_groups
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
