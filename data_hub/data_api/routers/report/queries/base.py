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
from common_utils.timezone_utils.timeloc import (
    convert_to_local_time,
)

from metadata.models import (
    Language,
    PlantEntityLocalization,
    TableField,
    TableFieldLocalization,
    TenantAttachmentRequirement,
    FormFieldLocalization,
    FormField
)

from acceptance_control.models import (
    Delivery,
    DeliveryERPAttachment
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
    "/report/delivery/{delivery_id}", methods=["GET"]
)
def get_delivery(
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
        timezone_str = tenant.timezone

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
        table_fields = TableField.objects.all()
        
        col = {}
        for table_field in table_fields:            
            localization = TableFieldLocalization.objects.filter(
                language=language, 
                field=table_field
            ).first()
            
            if not localization:
                continue

            col[table_field.name] = {
                "title": localization.title,
                "type": table_field.type.type,
                "field_key": table_field.name,
                "description": localization.description,
            }
            
        erp_data = {}
        erp_attachments = TenantAttachmentRequirement.objects.filter(tenant=tenant, is_active=True)
        for erp_attachment in erp_attachments:
            erp_localization = erp_attachment.attachment_type.name
            field = TableField.objects.filter(name=erp_attachment.attachment_type.name).first()
            if field:
                erp_localization = TableFieldLocalization.objects.filter(field=field).first()
                erp_localization = erp_localization.title if erp_localization else erp_attachment.attachment_type.name

            if not DeliveryERPAttachment.objects.filter(
                delivery=delivery,
                attachment_type=erp_attachment.attachment_type
            ).exists():
                
                erp_data.update(
                    {   
                        erp_localization: "-",
                    }
                )
                continue

            erp_data.update(
                {
                    erp_localization: DeliveryERPAttachment.objects.get(
                        delivery=delivery,
                        attachment_type=erp_attachment.attachment_type
                    ).value,
                }
            )

        feedback_form_field = FormField.objects.filter(
            name="comment",
        ).first()
        
        comment = {}
        if feedback_form_field:
            feedback_field_localization = FormFieldLocalization.objects.get(
                            field=feedback_form_field, 
                            language=language
                            ).title if FormFieldLocalization.objects.filter(
                                field=feedback_form_field,
                                language=language,
                                ).exists() else feedback_form_field.name
            
            comment.update(
                {
                    feedback_field_localization: "-"
                }
            )

        data = {
            col.get("id", {}).get('title') or "id": delivery.pk,
            # col.get("delivery_id", {}).get('title') or "delivery_id": delivery.delivery_id,
            col.get("delivery_date", {}).get('title') or "delivery_date": convert_to_local_time(utc_time=delivery.created_at, timezone_str=timezone_str).strftime('%Y-%m-%d'),
            col.get("start_time", {}).get('title') or "start_time": convert_to_local_time(utc_time=delivery.delivery_start, timezone_str=timezone_str).strftime("%H:%M:%S"),
            col.get("end_time", {}).get('title') or "end_time": convert_to_local_time(utc_time=delivery.delivery_end, timezone_str=timezone_str).strftime("%H:%M:%S"),
            col.get("location", {}).get('title') or "location": (
                PlantEntityLocalization.objects.get(plant_entity=delivery.entity, language=language).title 
                if PlantEntityLocalization.objects.filter(plant_entity=delivery.entity, language=language).exists() 
                else delivery.delivery_location
            ),
            **erp_data,
            **comment,
        }

        results = {
            "status_code": "success",
            "description": "Delivery data fetched successfully",
            "data": data
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