from django.db import models
from tenants.models import (
    Tenant,
    EntityType,
    PlantEntity
)


# Create your models here.
class Delivery(models.Model):
    tenant = models.ForeignKey(Tenant, on_delete=models.RESTRICT)
    entity = models.ForeignKey(PlantEntity, on_delete=models.RESTRICT)
    delivery_id = models.CharField(max_length=255, unique=True)
    delivery_start = models.DateTimeField()
    delivery_end = models.DateTimeField(null=True)
    delivery_location = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'delivery'
        verbose_name_plural = 'Deliveries'
    
    def __str__(self):
        return f'Delivery at {self.delivery_location} at {self.created_at}'

class Alarm(models.Model):
    pass