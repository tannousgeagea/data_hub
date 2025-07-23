import os
import json
import time
import math
import django
from django.db import connection
from django.db.models import Q
from fastapi import status
from datetime import datetime
from datetime import timedelta
from datetime import timezone
from datetime import time as dtime
from typing import Callable
from fastapi import Request
from fastapi import Response
from fastapi import APIRouter
from fastapi import HTTPException, Query, Body, Form
from fastapi.routing import APIRoute
from django.db.models import Prefetch
from typing import Dict, List, Optional
from pydantic import BaseModel, Field, create_model, ValidationError
from common_utils.timezone_utils.timeloc import (
    get_location_and_timezone,
    convert_to_local_time,
)

timezone_str = get_location_and_timezone()

django.setup()
from django.core.exceptions import ObjectDoesNotExist
from tenants.models import (
    Tenant,
    EntityType,
    PlantEntity,
    TenantStorageSettings,
)


from acceptance_control.models import (
    Alarm,
    AlarmTag,
    AlarmMedia,
    Severity,
    FlagType,
    FlagTypeLocalization,
    )

from metadata.models import (
    TableType,
    TenantTable,
    Language,
    TenantTableFilter,
    PlantEntityLocalization,
)

def filter_mapping(key, value, tenant):
    try:
        if value is None:
            return None
        
        if key == "severity_level":
            return ("severity", Severity.objects.filter(level=value).first())
        if key == "location":
            return ("entity", PlantEntity.objects.get(entity_uid=value, entity_type__tenant=tenant))
        if key == "flag_type":
            return ("flag_type", FlagType.objects.get(name=value))
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

description = """
    URL Path: /alarm

    TO DO

"""

