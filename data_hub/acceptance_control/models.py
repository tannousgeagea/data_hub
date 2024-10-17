from django.db import models
from tenants.models import (
    Tenant,
    PlantEntity
)


class Media(models.Model):
    IMAGE = 'image'
    VIDEO = 'video'
    MEDIA_TYPE_CHOICES = [
        (IMAGE, 'Image'),
        (VIDEO, 'Video')
    ]
    
    media_id = models.CharField(max_length=255, unique=True, db_index=True)
    media_name = models.CharField(max_length=255)
    media_type = models.CharField(max_length=100, choices=MEDIA_TYPE_CHOICES)
    media_url = models.CharField(max_length=255)
    file_size = models.BigIntegerField(null=True, blank=True)  # Store size in bytes
    duration = models.DurationField(null=True, blank=True)  # Duration for videos
    created_at = models.DateTimeField(auto_now_add=True)
    meta_info = models.JSONField(null=True, blank=True)
    
    class Meta:
        db_table = 'media'
        verbose_name_plural = 'Media'
        
    def __str__(self):
        return f"{self.media_name} ({self.media_type})"

class Delivery(models.Model):
    tenant = models.ForeignKey(Tenant, on_delete=models.RESTRICT)
    entity = models.ForeignKey(PlantEntity, on_delete=models.RESTRICT)
    delivery_id = models.CharField(max_length=255, unique=True)
    delivery_start = models.DateTimeField()
    delivery_end = models.DateTimeField(null=True, blank=True)
    delivery_location = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'delivery'
        verbose_name_plural = 'Deliveries'
    
    def __str__(self):
        return f"Delivery {self.delivery_id} for {self.tenant}"



class DeliveryMedia(models.Model):
    delivery = models.ForeignKey(Delivery, on_delete=models.RESTRICT)
    media = models.ForeignKey(Media, on_delete=models.RESTRICT)
    
    class Meta:
        db_table = 'delivery_media'
        verbose_name_plural = 'Delivery Media'
        
    def __str__(self):
        return f"{self.delivery}: {self.media}"
    
# Define the flags that will be associated with deliveries
class FlagType(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = "flag_type"
        verbose_name_plural = "Flag Types"
    
    def __str__(self):
        return self.name

# Severity levels for each flag
class Severity(models.Model):
    flag_type = models.ForeignKey(FlagType, on_delete=models.RESTRICT, related_name='severities')
    level = models.IntegerField()  # e.g., 1: low, 2: medium, 3: high
    description = models.TextField(null=True, blank=True)
    color_code = models.CharField(max_length=7)  # e.g., #00FF00 for green
    unicode_char = models.CharField(null=True, blank=True)
    
    class Meta:
        db_table = "severity"
        verbose_name_plural = "Severity"
    
    def __str__(self):
        return f"{self.flag_type.name} Severity Level {self.level}"

# Store the flags attached to each delivery
class DeliveryFlag(models.Model):
    delivery = models.ForeignKey(Delivery, on_delete=models.RESTRICT, related_name='flags')
    flag_type = models.ForeignKey(FlagType, on_delete=models.RESTRICT)
    severity = models.ForeignKey(Severity, on_delete=models.RESTRICT)

    class Meta:
        db_table = "delivery_flag"
        verbose_name_plural = "Delivery Flags"

    def __str__(self):
        return f"{self.flag_type.name} for {self.delivery.delivery_id} - Severity: {self.severity.level}"

# Multi-tenant deployment model, specifying which flags are available for each tenant
class TenantFlagDeployment(models.Model):
    tenant = models.ForeignKey(Tenant, on_delete=models.RESTRICT, related_name='flag_deployments')
    flag_type = models.ForeignKey(FlagType, on_delete=models.RESTRICT)
    is_deployed = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "tenant_flag_deployment"
        verbose_name_plural = "Tenant Flag Deployments"

    def __str__(self):
        return f"{self.flag_type.name} deployed for {self.tenant.tenant_name}: {self.is_deployed}"

class Alarm(models.Model):
    tenant = models.ForeignKey(Tenant, on_delete=models.RESTRICT)
    entity = models.ForeignKey(PlantEntity, on_delete=models.RESTRICT)
    flag_type = models.ForeignKey(FlagType, on_delete=models.RESTRICT)
    severity = models.ForeignKey(Severity, on_delete=models.RESTRICT)
    timestamp = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    event_uid = models.CharField(max_length=255, unique=True)
    delivery_id = models.CharField(max_length=255, null=True, blank=True)
    
    class Meta:
        db_table = 'alarm'
        verbose_name_plural = 'Alarms'
        
    def __str__(self):
        return f"Alarm {self.event_uid} for {self.tenant}"
    
class AlarmMedia(models.Model):
    alarm = models.ForeignKey(Alarm, on_delete=models.RESTRICT)
    media = models.ForeignKey(Media, on_delete=models.RESTRICT)
    
    class Meta:
        db_table = 'alarm_media'
        verbose_name_plural = 'Alarm Media'
        
    def __str__(self):
        return f"{self.alarm}: {self.media}"