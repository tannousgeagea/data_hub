from django.contrib import admin
from unfold.admin import ModelAdmin
from tenants.models import Tenant, EntityType, PlantEntity

# Register your models here.
@admin.register(Tenant)
class TenantAdmin(ModelAdmin):
    list_display = ('tenant_id', 'tenant_name', 'location', 'domain', 'is_active', 'created_at')
    search_fields = ('tenant_name', 'location', 'domain')
    list_filter = ('is_active',)
    
@admin.register(EntityType)
class EntityTypeAdmin(ModelAdmin):
    """
    Admin interface for the EntityType model.
    """
    list_display = ('tenant', 'entity_type', 'created_at')  # Display plant, entity type, and creation date
    search_fields = ('entity_type', 'tenant__tenant_name')  # Search by entity type and plant name
    list_filter = ('tenant', 'created_at')  # Add filters for plant and creation date
    ordering = ('-created_at',)  # Order by creation date, newest first
    readonly_fields = ('created_at',)  # Make created_at field read-only

@admin.register(PlantEntity)
class PlantEntityAdmin(ModelAdmin):
    """
    Admin interface for the PlantEntity model.
    """
    list_display = ('entity_type', 'entity_uid', 'description', 'created_At')  # Display fields in the list view
    search_fields = ('entity_uid', 'description', 'entity_type__entity_type')  # Search by UID, description, and entity type
    list_filter = ('entity_type', 'created_At')  # Add filters for entity type and creation date
    ordering = ('-created_At',)  # Order by creation date, newest first
    readonly_fields = ('created_At',)  # Make created_At field read-only