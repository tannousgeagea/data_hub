from django.contrib import admin
from unfold.admin import ModelAdmin
from .models import (
    Media, 
    Delivery, 
    DeliveryMedia, 
    FlagType,
    FlagTypeLocalization,
    Severity, 
    DeliveryFlag, 
    TenantFlagDeployment,
    Alarm,
    AlarmMedia,
    DeliveryERPAttachment,
)

# Admin for Media Model
@admin.register(Media)
class MediaAdmin(ModelAdmin):
    list_display = ('media_id', 'media_name', 'media_type', 'media_url', 'file_size', 'created_at')
    search_fields = ('media_name', 'media_id', 'media_type')
    list_filter = ('media_type', 'created_at')
    readonly_fields = ('created_at',)
    fieldsets = (
        ('Basic Info', {'fields': ('media_id', 'media_name', 'media_type', 'media_url')}),
        ('Additional Info', {'fields': ('file_size', 'duration', 'meta_info')}),
        ('Timestamps', {'fields': ('created_at',)}),
    )

# Admin for Delivery Model
@admin.register(Delivery)
class DeliveryAdmin(ModelAdmin):
    list_display = ('delivery_id', 'tenant', 'entity', 'delivery_start', 'delivery_end', 'delivery_location')
    search_fields = ('delivery_id', 'tenant__name', 'entity__name')
    list_filter = ('tenant', 'entity', 'delivery_start', 'created_at')
    readonly_fields = ('created_at',)
    fieldsets = (
        ('Delivery Info', {'fields': ('tenant', 'entity', 'delivery_id', 'delivery_location')}),
        ('Time Info', {'fields': ('delivery_start', 'delivery_end')}),
        ('Timestamps', {'fields': ('created_at',)}),
    )

# Admin for Delivery Media Model
@admin.register(DeliveryMedia)
class DeliveryMediaAdmin(ModelAdmin):
    list_display = ('delivery', 'media')
    search_fields = ('delivery__delivery_id', 'media__media_name')
    list_filter = ('delivery', 'media')

# Admin for FlagType Model
@admin.register(FlagType)
class FlagTypeAdmin(ModelAdmin):
    list_display = ('name', 'description', 'created_at')
    search_fields = ('name',)
    readonly_fields = ('created_at',)

@admin.register(FlagTypeLocalization)
class FlagTypeLocalizationAdmin(ModelAdmin):
    list_display = ('flag_type', 'language', 'title', 'created_at')
    list_filter = ('flag_type', )

# Admin for Severity Model
@admin.register(Severity)
class SeverityAdmin(ModelAdmin):
    list_display = ('flag_type', 'level', 'description', 'color_code')
    search_fields = ('flag_type__name',)
    list_filter = ('level',)

# Admin for DeliveryFlag Model
@admin.register(DeliveryFlag)
class DeliveryFlagAdmin(ModelAdmin):
    list_display = ('delivery', 'flag_type', 'severity')
    search_fields = ('delivery__delivery_id', 'flag_type__name', 'severity__level')
    list_filter = ('flag_type', 'severity')

# Admin for TenantFlagDeployment Model
@admin.register(TenantFlagDeployment)
class TenantFlagDeploymentAdmin(ModelAdmin):
    list_display = ('tenant', 'flag_type', 'is_deployed')
    search_fields = ('tenant__tenant_name', 'flag_type__name')
    list_filter = ('is_deployed',)


@admin.register(Alarm)
class AlarmAdmin(ModelAdmin):
    list_display = ('tenant', "entity", "flag_type", "severity", "delivery_id", "created_at")
    search_fields = ("event_uid", "delivery_id")
    list_filter = ('tenant__tenant_name', "flag_type__name", "entity__entity_uid", "created_at")
    
@admin.register(AlarmMedia)
class AlarmMediaAdmin(ModelAdmin):
    list_display = ("alarm", "media", "show_created_at")
    search_fields = ("alarm__event_uid", "alarm__delivery_id")
    list_filter = ("alarm__tenant__tenant_name", "alarm__flag_type__name")
    
    def show_created_at(self, obj):
        return obj.media.created_at
    
    show_created_at.short_description = "Created at"
    

@admin.register(DeliveryERPAttachment)
class DeliveryERPAttachmentAdmin(ModelAdmin):
    list_display = ('delivery', 'attachment_type', 'value', 'acquisition_configuration', 'source_reference', 'fetched_at', 'created_at')
    search_fields = ('delivery__delivery_id', 'attachment_type__name', 'source_reference')
    list_filter = ('attachment_type', 'fetched_at', 'created_at')
    ordering = ('-created_at',)