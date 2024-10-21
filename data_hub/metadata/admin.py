
from django.contrib import admin
from unfold.admin import ModelAdmin, TabularInline, StackedInline
from .models import (
    Language, TableType, DataType, TableField, TenantTable, FieldOrder,
    TenantTableField, TableFieldLocalization, TableFilter, FilterItem,
    FilterLocalization, FilterItemLocalization, TenantTableFilter
)

class TableFieldLocalizationInline(TabularInline):
    model = TableFieldLocalization
    extra = 1

class TenantTableFieldInline(TabularInline):
    model = TenantTableField
    extra = 1

class FilterItemInline(TabularInline):
    model = FilterItem
    extra = 1

class FilterLocalizationInline(TabularInline):
    model = FilterLocalization
    extra = 1

class FilterItemLocalizationInline(TabularInline):
    model = FilterItemLocalization
    extra = 1

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
    inlines = [TableFieldLocalizationInline]

@admin.register(TenantTable)
class TenantTableAdmin(ModelAdmin):
    list_display = ('tenant', 'table_type', 'is_active', 'created_at')
    search_fields = ('tenant__tenant_name', 'table_type__name')
    list_filter = ('is_active',)
    ordering = ('-created_at',)
    inlines = [TenantTableFieldInline]

@admin.register(FieldOrder)
class FieldOrderAdmin(ModelAdmin):
    list_display = ("field_position", "description")

@admin.register(TenantTableField)
class TenantTableFieldAdmin(ModelAdmin):
    list_display = ('tenant_table', 'field', 'is_active', 'created_at')
    search_fields = ('tenant_table__tenant__tenant_name', 'field__name')
    list_filter = ('is_active', 'tenant_table__tenant__tenant_name', "tenant_table__table_type__name")
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
    inlines = [FilterItemInline]

@admin.register(FilterItem)
class FilterItemAdmin(ModelAdmin):
    list_display = ('table_filter', 'item_key', 'is_active', 'created_at')
    search_fields = ('item_key',)
    list_filter = ('is_active',)
    ordering = ('-created_at',)
    inlines = [FilterItemLocalizationInline]

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
    list_filter = ('tenant_table__tenant__tenant_name', 'table_filter__filter_name')
