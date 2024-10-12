import django
django.setup()
from django.db import IntegrityError
from django.core.exceptions import ObjectDoesNotExist
from celery import shared_task
from datetime import datetime, timezone
from acceptance_control.models import Alarm, Media

@shared_task(bind=True,autoretry_for=(Exception,), retry_backoff=True, retry_kwargs={"max_retries": 5}, ignore_result=True,
             name='alarm:execute')
def execute(self, payload, **kwargs):
    data: dict = {}
    try:
        
        if not Alarm.objects.filter(event_uid=payload.event_uid).exists():
            raise ObjectDoesNotExist(
                f"event_uid {payload.event_uid} does not exist"
            )

        alarm = Alarm.objects.get(event_uid=payload.event_uid)
        media = Media(
            media_id=payload.media_id,
            media_name=payload.media_name,
            media_url=payload.media_url,
            media_type=payload.media_type,
        )
        media.save()
        
        # alarm_media = Alarm(
        #     media=media,
        #     alarm=alarm
        # )
        
        # alarm_media.save()
        
        alarm.save()
        data.update(
            {
                'action': 'done',
                'time':  datetime.now().strftime("%Y-%m-%d %H-%M-%S"),
                'result': 'success'
            }
        )
    
    except Exception as err:
        raise ValueError(f"Error saving delivery data into db: {err}")
    
    return data