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
from acceptance_control.models import Delivery, DeliveryFlag, TenantFlagDeployment

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

description = """
    URL Path: /delivery

    TO DO

"""

@router.api_route(
    "/delivery", methods=["GET"], tags=["Delivery"], description=description,
)
def get_delivery_data(
    response: Response, 
    tenant_domain:str,
    location:str='all',
    from_date:datetime=None,
    to_date:datetime=None,
    items_per_page:int=15,
    page:int=1,
    ):
    results = {}
    try:
        if not Tenant.objects.filter(domain=tenant_domain).exists():
            results = {
                "error": {
                    "status_code": "not found",
                    "status_description": f"Tenant {tenant_domain} not found",
                    "detail": f"Tenant {Tenant} not found ! Existing options: {[tenant.domain for tenant in Tenant.objects.all()]}",
                }
            }
            
            response.status_code = status.HTTP_404_NOT_FOUND
            return results
        
        today = datetime.today()
        if from_date is None:
            from_date = datetime(today.year, today.month, today.day)
        
        if to_date is None:
            to_date = from_date + timedelta(days=1)
            
        from_date = from_date.replace(tzinfo=timezone.utc)
        to_date = to_date.replace(tzinfo=timezone.utc) + timedelta(days=1)
        
        
        if page < 1:
            page = 1
        
        if items_per_page<=0:
            results['error'] = {
                'status_code': 400,
                'status_description': f'Bad Request, items_per_pages should not be 0',
                'detail': "division by zero."
            }

            response.status_code = status.HTTP_400_BAD_REQUEST    
            return results
        
        tenant = Tenant.objects.get(domain=tenant_domain)
        lookup_filters = Q()
        lookup_filters &= Q(tenant=tenant)
        lookup_filters &= Q(created_at__range=(from_date, to_date ))
        if not location=='all':
            lookup_filters &= Q(delivery_location=location)
        
        deliveries = Delivery.objects.filter(lookup_filters).order_by('-created_at')
        rows = []
        total_record = len(deliveries)
        for delivery in deliveries[(page - 1) * items_per_page:page * items_per_page]:
            row = {
                "id": delivery.id,
                "delivery_id": str(delivery.id).zfill(6),
                "delivery_date": delivery.created_at.strftime('%Y-%m-%d'),
                "start_time": delivery.delivery_start.strftime("%H:%M:%S"),
                "end_time": delivery.delivery_end.strftime("%H:%M:%S"),
                "location": delivery.delivery_location,
                }


            flags_deployment = TenantFlagDeployment.objects.filter(tenant=tenant)
            for flag in flags_deployment:
                flags = DeliveryFlag.objects.filter(delivery=delivery, flag_type=flag.flag_type)
                if not flags:
                    row.update(
                        {
                            flag.flag_type.name: '⬜',
                        }
                    )
                    
                    continue
                
                for flag in flags:
                    row.update(
                        {
                            flag.flag_type.name: flag.severity.unicode_char
                        }
                    )
                
            rows.append(
                row
            )
        
        results['data'] = {
            "type": "collection",
            "total_record": total_record,
            "filters": lookup_filters,
            "pages": math.ceil(total_record / items_per_page),
            "items": rows,
        }
        results['status_code'] = "ok"
        results["detail"] = "data retrieved successfully"
        results["status_description"] = "OK"
    
        
    except ObjectDoesNotExist as e:
        results['error'] = {
            'status_code': "non-matching-query",
            'status_description': f'Matching query was not found',
            'detail': f"matching query does not exist. {e}"
        }

        response.status_code = status.HTTP_404_NOT_FOUND
        
    except HTTPException as e:
        results['error'] = {
            "status_code": "not found",
            "status_description": "Request not Found",
            "detail": f"{e}",
        }
        
        response.status_code = status.HTTP_404_NOT_FOUND
    
    except Exception as e:
        results['error'] = {
            'status_code': 'server-error',
            "status_description": "Internal Server Error",
            "detail": str(e),
        }
        
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    
    return results