import django
django.setup()
from django.db import IntegrityError
from django.core.exceptions import ObjectDoesNotExist
from celery import shared_task
from datetime import datetime, timezone
from acceptance_control.models import Alarm, FlagType, Severity, Delivery
from tenants.models import Tenant, PlantEntity

@shared_task(bind=True,autoretry_for=(Exception,), retry_backoff=True, retry_kwargs={"max_retries": 5}, ignore_result=True,
             name='alarm:execute')
def execute(self, payload, **kwargs):
    data: dict = {}
    try:
        
        if not Tenant.objects.filter(domain=payload.tenant_domain).exists():
            raise ObjectDoesNotExist(
                f"tenant {payload.tenant_domain} does not exist"
            )
            
        tenant = Tenant.objects.get(domain=payload.tenant_domain)
        if not PlantEntity.objects.filter(entity_uid=payload.location, entity_type__tenant=tenant).exists():
            raise ObjectDoesNotExist(
                f"Entity {payload.location} does not exist"
            )
            
        if not FlagType.objects.filter(name=payload.flag_type).exists():
            raise ObjectDoesNotExist(
                f"flag type {payload.flag_type} does not exist"
            )
            
        flag_type = FlagType.objects.get(name=payload.flag_type)
        if not Severity.objects.filter(flag_type=flag_type, level=payload.severity_level).exists():
            raise ObjectDoesNotExist(
                f"severity level {payload.severity_level} for {payload.flag_type} does not exist"
            )

        # if payload.delivery_id:
        #     if not Delivery.objects.filter(delivery_id=payload.delivery_id).exists():
        #         raise ObjectDoesNotExist(
        #             f"delivery_id {payload.delivery_id} does not exist"
        #         )

        if Alarm.objects.filter(event_uid=payload.event_uid).exists():
            return {
                'action': "ignored",
                "time": datetime.now().strftime("%Y-%m-%d %H-%M-%S"),
                "result": f"{payload.event_uid} exists"
            }
                
        entity = PlantEntity.objects.get(entity_uid=payload.location, entity_type__tenant=tenant)
        severity = Severity.objects.get(flag_type=flag_type, level=payload.severity_level)

        alarm = Alarm(
            tenant=tenant,
            entity=entity,
            flag_type=flag_type,
            severity=severity,
            timestamp=payload.timestamp.replace(tzinfo=timezone.utc),
            event_uid=payload.event_uid,
            delivery_id=payload.delivery_id,
        )
        
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