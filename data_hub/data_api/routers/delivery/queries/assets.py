
import os
import math
import time
import django
django.setup()
from django.db import connection
from datetime import datetime, timedelta
from datetime import date, timezone
from typing import Callable
from fastapi import Request
from fastapi import Response
from fastapi import APIRouter
from fastapi import HTTPException
from fastapi.responses import JSONResponse
from fastapi.routing import APIRoute
from fastapi import status
from pydantic import BaseModel
from typing import Dict, List, Optional
from acceptance_control.models import (
    Delivery,
    Media, 
    DeliveryFlag, 
    DeliveryMedia,
    )

DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"

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

This API endpoint is designed to retrieve detailed information related to a delivery identified by delivery_id. Here's a breakdown of its functionality:
Endpoint Definition

python

@router.api_route(
    "/delivery/assets/{delivery_id}", methods=["GET"], tags=["Delivery"]
)

    Route: /delivery/assets/{delivery_id}
    Methods: GET
    Tags: ["Delivery"]
    Parameters:
        delivery_id: Path parameter representing the unique identifier of the delivery.

Functionality

    Input Validation:
        Checks if delivery_id is 'null'. If true, returns a 400 Bad Request response indicating that delivery_id cannot be null.
        Checks if delivery_id is not a digit. If true, returns a 400 Bad Request response indicating that delivery_id should be a number.

    Existence Check:
        Queries the database (DeliveryState model) to verify if a delivery with the specified delivery_id exists. If not found, returns a 404 Not Found response indicating that the delivery was not found.

    Successful Response:
        If the delivery_id is valid and exists, constructs a detailed response containing:
            Information about the delivery ('delivery' section).
            Analytics related to the delivery ('analytics' section), including querying external APIs (query_impurity_by_delivery, query_staub_by_delivery, query_hotspot_by_delivery).
            Additional information ('information' section) related to the delivery, such as comments and additional data.

    Error Handling:
        Catches exceptions:
            HTTPException: Specifically catches and handles HTTP exceptions, setting a 404 Not Found status code.
            General Exception: Catches any other unexpected errors, setting a 500 Internal Server Error status code and providing details of the error in the response.

Response Structure

    Success Response (200 OK):
        Detailed JSON structure containing sections for delivery details, analytics, and additional information.

    Error Responses:
        400 Bad Request: When delivery_id is 'null' or not a digit.
        404 Not Found: When the specified delivery_id does not exist in the database or when caught HTTPException.
        500 Internal Server Error: For any other unexpected errors, providing details of the error in the response.

Usage

This API is used to fetch comprehensive information and analytics related to a specific delivery identified by delivery_id, integrating with external analytics APIs to provide enriched data about the delivery process.

"""


@router.api_route(
    "/delivery/assets/{delivery_id}", methods=["GET"], tags=["Delivery"], description=description,
)
def get_delivery_assets(response: Response, delivery_id:str):
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
        
        # if not delivery_id.isdigit():
        #     results['error'] = {
        #         'status_code': "bad-request",
        #         'status_description': f"delivery_id is expected a number but got {delivery_id}",
        #         'detail': 'delivery_id is null, please provide a valid delivery_id'
        #     }
        #     response.status_code = status.HTTP_400_BAD_REQUEST
        #     return results
    
        if not Delivery.objects.filter(delivery_id=delivery_id).exists():
            results['error'] = {
                'status_code': "Not-Found",
                'status_description': f"delivery_id {delivery_id} is not found",
                'detail': 'please provide a valid delivery_id'
            }
            response.status_code = status.HTTP_404_NOT_FOUND
            return results
            
        delivery = Delivery.objects.get(delivery_id=delivery_id)
        delivery_media = DeliveryMedia.objects.filter(delivery=delivery)
        
        for media in delivery_media:
            media.media.media_url
        
        results['categories'] = [
            {
                'key': 'preview',
                'name': "Nachshau",
            },
            {
                'key': 'analytics',
                'name': "Auffälligkeiten",
            },
        ]
        
        results['data'] = [
            {
                'title': "Nachschau",
                "key":"preview",
                'items': [
                    {
                        'title': 'Aktivität',
                        "key":"snapshots",
                        'type': 'image',
                        'data': [
                            {
                                'url': media.media.media_url,
                                'name': media.media.media_name,
                                'time': media.media.created_at.strftime(DATETIME_FORMAT),
                            } for media in delivery_media if media.media.media_type == "image"
                        ]
                    },
                    {
                        'title': 'Zeitrafferaufnahme',
                        "key":"videos",
                        'type': 'video',
                        'data': [
                            {
                                'url': media.media.media_url,
                                'name': media.media.media_name,
                                'time': media.media.created_at.strftime(DATETIME_FORMAT),
                            } for media in delivery_media if media.media.media_type == "video"
                        ]
                    }
                ]
            },
            {
                "title": "Auffälligkeiten",
                "key": 'analytics',
                "items": [
                    {
                        "title": "Prob. Langteile Aufnahme",
                        "key": "impurity_snapshots",
                        "type": "image",
                        "data": [
                            {
                                'url': media.media.media_url,
                                'name': media.media.media_name,
                                'time': media.media.created_at.strftime(DATETIME_FORMAT),
                            } for media in delivery_media if media.media.media_type == "image"
                        ]
                    },
                ]
            },
        ]

        return results    
    
    except HTTPException as e:
        results['error'] = {
            "status_code": 404,
        }
        
        response.status_code = status.HTTP_404_NOT_FOUND
        return results
    
    except Exception as e:
        results['error'] = {
            'status_code': 500,
            "status_description": "Internal Server Error",
            "detail": str(e),
        }
        
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return results