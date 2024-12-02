import django
django.setup()
from django.db import IntegrityError
from django.core.exceptions import ObjectDoesNotExist
from celery import shared_task
from datetime import datetime, timezone
from acceptance_control.models import Delivery, Media, DeliveryMedia
from tenants.models import SensorBox

@shared_task(bind=True,autoretry_for=(Exception,), retry_backoff=True, retry_kwargs={"max_retries": 5}, ignore_result=True,
             name='delivery_media:execute')
def execute(self, payload, **kwargs):
    data: dict = {}
    try:        
        if not Delivery.objects.filter(delivery_id=payload.delivery_id).exists():
            raise ObjectDoesNotExist(
                f"delivery_id {payload.delivery_id} does not exist"
            )

            
        delivery = Delivery.objects.get(delivery_id=payload.delivery_id)
        sensor_box = SensorBox.objects.filter(
                plant_entity=delivery.entity,
                sensor_box_location=payload.sensor_box_location
            )   
        media = Media(
            media_id=payload.media_id,
            media_name=payload.media_name,
            media_url=payload.media_url,
            media_type=payload.media_type,
            sensor_box=sensor_box.first() if sensor_box else None,
        )
        media.save()
        
        delivery_media = DeliveryMedia(
            media=media,
            delivery=delivery
        )
        
        delivery_media.save()
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