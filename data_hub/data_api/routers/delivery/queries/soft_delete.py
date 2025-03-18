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
from typing import Optional, Dict
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
    delivery_id: Optional[str] = None
    from_date: Optional[date] = None
    to_date: Optional[date] = None
    location: Optional[str] = None 

@router.api_route(
    "/delivery/soft-delete", methods=["PUT"], tags=["Delivery"],
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

    from_date = request.from_date
    to_date = request.to_date
    today = datetime.today()
    if from_date is None:
        from_date = datetime(today.year, today.month, today.day)
    
    if to_date is None:
        to_date = from_date
        
    from_date = datetime.combine(from_date, dtime.min).replace(tzinfo=timezone.utc)
    to_date = datetime.combine(to_date, dtime.max).replace(tzinfo=timezone.utc)

    filters = {
        "tenant__domain": request.tenant_domain,
        "is_deleted": False,
    }
    if request.location:
        filters["entity__entity_uid"] = request.location



    deleted_count = 0

    if request.delivery_id:
        try:
            delivery = Delivery.objects.get(
                delivery_id=request.delivery_id, 
                **filters
                )
        except Delivery.DoesNotExist:
            raise HTTPException(
                status_code=404,
                detail="Delivery not found or already deleted for the given tenant and entity."
            )
        delivery.is_deleted = True
        delivery.save()
        deleted_count = 1
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