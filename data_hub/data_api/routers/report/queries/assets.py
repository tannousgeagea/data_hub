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

from tenants.models import (
    TenantStorageSettings
)

from metadata.models import (
    Language,
    PlantEntityLocalization,
    TenantTableAsset,
    TenantTable,
    TableAssetLocalization,
    TableAssetItemLocalization,
    TenantTableAssetItem,
    TableType
)

from acceptance_control.models import (
    Delivery,
    DeliveryMedia,
    AlarmMedia,
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
    

DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
router = APIRouter(
    route_class=TimedRoute,
)

def map_item_assets(delivery_id, item):
    try:
        if "delivery" in item.key:
            return DeliveryMedia.objects.filter(
                delivery__delivery_id=delivery_id, 
                media__media_type=item.media_type
                ).order_by('media__sensor_box__order')
        if "impurity" in item.key:
            return AlarmMedia.objects.filter(
                alarm__delivery_id=delivery_id, 
                alarm__flag_type__name="impurity", 
                media__media_type=item.media_type,
                alarm__exclude_from_dashboard=False,
                )
        else:
            return []
    except Exception as err:
        raise ValueError(f"Error mapping items to assets: {err}")

@router.api_route(
    "/report/delivery/assets/{delivery_id}", methods=["GET"]
)
def get_delivery_assets(
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
        table_assets = TenantTableAsset.objects.filter(
            tenant_table=TenantTable.objects.get(
                tenant=delivery.tenant,
                table_type=TableType.objects.get(name='delivery'),
            ),
            is_active=True,
        )
        
        AzAccoutKey = TenantStorageSettings.objects.get(tenant=delivery.tenant).account_key
        placeholder = {
            'url': f"https://wacoreblob.blob.core.windows.net/amk/placeholder.jpg?{AzAccoutKey}",
            'name': "Bild in Vorbereitung",
            'time': (datetime.now() + timedelta(hours=2)).strftime(DATETIME_FORMAT),
            }
        
        categories = []
        data = []
        
        for table_asset in table_assets:
            categories.append(
                {
                    'key': table_asset.table_asset.key,
                    'name': (
                        TableAssetLocalization.objects.get(asset=table_asset.table_asset, language=language).title 
                        if TableAssetLocalization.objects.filter(asset=table_asset.table_asset, language=language) 
                        else table_asset.table_asset.key
                        ),
                }
            )
            
            items = []
            table_asset_items = TenantTableAssetItem.objects.filter(tenant_table_asset=table_asset, is_active=True, asset_item__media_type="image")
            for item in table_asset_items:
                item = item.asset_item
                medias = map_item_assets(delivery_id=delivery_id, item=item)
                
                items.append(
                    {
                        'key': item.key,
                        'title': (
                            TableAssetItemLocalization.objects.get(asset_item=item, language=language).title 
                            if TableAssetItemLocalization.objects.filter(asset_item=item, language=language) 
                            else item.name
                            ),
                        'type': item.media_type,
                        'data': [
                            {
                                'url': f"{media.media.media_url}?{AzAccoutKey}",
                                'name': media.media.media_name,
                                'time': media.media.created_at.strftime(DATETIME_FORMAT),
                            } for media in medias if media.media.media_type == item.media_type
                        ]
                    },
                )
            
            data.append(
                {
                    "key": table_asset.table_asset.key,
                    "title": (
                        TableAssetLocalization.objects.get(asset=table_asset.table_asset, language=language).title 
                        if TableAssetLocalization.objects.filter(asset=table_asset.table_asset, language=language) 
                        else table_asset.table_asset.key
                        ),
                    "items": items,
                }
            )
        
        
        results = {
            "status": "success",
            "status_description": "Data Fetched successfully",
            "categories": categories,
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