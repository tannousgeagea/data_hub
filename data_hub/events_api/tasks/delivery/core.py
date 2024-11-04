import django
django.setup()
from django.db import IntegrityError
from django.core.exceptions import ObjectDoesNotExist
from celery import shared_task
from datetime import datetime, timezone
from acceptance_control.models import Delivery
from tenants.models import Tenant, PlantEntity

@shared_task(bind=True,autoretry_for=(Exception,), retry_backoff=True, retry_kwargs={"max_retries": 5}, ignore_result=True,
             name='delivery:execute')
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
                f"Entity {payload.location} for {tenant.domain} does not exist"
            )
            
            
        if Delivery.objects.filter(delivery_id=payload.delivery_id).exists():
            delivery = Delivery.objects.get(
                delivery_id=payload.delivery_id
            )
            delivery.delivery_end = payload.delivery_end.replace(tzinfo=timezone.utc)
            
        else:
            entity = PlantEntity.objects.get(entity_uid=payload.location, entity_type__tenant=tenant)
            delivery = Delivery(
                tenant=tenant,
                entity=entity,
                delivery_id=payload.delivery_id,
                delivery_location=payload.location,
                delivery_start=payload.delivery_start.replace(tzinfo=timezone.utc),
                delivery_end=payload.delivery_end.replace(tzinfo=timezone.utc),
            )
        
        delivery.save()
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