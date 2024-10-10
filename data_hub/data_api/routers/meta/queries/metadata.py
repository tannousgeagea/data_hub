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
    TableType,
    TenantTable,
    TenantTableField,
    TableFieldLocalization,
)

from metadata.models import (
    TableFilter,
    FilterLocalization,
    FilterItem,
    FilterItemLocalization,
    TenantTableFilter,
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

URL Path: /delivery/metadata

    The {language} path parameter specifies the language in which the metadata and filter localization should be returned. Example values could be "de" for German or "en" for English.

Parameters:

    language (required): The language code for retrieving metadata and filter localizations.
    metadata_id (optional, default is 1): The ID of the metadata for which data should be retrieved.

Responses:

    Success (HTTP 200):
        Returns a dictionary containing:
            columns: A list of column metadata, including localized title, type, and description.
            filters: A list of filters, including localized filter names, types, descriptions, and filter items.
            primary_key: The primary key of the Metadata object for the given metadata_id.
        Includes a status code "ok" and detailed success message.

    Error Responses (HTTP 404):
        Metadata Not Found: If no metadata is found for the given metadata_id, the response returns an error indicating that the metadata was not found.
        Language Localization Not Found: If no localization exists for the specified language, the response includes an error message specifying that the localization for that language is missing.
        Filter Items Not Found: If active filter items or their localizations for a given filter are missing, an error response is returned with details.

    Error Responses (HTTP 500):
        If an unexpected error occurs, a generic server error with status code 500 is returned, with details about the error.

"""

@router.api_route(
    "/{table_type}/metadata", methods=["GET"], tags=["Metadata"], description=description,
)
def get_metadata(
    response: Response, 
    tenant_domain:str, 
    table_type:str,
    language:str="de",
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


        if not TableType.objects.filter(name=table_type).exists():
            results = {
                "error": {
                    "status_code": "not found",
                    "status_description": f"Table {table_type} not found",
                    "detail": f"Table {table_type} not found ! Existing options: {[table_type.name for table_type in TableType.objects.all()]}",
                }
            }
            
            response.status_code = status.HTTP_404_NOT_FOUND
            return results
        
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

        col = {}
        table_type = TableType.objects.get(name=table_type)
        tenant = Tenant.objects.get(domain=tenant_domain)
        
        if not TenantTable.objects.filter(table_type=table_type, tenant=tenant).exists():
            results = {
                "error": {
                    "status_code": "not found",
                    "status_description": f"Table {table_type} for Tenant {tenant_domain} not found",
                    "detail": f"Table {table_type} for Tenant {tenant_domain} not found",
                }
            }
            
            response.status_code = status.HTTP_404_NOT_FOUND
            return results
        
        tenant_table = TenantTable.objects.get(table_type=table_type, tenant=tenant)
        lang = Language.objects.get(
            code=language
        )
        
        table_fields = TenantTableField.objects.filter(
            tenant_table=tenant_table,
        ).order_by('field_order')
        
        for table_field in table_fields:
            if not TableFieldLocalization.objects.filter(language=lang, field=table_field.field).exists():
                results = {
                    "error": {
                        "status_code": "not found",
                        "status_description": f"language {language} ({lang.name}) for filed {table_field.field.name} not found",
                        "deatil": f"language {language} ({lang.name}) for filter item {table_field.field.name} not found",
                        }
                    }
            
                response.status_code = status.HTTP_404_NOT_FOUND
                return results 
            
            localization = TableFieldLocalization.objects.get(
                language=lang, 
                field=table_field.field
                )
            
            col[table_field.field.name] = {
                "title": localization.title,
                "type": table_field.field.type.type,
                "description": localization.description,
            }
        
        
        print('hello')
        tenant_table_filters = TenantTableFilter.objects.filter(
            tenant_table=tenant_table
        )
        
        filters = {}
        for tenant_table_filter in tenant_table_filters:
            if not FilterLocalization.objects.filter(
                language=lang,
                table_filter=tenant_table_filter.table_filter,
            ).exists():
                results = {
                    "error": {
                        "status_code": "not found",
                        "status_description": f"language {language} ({lang.name}) for filter {tenant_table_filter.table_filter.filter_name} not found",
                        "deatil": f"language {language} ({lang.name}) for filter item {tenant_table_filter.table_filter.filter_name} not found",
                        }
                    }
            
                response.status_code = status.HTTP_404_NOT_FOUND
                return results 
            
            localization = FilterLocalization.objects.get(
                language=lang,
                table_filter=tenant_table_filter.table_filter
            )
            
            filters[tenant_table_filter.table_filter.filter_name] = {
                "title": localization.title,
                "type": tenant_table_filter.table_filter.type,
                "description": localization.description,
                "placeholder": localization.placeholder,
            }

            filter_items = FilterItem.objects.filter(
                table_filter=tenant_table_filter.table_filter
            ).order_by('field_order')
        
            filters[tenant_table_filter.table_filter.filter_name].update(
                {  
                    'default': filter_items.first().item_key,
                    'items': {
                        filter_item.item_key: FilterItemLocalization.objects.get(
                            language=lang, filter_item=filter_item
                            ).item_value
                        for filter_item in filter_items
                        if FilterItemLocalization.objects.filter(language=lang, filter_item=filter_item).exists()
                    }
                }
            )
                
                
        results['metadata'] = {
            "columns": col,
            "filters": filters,
            "primary_key": table_fields.first().field.name if table_fields.first() else None,
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