@router.api_route(
    "/alarm/live", methods=["GET"], tags=["Alarm"], description=description,
)
def get_alarm_notification(
    response: Response, 
    tenant_domain:str,
    severity_level:str="3",
    language:str=None,
    expire:int=120,
    items_per_page:int=15,
    entity_type:str=f"gate"
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
        
        now = datetime.now(tz=timezone.utc)
        before = (now - timedelta(minutes=expire)).replace(tzinfo=timezone.utc)
        
        tenant = Tenant.objects.get(domain=tenant_domain)
        entity_type = EntityType.objects.filter(entity_type=entity_type, tenant=tenant).first()
        if not language:
            lang_code = tenant.default_language
            if lang_code:
                language = lang_code
            else:
                language = 'de'
        
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
        AzAccoutKey = TenantStorageSettings.objects.get(tenant=tenant).account_key
        
        lookup_filters = Q()
        lookup_filters &= Q(ack_status=False)
        lookup_filters &= Q(tenant=tenant)
        lookup_filters &= Q(("severity__level__gte", severity_level))
        lookup_filters &= Q(exclude_from_dashboard=False)
        lookup_filters &= Q(created_at__range=(before, now))
        if entity_type:
            lookup_filters &= Q(entity__entity_type=entity_type)
        
        rows = []
        alarms = Alarm.objects.filter(lookup_filters).order_by('-created_at').prefetch_related(
            Prefetch(
                'alarm_tags',
                queryset=AlarmTag.objects.select_related('tag')
            )
        )
        for alarm in alarms:
            flag_type = alarm.flag_type
            plant_entity = PlantEntity.objects.get(entity_uid=alarm.entity.entity_uid, entity_type__tenant=tenant)
            if not PlantEntityLocalization.objects.filter(
                plant_entity=plant_entity,
                language=language,
            ).exists():
                results['error'] = {
                    'status_code': "non-matching-query",
                    'status_description': f'localization {language.name} not found for {plant_entity.entity_uid}',
                    'detail': f'localization {language.name} not found for {plant_entity.entity_uid}',
                }

                response.status_code = status.HTTP_404_NOT_FOUND
                return results
                  
            if not FlagTypeLocalization.objects.filter(
                flag_type=flag_type,
                language=language
            ).exists():
                results['error'] = {
                    'status_code': "non-matching-query",
                    'status_description': f'localization {language.name} not found for {flag_type.name}',
                    'detail': f'localization {language.name} not found for {flag_type.name}',
                }

                response.status_code = status.HTTP_404_NOT_FOUND
                return results

            plant_entity_localization = PlantEntityLocalization.objects.get(
                plant_entity=PlantEntity.objects.get(entity_uid=alarm.entity.entity_uid, entity_type__tenant=tenant),
                language=language,
            )
            
            flag_type_localization = FlagTypeLocalization.objects.get(
                flag_type=flag_type,
                language=language,
            )
            
            media = AlarmMedia.objects.filter(
                alarm=alarm,
                media__media_type='image'
            ).first()
            
            if not media:
                continue
            
            row = {
                "id": alarm.id,
                "event_uid": alarm.event_uid,
                "event_date": alarm.created_at.strftime('%Y-%m-%d'),
                "timestamp": alarm.timestamp.strftime("%H:%M:%S"),
                "location": plant_entity_localization.title,
                "event_name": flag_type_localization.title,
                "severity_level": alarm.severity.unicode_char,
                "ack_status": alarm.ack_status,
                "url": f"{media.media.media_url}?{AzAccoutKey}",
                "name": media.media.media_name,
                "type": media.media.media_type,
                "tags": [alarm_tag.tag.name for alarm_tag in alarm.alarm_tags.all()],
                # "media": [
                #     {
                #         "url": f"{media.media.media_url}?{AzAccoutKey}",
                #         "name": media.media.media_name,
                #         "type": media.media.media_type,
                #     }   
                # ]
                }
                
            rows.append(
                row
            )
        
        total_record = len(alarms)
        results['data'] = {
            "language": language.name,
            "tenant": tenant.tenant_name,
            "type": "collection",
            "total_record": total_record,
            "user_filters": lookup_filters.children,
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
            "status_code": f"{e.status_code}",
            "status_description": f"{e.detail}",
            "detail": f"{e.detail}",
        }
        
        response.status_code = e.status_code
    
    except Exception as e:
        results['error'] = {
            'status_code': 'server-error',
            "status_description": "Internal Server Error",
            "detail": str(e),
        }
        
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    
    return results


class APIRequest(BaseModel):
    event_uid:str

description = """
    URL Path: /alarm

    TO DO

"""

@router.api_route(
    "/alarm/live", methods=["POST"], tags=["Alarm"], description=description,
)
def update_alarm_status(
    response: Response,
    data: APIRequest,
): 
    results = {}
    try:
        event_uid = data.event_uid
        if event_uid == 'null':
            results['error'] = {
                'status_code': "bad-request",
                'status_description': "delivery_id is not supposed to be null",
                'detail': 'delivery_id is null, please provide a valid delivery_id'
            }
            response.status_code = status.HTTP_400_BAD_REQUEST
            return results
    
        if not Alarm.objects.filter(event_uid=event_uid).exists():
            results['error'] = {
                'status_code': "Not-Found",
                'status_description': f"event_uid {event_uid} is not found",
                'detail': 'please provide a valid delivery_id'
            }
            response.status_code = status.HTTP_404_NOT_FOUND
            return results
            
        alarm = Alarm.objects.get(event_uid=event_uid)
        alarm.ack_status = True
        alarm.save()
        
        results['status_code'] = "ok"
        results["detail"] = "acknowledge status updated successfully"
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
            "status_code": f"{e.status_code}",
            "status_description": f"{e.detail}",
            "detail": f"{e.detail}",
        }
        
        response.status_code = e.status_code
    
    except Exception as e:
        results['error'] = {
            'status_code': 'server-error',
            "status_description": "Internal Server Error",
            "detail": str(e),
        }
        
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    
    return results
