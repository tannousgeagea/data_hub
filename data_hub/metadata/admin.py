
from django.contrib import admin
from unfold.admin import ModelAdmin
from .models import (
    Tenant, Language, TableType, DataType, TableField, TenantTable,
    TenantTableField, TableFieldLocalization, TableFilter, FilterItem,
    FilterLocalization, FilterItemLocalization, TenantTableFilter
)

@admin.register(Tenant)
class TenantAdmin(ModelAdmin):
    list_display = ('tenant_id', 'tenant_name', 'location', 'domain', 'is_active', 'created_at')
    search_fields = ('tenant_name', 'location', 'domain')
    list_filter = ('is_active',)


@admin.register(Language)
class LanguageAdmin(ModelAdmin):
    list_display = ('code', 'name', 'created_at')
    search_fields = ('code', 'name')
    ordering = ('-created_at',)

@admin.register(TableType)
class TableTypeAdmin(ModelAdmin):
    list_display = ('name', 'created_at')
    search_fields = ('name',)
    ordering = ('-created_at',)

@admin.register(DataType)
class DataTypeAdmin(ModelAdmin):
    list_display = ('type', 'created_at')
    search_fields = ('type',)
    ordering = ('-created_at',)

@admin.register(TableField)
class TableFieldAdmin(ModelAdmin):
    list_display = ('name', 'type', 'created_at')
    search_fields = ('name',)
    list_filter = ('type',)
    ordering = ('-created_at',)

@admin.register(TenantTable)
class TenantTableAdmin(ModelAdmin):
    list_display = ('tenant', 'table_type', 'is_active', 'created_at')
    search_fields = ('tenant__tenant_name', 'table_type__name')
    list_filter = ('is_active',)
    ordering = ('-created_at',)

@admin.register(TenantTableField)
class TenantTableFieldAdmin(ModelAdmin):
    list_display = ('tenant_table', 'field', 'is_active', 'created_at')
    search_fields = ('tenant_table__tenant__tenant_name', 'field__name')
    list_filter = ('is_active',)
    ordering = ('-created_at',)

@admin.register(TableFieldLocalization)
class TableFieldLocalizationAdmin(ModelAdmin):
    list_display = ('field', 'language', 'title', 'created_at')
    search_fields = ('field__name', 'language__name')
    ordering = ('-created_at',)

@admin.register(TableFilter)
class TableFilterAdmin(ModelAdmin):
    list_display = ('filter_name', 'type', 'is_active', 'created_at')
    search_fields = ('filter_name', 'type')
    list_filter = ('is_active',)
    ordering = ('-created_at',)

@admin.register(FilterItem)
class FilterItemAdmin(ModelAdmin):
    list_display = ('table_filter', 'item_key', 'is_active', 'created_at')
    search_fields = ('item_key',)
    list_filter = ('is_active',)
    ordering = ('-created_at',)

@admin.register(FilterLocalization)
class FilterLocalizationAdmin(ModelAdmin):
    list_display = ('table_filter', 'language', 'title', 'created_at')
    search_fields = ('table_filter__filter_name', 'language__name')
    ordering = ('-created_at',)

@admin.register(FilterItemLocalization)
class FilterItemLocalizationAdmin(ModelAdmin):
    list_display = ('filter_item', 'language', 'item_value', 'created_at')
    search_fields = ('filter_item__item_key', 'language__name')
    ordering = ('-created_at',)

@admin.register(TenantTableFilter)
class TenantTableFilterAdmin(ModelAdmin):
    list_display = ('tenant_table', 'table_filter', 'created_at')
    search_fields = ('tenant_table__tenant__tenant_name', 'table_filter__filter_name')
    ordering = ('-created_at',)
