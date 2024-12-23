from django.db import models
from tenants.models import (
    Tenant,
    PlantEntity,
    SensorBox,
)

from metadata.models import (
    Language,
    DataType,
    ERPDataType,
    AttachmentAcquisitionConfiguration,
)

class Media(models.Model):
    IMAGE = 'image'
    VIDEO = 'video'
    MEDIA_TYPE_CHOICES = [
        (IMAGE, 'Image'),
        (VIDEO, 'Video')
    ]
    
    media_id = models.CharField(max_length=255, unique=True, db_index=True)
    sensor_box = models.ForeignKey(SensorBox, on_delete=models.RESTRICT, null=True, blank=True)
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
        return f"{self.media_id} ({self.media_type})"

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

class FlagTypeLocalization(models.Model):
    flag_type = models.ForeignKey(
        FlagType,
        on_delete=models.RESTRICT,
        related_name='flag_type_localization'
    )
    
    language = models.ForeignKey(Language, on_delete=models.RESTRICT)
    title = models.CharField(max_length=255, help_text="Localized title of the flag type.")
    description = models.TextField(blank=True, null=True, help_text="Localized description of the falg type.")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'flag_type_localization'
        verbose_name_plural = 'Flag Type Localizations'
        unique_together = ('flag_type', 'language')
        indexes = [
            models.Index(fields=['flag_type', 'language']),
        ]

    def __str__(self):
        return f"Localization for '{self.flag_type.name}' in {self.language}"

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
    event_uid = models.CharField(max_length=255, unique=True, null=True, blank=True)
    
    # Feedback-related fields
    feedback_provided = models.BooleanField(default=False)
    is_actual_alarm = models.BooleanField(null=True, blank=True)
    exclude_from_dashboard = models.BooleanField(default=False)
    
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
    ack_status = models.BooleanField(default=False)
    
    # Feedback-related fields
    feedback_provided = models.BooleanField(default=False)
    is_actual_alarm = models.BooleanField(null=True, blank=True)
    exclude_from_dashboard = models.BooleanField(default=False)
    
    # Extra Info
    value = models.CharField(max_length=255, null=True, blank=True)
    meta_info = models.JSONField(null=True, blank=True)
    
    class Meta:
        db_table = 'alarm'
        verbose_name_plural = 'Alarms'
        
    def __str__(self):
        return f"Alarm {self.event_uid} for {self.tenant}"

class AlarmAttr(models.Model):
    alarm = models.ForeignKey(Alarm, related_name="alarm_attr", on_delete=models.RESTRICT)
    key = models.CharField(max_length=255)
    value = models.CharField(max_length=255)
    data_type = models.ForeignKey(DataType, on_delete=models.RESTRICT)

    class Meta:
        db_table = 'alarm_attr'
        verbose_name_plural = 'Alarm Attribute'

    def __str__(self):
        return f"{self.key}: {self.value} ({self.data_type})"

class AlarmMedia(models.Model):
    alarm = models.ForeignKey(Alarm, on_delete=models.RESTRICT)
    media = models.ForeignKey(Media, on_delete=models.RESTRICT)
    
    class Meta:
        db_table = 'alarm_media'
        verbose_name_plural = 'Alarm Media'
        
    def __str__(self):
        return f"{self.alarm}: {self.media}"
    

class DeliveryERPAttachment(models.Model):
    delivery = models.ForeignKey(Delivery, on_delete=models.RESTRICT)
    attachment_type = models.ForeignKey(ERPDataType, on_delete=models.CASCADE)
    value = models.CharField(max_length=255, null=True, blank=True)
    acquisition_configuration = models.ForeignKey(AttachmentAcquisitionConfiguration, on_delete=models.SET_NULL, null=True)
    source_reference = models.CharField(max_length=255, null=True, blank=True, help_text="Optional reference to external source or entry")
    fetched_at = models.DateTimeField(null=True, blank=True, help_text="Timestamp for API data retrieval")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'delivery_erp_attachment'
        verbose_name_plural = 'Delivery ERP Attachments'
        unique_together = ('delivery', 'attachment_type')

    def __str__(self):
        return f"{self.delivery.delivery_id}: {self.attachment_type.name}"


class AlarmFeedback(models.Model):
    alarm = models.ForeignKey(
        Alarm, on_delete=models.RESTRICT
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    user_id = models.CharField(max_length=255, null=True, blank=True)
    is_actual_alarm = models.BooleanField()
    comment = models.CharField(max_length=255, null=True, blank=True)
    rating = models.ForeignKey(
        Severity,
        on_delete=models.RESTRICT,
        null=True,
        blank=True,
    )
    meta_info = models.JSONField(null=True, blank=True)

    class Meta:
        db_table = 'alarm_feedback'
        verbose_name = 'Alarm Feedback'
        verbose_name_plural = 'Alarm Feedbacks'

    def __str__(self):
        return f"Feedback for Alarm {self.alarm.event_uid}"