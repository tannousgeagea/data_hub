import django
django.setup()
from django.db import IntegrityError
from django.core.exceptions import ObjectDoesNotExist
from celery import shared_task
from datetime import datetime, timezone
from acceptance_control.models import Delivery, DeliveryFlag, FlagType, Severity

@shared_task(bind=True,autoretry_for=(Exception,), retry_backoff=True, retry_kwargs={"max_retries": 5}, ignore_result=True,
             name='delivery_flag:execute')
def execute(self, payload, **kwargs):
    data: dict = {}
    try:        
        if not Delivery.objects.filter(delivery_id=payload.delivery_id).exists():
            raise ObjectDoesNotExist(
                f"delivery_id {payload.delivery_id} does not exist"
            )
            
        if not FlagType.objects.filter(name=payload.flag_type).exists():
            raise ObjectDoesNotExist(
                f"flag type {payload.flag_type} does not exist"
            )
            
        delivery = Delivery.objects.get(delivery_id=payload.delivery_id)
        flag_type = FlagType.objects.get(name=payload.flag_type)
        
        if not Severity.objects.filter(flag_type=flag_type, level=payload.severity_level).exists():
            raise ObjectDoesNotExist(
                f"severity level {payload.severity_level} for {payload.flag_type} does not exist"
            )
        
        severity = Severity.objects.get(flag_type=flag_type, level=payload.severity_level)
        
        flag = DeliveryFlag(
            delivery=delivery,
            flag_type=flag_type,
            severity=severity,
        )
        
        flag.save()
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