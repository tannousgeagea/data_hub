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
from common_utils.timezone_utils.timeloc import (
    get_location_and_timezone,
    convert_to_local_time,
)

timezone_str = get_location_and_timezone()

from metadata.models import (
    Language,
    PlantEntityLocalization
)

from acceptance_control.models import (
    Delivery,
    TenantFlagDeployment,
    DeliveryFlag,
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
    "/report/delivery/flags/{delivery_id}", methods=["GET"]
)
def get_delivery_flags(
    response:Response,
    delivery_id:str,
    language:Optional[str] = None,
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
        tenant = delivery.tenant
        if not language:
            lang_code = tenant.default_language
            if lang_code:
                language = lang_code
                msg = f'using default language: {language}'
            else:
                language = 'de'
                msg = f"using german language"
        
        if not Language.objects.filter(code=language).exists():
            results = {
                "error": {
                    "status_code": "not found",
                    "status_description": f"Given Language {language} not supported",
                    "detail": f"Given Language {language} not supported! Supported Language: {[lang.name for lang in Language.objects.all()]}",
                }
            }    
            response.status_code = status.HTTP_404_NOT_FOUND
            return results
        
        language = Language.objects.get(code=language)
        flags_deployment = TenantFlagDeployment.objects.filter(tenant=tenant)
        
        data = []
        for flag in flags_deployment:
            flags = DeliveryFlag.objects.filter(
                delivery=delivery,
                flag_type=flag.flag_type,
                exclude_from_dashboard=False,
            ).annotate(
                max_severity=Max('severity__level')
            ).filter(
                severity__level=F('max_severity')
            )
            
            if not flags.exists():
                data.append(
                    {
                        "flag": flag.flag_type.name, 
                        "value": '🟩',
                        "color": "#00FF00",
                    }
                )
                
                continue
            
            flag = flags.last()
            for flag_ in flags:
                if flag_.severity.level > flag.severity.level:
                        flag = flag_

            data.append(
                {
                    "flag": flag.flag_type.name,
                    "value": flag.severity.unicode_char,
                    "color": flag.severity.color_code
                }
            )

        results = {
            "status_code": "success",
            "status_description": "Data fetched successfully",
            "data": data,
        }

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
    