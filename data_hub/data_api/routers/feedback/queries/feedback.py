
import os
import time
import math
import django
from django.db.models import Q
from fastapi import status
from datetime import datetime
from datetime import timedelta
from datetime import timezone
from typing import Callable
from typing import Optional, Dict
from fastapi import Depends, Body
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
    Severity,
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

    Endpoint: POST /alarm/feedback/{event_uid}
    Description:

    This API endpoint allows users to provide feedback for a specific alarm identified by its event_uid. 
    Feedback can include information about whether the alarm is valid, its severity rating, comments, and additional metadata. 
    If the feedback indicates the alarm is not valid, it will no longer appear in the dashboard.
    Features:

        Submit new feedback or update existing feedback for an alarm.
        Indicate if the alarm is valid (is_actual_alarm).
        Optionally adjust the alarm severity (rating) and provide a comment.
        Attach metadata to enrich feedback (meta_info).

    Parameters:
        Path Parameter:

        . event_uid (string, required):
            A unique identifier for the alarm. Must not be null.

        Request Body:

        A JSON object with the following optional fields:
        Field	            Type	Required	                Description
        ----------------------------------------------------------------------------------------------------------------------------
        user_id	            string	    No	                    Identifier of the user providing feedback.
        comment	            string	    No	                    Optional comment to explain the feedback.
        rating	            integer	    No	                    Severity rating for the alarm. Must align with the alarm's flag type.
        meta_info           object	    No	                    Additional metadata related to the feedback.
        is_actual_alarm	    boolean	    Yes (for new feedback)	Indicates whether the alarm is valid.
        ----------------------------------------------------------------------------------------------------------------------------
        Responses:

            200 OK: Feedback was recorded successfully.

            {
                "status_code": "ok",
                "detail": "Feedback recorded successfully",
                "status_description": "OK"
            }

            400 Bad Request: Invalid or missing input.

            {
                "error": {
                    "status_code": "bad-request",
                    "status_description": "Invalid or missing input",
                    "detail": "Missing required field: is_actual_alarm"
                }
            }

            404 Not Found: Alarm or related data was not found.

            {
                "error": {
                    "status_code": "not-found",
                    "status_description": "Alarm not found",
                    "detail": "Matching query does not exist."
                }
            }

            500 Internal Server Error: An unexpected error occurred.

"""
class Request(BaseModel):
    user_id:Optional[str] = None
    comment:Optional[str] = None
    rating:Optional[int] = None
    meta_info:Optional[Dict] = None
    is_actual_alarm:Optional[bool] = None

@router.api_route(
    "/feedback/alarm/{event_uid}", methods=["POST"], tags=["Feedback"], description=description,
)
def insert_feedback(response: Response, event_uid:str, request:Request = Body()):
    results = {}
    try:
        
        exists = False
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
        
        user_id = request.user_id
        if not AlarmFeedback.objects.filter(alarm=alarm, user_id=user_id).exists():
            if request.is_actual_alarm is None:
                results['error'] = {
                    'status_code': "Bad Request",
                    'status_description': f"Missing required field: is_actual_alarm",
                    'detail': f"Missing required field: is_actual_alarm",
                }
                response.status_code = status.HTTP_400_BAD_REQUEST
                return results
            
            alarm_feedback = AlarmFeedback()
            alarm_feedback.is_actual_alarm = request.is_actual_alarm
            alarm_feedback.alarm = alarm
            alarm.is_actual_alarm = request.is_actual_alarm
        
        else:
            alarm_feedback = AlarmFeedback.objects.get(alarm=alarm, user_id=user_id)
            if request.is_actual_alarm is not None:
                alarm_feedback.is_actual_alarm = request.is_actual_alarm
                alarm.is_actual_alarm = request.is_actual_alarm

        alarm_feedback.user_id = user_id
        alarm_feedback.comment = request.comment
        
        severity = Severity.objects.filter(
            flag_type=alarm.flag_type,
            level=request.rating
        ).first()

        if request.rating is not None and not severity:
            results['error'] = {
                'status_code': "Not Found",
                'status_description': f"Severity level {request.rating} not found for the flag type",
                'detail': "Invalid rating level provided.",
            }
            response.status_code = status.HTTP_404_NOT_FOUND
            return results
        
        alarm_feedback.rating = severity
        alarm_feedback.meta_info = request.meta_info
        alarm_feedback.updated_at = datetime.now(tz=timezone.utc)
        alarm_feedback.save()
        
        alarm.feedback_provided = True
        alarm.exclude_from_dashboard = not alarm.is_actual_alarm
        alarm.save()
        
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