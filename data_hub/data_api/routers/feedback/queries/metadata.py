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
    FeedbackForm,
    FeedbackFormField,
    FeedbackFormFieldItem,
    TenantFeedbackForm,
    FormFieldLocalization,
    FeedbackFormFieldItemLocalization,
    TagGroup, Tag, TagGroupLocalization, TagLocalization
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
    "/feedback/{feedback_type}/metadata", methods=["GET"], tags=["Feedback"], description=description,
)
def get_metadata(
    response: Response, 
    tenant_domain:str,
    feedback_type:str,
    language:str=None,
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

        if not FeedbackForm.objects.filter(name=feedback_type).exists():
            results = {
                "error": {
                    "status_code": "not found",
                    "status_description": f"Feedback Form {feedback_type} not found",
                    "detail": f"Feedback Form {feedback_type} not found ! Existing options: {[feedback_form.name for feedback_form in FeedbackForm.objects.all()]}",
                }
            }
            
            response.status_code = status.HTTP_404_NOT_FOUND
            return results
        
        feedback_form = FeedbackForm.objects.get(name=feedback_type)
        tenant = Tenant.objects.get(domain=tenant_domain)
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
    
        if not TenantFeedbackForm.objects.filter(feedback_form=feedback_form, tenant=tenant).exists():
            results = {
                "error": {
                    "status_code": "not found",
                    "status_description": f"Feedback Form {feedback_form} for Tenant {tenant_domain} not found",
                    "detail": f"Feedback Form {feedback_form} {tenant_domain} not found",
                }
            }
            
            response.status_code = status.HTTP_404_NOT_FOUND
            return results
        
        tenant_feedback_form = TenantFeedbackForm.objects.get(feedback_form=feedback_form, tenant=tenant)
        lang = Language.objects.get(
            code=language
        )
        
        feedback_form_fields = FeedbackFormField.objects.filter(
            form=tenant_feedback_form.feedback_form,
            is_active=True
        ).order_by('field_order__field_position')
        
        results['metadata'] = {
            "fields": [
                {
                    "field_key": feedback_form_field.form_field.name,
                    "title": FormFieldLocalization.objects.get(
                        field=feedback_form_field.form_field, 
                        language=lang
                        ).title if FormFieldLocalization.objects.filter(
                            field=feedback_form_field.form_field,
                            language=lang,
                            ).exists() else feedback_form_field.form_field.name,
                    
                    "type": feedback_form_field.form_field.type.type,
                    
                    "description": FormFieldLocalization.objects.get(
                        field=feedback_form_field.form_field, 
                        language=lang
                        ).description if FormFieldLocalization.objects.filter(
                            field=feedback_form_field.form_field,
                            language=lang,
                            ).exists() else feedback_form_field.form_field.description,
                    
                    "placeholder": FormFieldLocalization.objects.get(
                        field=feedback_form_field.form_field, 
                        language=lang
                        ).placeholder if FormFieldLocalization.objects.filter(
                            field=feedback_form_field.form_field,
                            language=lang,
                            ).exists() else '',
                    
                    "items": [
                        {
                            "key": field_item.item_key,
                            "value": FeedbackFormFieldItemLocalization.objects.get(
                                field_item=field_item, 
                                language=lang
                                ).title if FeedbackFormFieldItemLocalization.objects.filter(
                                    field_item=field_item, 
                                    language=lang
                                    ).exists() else field_item.item_key,
                                
                            "color": field_item.color, 
                        } for field_item in FeedbackFormFieldItem.objects.filter(
                            field=feedback_form_field.form_field,
                        )
                    ]   
                } for feedback_form_field in feedback_form_fields 
            ]
        }

        # Add tags grouped by TagGroup
        tag_groups = []
        for group in TagGroup.objects.all():
            group_localization = group.tag_group_localization.filter(language=lang).first()
            group_name = group_localization.name if group_localization else group.name
            group_description = group_localization.description if group_localization else group.description

            tags = []
            for tag in group.tags.all():
                tag_localization = tag.tag_localization.filter(language=lang).first()
                tag_name = tag_localization.name if tag_localization else tag.name
                tag_description = tag_localization.description if tag_localization else tag.description

                tags.append({
                    "id": tag.id,
                    "key": tag.name,
                    "title": tag_name,
                    "type": tag.tag_type,
                    "color": tag.color,
                    "description": tag_description,
                })

            tag_groups.append({
                "group_id": group.id,
                "group_key": group.name,
                "title": group_name,
                "description": group_description,
                "tags": tags,
            })

        results["metadata"]["tags"] = tag_groups
        results['status_code'] = "ok"
        results["detail"] = "metadata retrieved successfully"
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