import os
import json
import time
import math
import django
django.setup()
from django.core.exceptions import ObjectDoesNotExist
from django.db import connection
from django.db.models import Max, F
from django.db.models import Q
from fastapi import status
from datetime import datetime
from datetime import timedelta
from datetime import timezone
from datetime import time as dtime
from typing import Optional, Dict
from typing import Callable
from fastapi import Request
from fastapi import Response
from fastapi import APIRouter
from fastapi import Query
from fastapi import HTTPException
from fastapi.routing import APIRoute
from pydantic import BaseModel, create_model, ValidationError

from acceptance_control.models import (
    Delivery,
    DeliveryERPAttachment,
)

from metadata.models import (
    ERPDataType,
    TenantAttachmentRequirement,
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


description = """
    URL Path: /delivery/erp

    TO DO

"""

@router.api_route(
    "/delivery/erp", methods=["POST"], tags=["Delivery"], description=description,
)
def update_erp_data(
    response: Response,
    delivery_id: str,
    erp_data_type: Dict,
    ):
    results = {}
    try:
        if delivery_id == 'null':
            results['error'] = {
                'status_code': "bad-request",
                'status_description': "delivery_id is not supposed to be null",
                'detail': 'delivery_id is null, please provide a valid delivery_id'
            }
            response.status_code = status.HTTP_400_BAD_REQUEST
            return results
    
        if not Delivery.objects.filter(delivery_id=delivery_id).exists():
            results['error'] = {
                'status_code': "Not-Found",
                'status_description': f"delivery_id {delivery_id} is not found",
                'detail': 'please provide a valid delivery_id'
            }
            response.status_code = status.HTTP_404_NOT_FOUND
            return results
        
        delivery = Delivery.objects.get(delivery_id=delivery_id)
        for key, value in erp_data_type.items():
            if not ERPDataType.objects.filter(name=key).exists():
                results['error'] = {
                    'status_code': "not-found",
                    'status_description': f"ERP data type {key} not register in db yet",
                    'detail': f"ERP data type {key} not register in db yet",
                }
                response.status_code = status.HTTP_404_NOT_FOUND
                return results
            
            erp_attachment_type = ERPDataType.objects.get(
                name=key
            )
            if not TenantAttachmentRequirement.objects.filter(
                tenant=delivery.tenant,
                attachment_type=erp_attachment_type,
            ).exists():
                results['error'] = {
                    'status_code': "not-found",
                    'status_description': f"ERP data type {key} for {delivery.tenant.tenant_name} is not found",
                    'detail': f"ERP data type {key} for {delivery.tenant.tenant_name} is not found",
                }
                response.status_code = status.HTTP_404_NOT_FOUND
                return results
            
            if DeliveryERPAttachment.objects.filter(
                delivery=delivery,
                attachment_type=erp_attachment_type,
            ).exists():
                delivery_erp_attachment = DeliveryERPAttachment.objects.get(
                    delivery=delivery,
                    attachment_type=erp_attachment_type,
                )
                
                delivery_erp_attachment.value = value
            else:
                delivery_erp_attachment = DeliveryERPAttachment(
                    delivery=delivery,
                    attachment_type=erp_attachment_type,
                    value=value,
                )
            
            delivery_erp_attachment.save()
            
        results['data'] = {
            "erp_data_type": erp_data_type
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