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

django.setup()
from django.core.exceptions import ObjectDoesNotExist
from tenants.models import (
    Tenant,
    PlantEntity,
)

from acceptance_control.models import (
    Delivery, 
    DeliveryFlag, 
    TenantFlagDeployment,
    Severity,
    FlagType,
    FlagTypeLocalization,
    DeliveryERPAttachment,
    )

from metadata.models import (
    TableType,
    TenantTable,
    Language,
    TenantTableFilter,
    PlantEntityLocalization,
    TenantAttachmentRequirement,
)


def filter_mapping(key, value, tenant):
    try:
        if value is None:
            return None

        if value == "all":
            return None
        
        if key == "severity_level":
            return ("flags__severity__level__gte", value) #Severity.objects.filter(level=value).first())
        if key == "location":
            return ("entity", PlantEntity.objects.get(entity_uid=value, entity_type__tenant=tenant))
        if key == "flag_type":
            return ("flags__flag_type", FlagType.objects.get(name=value))
    except Exception as err:
        raise ValueError(f"Failed to map filter value {value} filter {key}: {err}")

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

def create_filter_model(fields: Dict[str, Optional[str]]):
    """
    This function creates a dynamic Pydantic model based on the fields provided,
    without setting default values.
    """
    return create_model("DynamicFilterModel", **{k: (Optional[str], None) for k in fields})

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
    user_filters: Optional[str] = Query(None),
    from_date:datetime=None,
    to_date:datetime=None,
    items_per_page:int=15,
    page:int=1,
    language:str='de',
    ):
    results = {}
    try:
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
        
        filters_dict = {}
        if user_filters:
            try:
                filters_dict = json.loads(user_filters)
            except json.JSONDecodeError:
                raise HTTPException(status_code=400, detail="Invalid JSON format for user_filters")

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
        
        if not TableType.objects.filter(name='delivery').exists():
            results = {
                "error": {
                    "status_code": "not found",
                    "status_description": f"Table Type alarm not found",
                    "detail": f"Table Type alarm not found ! Existing options: {[table_type.name for table_type in TableType.objects.all()]}",
                }
            }
            
            response.status_code = status.HTTP_404_NOT_FOUND
            return results
        
        language = Language.objects.get(code=language)
        table_type = TableType.objects.get(name='delivery')
        tenant = Tenant.objects.get(domain=tenant_domain)
        
        today = datetime.today()
        if from_date is None:
            from_date = datetime(today.year, today.month, today.day)
        
        if to_date is None:
            to_date = from_date
            
        from_date = from_date.replace(tzinfo=timezone.utc)
        to_date = datetime.combine(to_date, dtime.max).replace(tzinfo=timezone.utc)
        
        
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
        
        tenant_table = TenantTable.objects.get(
            tenant=tenant,
            table_type=table_type
        )
        
        tenant_table_filter = TenantTableFilter.objects.filter(
            tenant_table=tenant_table,
            is_active=True
        )
        
        filter_fields = {
            fil.table_filter.filter_name: '' for fil in tenant_table_filter
        }
        
        
        DynamicFilterModel = create_filter_model(filter_fields)
        try:
            validated_filters = DynamicFilterModel(**filters_dict)
        except ValidationError as e:
            results['error'] = {
                "status_code": 422,
                "detail": f"{e.errors()}"
            }
            
            response.status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
            return results
        
        lookup_filters = Q()
        lookup_filters &= Q(tenant=tenant)
        lookup_filters &= Q(created_at__range=(from_date, to_date ))
        for key, value in validated_filters:
            filter_map = filter_mapping(key, value, tenant=tenant)
            if filter_map:
                lookup_filters &= Q(filter_map) 
        
        language = Language.objects.get(code='de')
        deliveries = Delivery.objects.filter(lookup_filters).order_by('-created_at').distinct()
        
        filtered_deliveries =  []
        ongoing = []
        for delivery in deliveries:
            delivery_status = "done"
            duration = (delivery.delivery_end - delivery.delivery_start).seconds
            if duration < 3:
                delivery_status = "ongoing"
            elif duration <30:
                continue
            
            filtered_deliveries.append(delivery)
            ongoing.append(delivery_status)

        deliveries = filtered_deliveries

        rows = []
        total_record = len(deliveries)
        for i, delivery in enumerate(deliveries[(page - 1) * items_per_page:page * items_per_page]):
            row = {
                "id": delivery.id,
                "delivery_id": delivery.delivery_id,
                "delivery_date": convert_to_local_time(utc_time=delivery.created_at, timezone_str=timezone_str).strftime('%Y-%m-%d'),
                "start_time": convert_to_local_time(utc_time=delivery.delivery_start, timezone_str=timezone_str).strftime("%H:%M:%S"),
                "end_time": convert_to_local_time(utc_time=delivery.delivery_end, timezone_str=timezone_str).strftime("%H:%M:%S") if ongoing[i] == "done" else "-",
                "location": PlantEntityLocalization.objects.get(plant_entity=delivery.entity, language=language).title if PlantEntityLocalization.objects.filter(plant_entity=delivery.entity, language=language).exists() else delivery.delivery_location,
                }


            flags_deployment = TenantFlagDeployment.objects.filter(tenant=tenant)
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
                    row.update(
                        {
                            flag.flag_type.name: '🟩',
                        }
                    )
                    
                    continue
                
                flag = flags.last()
                for flag_ in flags:
                    if flag_.severity.level > flag.severity.level:
                            flag = flag_

                row.update(
                    {
                        flag.flag_type.name: flag.severity.unicode_char
                    }
                )
            
            erp_attachments = TenantAttachmentRequirement.objects.filter(tenant=tenant, is_active=True)
            for erp_attachment in erp_attachments:
                if not DeliveryERPAttachment.objects.filter(
                    delivery=delivery,
                    attachment_type=erp_attachment.attachment_type
                ).exists():
                    row.update(
                        {
                            erp_attachment.attachment_type.name: "⬛",
                        }
                    )
                    continue
                
                row.update(
                    {
                        erp_attachment.attachment_type.name: DeliveryERPAttachment.objects.get(
                            delivery=delivery,
                            attachment_type=erp_attachment.attachment_type
                        ).value,
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
