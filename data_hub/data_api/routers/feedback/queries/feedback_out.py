
import os
import time
import math
import django
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
from acceptance_control.models import (
    Alarm,
    AlarmFeedback,
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
    responses={404: {"description": "Not found"}},
)

description = """

    GET /feedback/alarm/{event_uid}
    Overview

    This API endpoint retrieves feedback for a specific alarm identified by its event_uid. It provides detailed information about the feedback, including its validity, severity, and any associated metadata. If no feedback has been provided yet, the API returns a placeholder response indicating that feedback is unavailable.
    Features

        Retrieve Feedback: Returns detailed feedback for a specific alarm if available.
        Handle Missing Feedback: Responds gracefully with a placeholder if feedback has not been provided yet.
        Error Handling: Provides appropriate responses for invalid or missing event_uid.

    Request

        Method: GET
        Endpoint: /feedback/alarm/{event_uid}
        Path Parameter:
            event_uid (string, required): The unique identifier for the alarm.

    Response

        Success:
            200 OK: Returns alarm feedback details or a placeholder if feedback is missing.

        Response Body Example (Feedback Exists):

            {
                "data": {
                    "alarm_id": 1,
                    "event_uid": "alarm123",
                    "feedback": {
                        "is_actual_alarm": true,
                        "rating": 3,
                        "comment": "Large object detected.",
                        "meta_info": {"object_type": "sofa", "size": "large"},
                        "timestamp": "2025-01-03T12:00:00Z",
                        "updated_at": "2025-01-03T12:30:00Z"
                    }
                },
                "status_code": "ok",
                "status_description": "Feedback retrieved successfully."
            }

        Response Body Example (Feedback Missing):

            {
                "data": {
                    "alarm_id": 1,
                    "event_uid": "alarm123",
                    "feedback": null,
                    "status_description": "No feedback provided yet for this alarm."
                },
                "status_code": "ok"
            }

        Errors:

            404 Not Found: If the event_uid does not correspond to any alarm.

                {
                    "error": {
                        "status_code": "not-found",
                        "status_description": "Alarm with event_uid alarm123 not found",
                        "detail": "Please provide a valid event_uid."
                    }
                }

            500 Internal Server Error: For unexpected issues.

                {
                    "error": {
                        "status_code": "server-error",
                        "status_description": "Internal Server Error",
                        "detail": "An unexpected error occurred."
                    }
                }

"""

@router.api_route(
    "/feedback/alarm/{event_uid}", methods=["GET"], tags=["Feedback"], description=description,
)
def get_feedback(response: Response, event_uid:str):
    results = {}
    try:
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
                'detail': 'please provide a valid event UID'
            }
            response.status_code = status.HTTP_404_NOT_FOUND
            return results
        
        alarm = Alarm.objects.get(event_uid=event_uid)
        if not AlarmFeedback.objects.filter(alarm=alarm).exists():
            results['data'] = {
                "alarm_id": alarm.id,
                "event_uid": alarm.event_uid,
                "feedback": None,
                "status_description": "No feedback provided yet for this alarm.",
            }
            results['status_code'] = "ok"
            response.status_code = status.HTTP_200_OK
            return results
        
        feedback = AlarmFeedback.objects.filter(alarm=alarm).first()
        results['data'] = {
            "alarm_id": alarm.id,
            "event_uid": alarm.event_uid,
            "feedback": {
                "is_actual_alarm": feedback.is_actual_alarm,
                "rating": feedback.rating.level if feedback.rating else None,
                "comment": feedback.comment,
                "meta_info": feedback.meta_info,
                "timestamp": feedback.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                "updated_at": feedback.updated_at.strftime('%Y-%m-%d %H:%M:%S'),
                "user": feedback.user_id,
            },
        }
        
        results['status_code'] = "ok"
        results['status_description'] = "Feedback retrieved successfully."
        
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