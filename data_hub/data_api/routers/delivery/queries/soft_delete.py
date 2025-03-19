import os
import json
import time
import math
import django
from django.db import connection
from django.db.models import Max, F
from django.db.models import Q
from fastapi import status
from datetime import datetime
from datetime import timedelta
from datetime import timezone
from datetime import date
from datetime import time as dtime
from typing import Optional, Dict, List, Union
from typing import Callable
from fastapi import Request
from fastapi import Response
from fastapi import APIRouter
from fastapi import Query
from fastapi import HTTPException
from fastapi.routing import APIRoute
from pydantic import BaseModel
from asgiref.sync import sync_to_async

django.setup()
from django.core.exceptions import ObjectDoesNotExist
from tenants.models import (
    Tenant,
    PlantEntity,
)

from acceptance_control.models import (
    Delivery,
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



class SoftDeleteRequest(BaseModel):
    tenant_domain: str
    location: Optional[str] = None
    delivery_id: Optional[Union[List[str], str]] = None
    from_date: Optional[datetime] = None
    to_date: Optional[datetime] = None
    location: Optional[str] = None 

description = """
Endpoint: /delivery/soft-delete
Method: PUT

    This endpoint marks one or more Delivery records as deleted by updating their is_deleted field to True (soft deletion). The deletion is restricted to a specified tenant and can be further narrowed by location (i.e., the entity UID), a list of delivery IDs, or a datetime range.
    Request Schema

    The endpoint expects a JSON body conforming to the following schema:
    Field	Type	Required	Description
    tenant_domain	string	Yes	The domain of the tenant. Only deliveries belonging to this tenant will be affected.
    location	string	No	(Optional) The entity UID (location) to narrow the deletion.
    delivery_id	string or List[string]	No	(Optional) One or more specific delivery IDs to delete. If provided, these are used to target specific deliveries.
    from_date	datetime (ISO 8601 format)	No	(Optional) The starting datetime to filter deliveries by their created_at field. If not provided (and no delivery_id), defaults to today.
    to_date	datetime (ISO 8601 format)	No	(Optional) The ending datetime to filter deliveries by their created_at field. If not provided (and no delivery_id), defaults to the end of the day for from_date.

    Note:

        You must provide either a delivery_id (or list of them) or both from_date and to_date.
        If a full datetime (including time information) is provided, that exact range will be used for filtering.
        The filtering is always combined with the tenant (and optionally location) so that only relevant records are updated.

Behavior

    Tenant Validation:
    The API first checks that the provided tenant_domain exists. If not, it returns a 400 error with the available tenant domains.

    Parameter Validation:
    If neither delivery_id nor the pair of from_date and to_date is provided, a 400 error is returned.

    Datetime Defaults:
        If from_date is not provided, it defaults to the start of the current day (midnight) in UTC.
        If to_date is not provided, it defaults to the end of the day for the from_date (23:59:59.999999 in UTC).

        Filtering:
        The query filters on:
            tenant__domain equal to the provided tenant.
            is_deleted is False (only active deliveries are considered).
            If provided, entity__entity_uid equals the supplied location.
            Either matching one or more delivery_id values or deliveries whose created_at falls within the provided datetime range.

        Update Operation:
        The endpoint updates the matching deliveries by setting is_deleted to True and returns the number of records affected.

Example Use Cases

    1. Soft Delete by Specific Delivery ID (Single Value)

        Request:

            {
            "tenant_domain": "example.com",
            "delivery_id": "D12345"
            }

        Behavior:

            The API checks for deliveries with delivery_id "D12345" that belong to tenant example.com and are not yet deleted.
            If found, the delivery is marked as deleted.

        Response:

            {
            "deleted_count": 1,
            "message": "Soft deletion completed successfully."
            }

    2. Soft Delete by Specific Delivery IDs (Multiple Values)

        Request:

            {
            "tenant_domain": "example.com",
            "delivery_id": ["D12345", "D12346", "D12347"]
            }

        Behavior:

            The API fetches deliveries with IDs "D12345", "D12346", and "D12347" for tenant example.com that are not already deleted.
            All matching deliveries are updated with is_deleted = True.

        Response:

            {
            "deleted_count": 3,
            "message": "Soft deletion completed successfully."
            }

    3. Soft Delete by Datetime Range

        Request:

            {
            "tenant_domain": "example.com",
            "from_date": "2025-03-01T00:00:00Z",
            "to_date": "2025-03-31T23:59:59Z"
            }

        Behavior:

            The API deletes all deliveries for tenant example.com that were created between March 1, 2025, and March 31, 2025.
            The created_at field is used for filtering.

        Response:

            {
            "deleted_count": 25,
            "message": "Soft deletion completed successfully."
            }

    4. Soft Delete by Datetime Range with Location Filtering

        Request:

            {
            "tenant_domain": "example.com",
            "location": "LOC_789",
            "from_date": "2025-03-01T08:00:00Z",
            "to_date": "2025-03-01T18:00:00Z"
            }

        Behavior:

            The API applies an additional filter for entity__entity_uid equal to "LOC_789".
            It then deletes all deliveries created on March 1, 2025, between 08:00 and 18:00 UTC that match this location.

        Response:

            {
            "deleted_count": 5,
            "message": "Soft deletion completed successfully."
            }

    5. Error: Missing Both Delivery ID and Date Range

        Request:

            {
            "tenant_domain": "example.com"
            }

        Behavior:

            Since neither a delivery_id nor a date range is provided, the API returns a 400 error.

        Response:

            {
            "detail": "Please provide either a delivery_id or both from_date and to_date."
            }

    6. Error: Unknown Tenant

        Request:

            {
            "tenant_domain": "nonexistent.com",
            "delivery_id": "D12345"
            }

        Behavior:

            The API checks for tenant existence and, if not found, returns a 400 error including the available tenant domains.

        Response:

            {
            "detail": "Tenant nonexistent.com not found! Existing options: [\"example.com\", \"another.com\"]"
            }

"""


@router.api_route(
    "/delivery/soft-delete", methods=["PUT"], tags=["Delivery"], description=description,
)
def soft_delete_deliveries(request: SoftDeleteRequest):
    """
    Soft delete deliveries by marking is_deleted = True.
    
    - tenant_domain is required to ensure only deliveries for that tenant are affected.
    - Optionally, an entity identifier can be provided to narrow the deletion.
    - If delivery_id is provided, soft delete that specific delivery.
    - If a date range (start_date and end_date) is provided, soft delete all deliveries
      for the tenant (and entity if provided) whose delivery_start is within that range.
    """

    if not Tenant.objects.filter(domain=request.tenant_domain).exists():
        raise HTTPException(
            status_code=400,
            detail=f"Tenant {request.tenant_domain} not found ! Existing options: {[tenant.domain for tenant in Tenant.objects.all()]}",

        )

    if not request.delivery_id and not (request.from_date and request.to_date):
        raise HTTPException(
            status_code=400,
            detail="Please provide either a delivery_id or both start_date and end_date."
        )

    if request.from_date is None:
        today = datetime.now(timezone.utc)
        from_date = datetime.combine(today.date(), dtime.min).replace(tzinfo=timezone.utc)
    else:
        from_date = request.from_date

    if request.to_date is None:
        to_date = datetime.combine(from_date.date(), dtime.max).replace(tzinfo=timezone.utc)
    else:
        to_date = request.to_date

    filters = {
        "tenant__domain": request.tenant_domain,
        "is_deleted": False,
    }
    if request.location:
        filters["entity__entity_uid"] = request.location

    deleted_count = 0
    if request.delivery_id:
        try:
            delivery = Delivery.objects.filter(
                delivery_id__in=request.delivery_id, 
                **filters
                )
        except Delivery.DoesNotExist:
            raise HTTPException(
                status_code=404,
                detail="Delivery not found or already deleted for the given tenant and entity."
            )
        deleted_count = delivery.update(is_deleted=True)
    else:
        # Soft delete all deliveries whose delivery_start falls within the date range
        queryset = Delivery.objects.filter(
            created_at__range=(from_date, to_date),
            **filters

        )
        deleted_count = queryset.update(is_deleted=True)

    return {
        "deleted_count": deleted_count,
        "message": "Soft deletion completed successfully."
    }