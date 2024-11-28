
from django.contrib import admin
from unfold.admin import ModelAdmin, TabularInline, StackedInline
from .models import (
    Language, TableType, DataType, TableField, TenantTable, FieldOrder,
    TenantTableField, TableFieldLocalization, TableFilter, FilterItem,
    FilterLocalization, FilterItemLocalization, TenantTableFilter,
    PlantEntityLocalization,
    TableAsset, 
    TableAssetLocalization,
    TableAssetItemLocalization,
    TableAssetItem,
    TenantTableAsset
    )

from .models import (
    ERPDataType, 
    TenantAttachmentRequirement, 
    Protocol, 
    Method, 
    AttachmentAcquisitionConfiguration,
)


from .models import (
    FormField, FormFieldLocalization, FeedbackForm, FeedbackFormField, FeedbackFormFieldItem,
    FeedbackFormFieldItemLocalization, TenantFeedbackForm,
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

@admin.register(PlantEntityLocalization)
class PlantEntityLocalizationAdmin(ModelAdmin):
    list_display = ('plant_entity', 'language', 'title', 'created_at')
    list_filter = ('plant_entity', )

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

class TableAssetLocalizationInline(TabularInline):
    model = TableAssetLocalization
    extra = 1

class TableAssetItemLocalizationInline(TabularInline):
    model = TableAssetItemLocalization
    extra = 1

class TableAssetItemInline(TabularInline):
    model = TableAssetItem
    extra = 1
@admin.register(TableAsset)
class TableAssetAdmin(ModelAdmin):
    list_display = ('key', 'is_active', 'is_external', 'created_at')
    list_filter = ('is_active', 'is_external')
    search_fields = ('key',)
    inlines = [TableAssetLocalizationInline, TableAssetItemInline]
@admin.register(TableAssetItem)
class TableAssetItemAdmin(ModelAdmin):
    list_display = ('key', 'media_type', 'is_active', 'is_external', 'created_at')
    list_filter = ('is_active', 'is_external', 'media_type')
    search_fields = ('key', 'name')
    inlines = [TableAssetItemLocalizationInline]
@admin.register(TenantTableAsset)
class TenantTableAssetAdmin(ModelAdmin):
    list_display = ('tenant_table', 'table_asset', 'is_active', 'field_order', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('table_asset__key', 'tenant_table__name')
    
##########################################################################
###################### ERP Data ##########################################
@admin.register(ERPDataType)
class ERPDataTypeAdmin(ModelAdmin):
    list_display = ('name', 'description', 'data_type', 'created_at')
    search_fields = ('name', 'description')
    list_filter = ('data_type',)
    ordering = ('created_at',)

@admin.register(TenantAttachmentRequirement)
class TenantAttachmentRequirementAdmin(ModelAdmin):
    list_display = ('tenant', 'attachment_type', 'is_active', 'created_at')
    search_fields = ('tenant__tenant_name', 'attachment_type__name')
    list_filter = ('is_active', 'created_at')
    ordering = ('-created_at',)

@admin.register(Protocol)
class ProtocolAdmin(ModelAdmin):
    list_display = ('name', 'description', 'created_at')
    search_fields = ('name', 'description')
    ordering = ('created_at',)

@admin.register(Method)
class MethodAdmin(ModelAdmin):
    list_display = ('name', 'description', 'protocol', 'endpoint_url', 'created_at')
    search_fields = ('name', 'description', 'endpoint_url')
    list_filter = ('protocol',)
    ordering = ('created_at',)

@admin.register(AttachmentAcquisitionConfiguration)
class AttachmentAcquisitionConfigurationAdmin(ModelAdmin):
    list_display = ('tenant', 'attachment_type', 'method', 'created_at')
    search_fields = ('tenant__tenant_name', 'attachment_type__name', 'method__name')
    list_filter = ('created_at',)
    ordering = ('-created_at',)
    
    
#######################################################################################
############################### Feedback ##############################################
# Inline for FormFieldLocalization
class FormFieldLocalizationInline(TabularInline):
    model = FormFieldLocalization
    extra = 1
    fields = ('language', 'title', 'description', 'placeholder')
    verbose_name_plural = "Localizations"

# Inline for FeedbackFormField
class FeedbackFormFieldInline(TabularInline):
    model = FeedbackFormField
    extra = 1
    fields = ('form_field', 'is_active', 'is_hidden', 'field_order', 'dependency', 'description')
    verbose_name_plural = "Fields in Form"
    

class FormFieldLocalizationInline(TabularInline):
    model = FormFieldLocalization
    extra = 1
    fields = ('language', 'title', 'description', 'placeholder')
    verbose_name_plural = "Field Localizations"

# Inline for FeedbackFormFieldItem
class FeedbackFormFieldItemInline(TabularInline):
    model = FeedbackFormFieldItem
    extra = 1
    fields = ('item_key', 'is_active', 'field_order', 'description')
    verbose_name_plural = "Field Items"

# Inline for FeedbackFormFieldItemLocalization
class FeedbackFormFieldItemLocalizationInline(TabularInline):
    model = FeedbackFormFieldItemLocalization
    extra = 1
    fields = ('language', 'title', 'color', 'description')
    verbose_name_plural = "Item Localizations"

# Admin for FeedbackForm
@admin.register(FormField)
class FormFieldAdmin(ModelAdmin):
    list_display = ('name', 'type', 'description', 'created_at')
    search_fields = ('name',)
    inlines = [FormFieldLocalizationInline, FeedbackFormFieldItemInline]

@admin.register(FeedbackForm)
class FeedbackFormAdmin(ModelAdmin):
    list_display = ('name', 'is_active', 'description', 'created_at')
    search_fields = ('name',)
    inlines = [FeedbackFormFieldInline]

@admin.register(FeedbackFormField)
class FeedbackFormFieldAdmin(ModelAdmin):
    list_display = ('form', 'form_field', 'is_active', 'is_hidden', 'field_order', 'created_at')
    search_fields = ('form__name', 'form_field__name')
    list_filter = ('is_active', 'is_hidden')
    inlines = []

@admin.register(FeedbackFormFieldItem)
class FeedbackFormFieldItemAdmin(ModelAdmin):
    list_display = ('field', 'item_key', 'is_active', 'field_order', 'created_at')
    search_fields = ('field__name', 'item_key')
    list_filter = ('is_active',)
    inlines = [FeedbackFormFieldItemLocalizationInline]

@admin.register(TenantFeedbackForm)
class TenantFeedbackFormAdmin(ModelAdmin):
    list_display = ('tenant', 'feedback_form', 'is_active', 'created_at')
    search_fields = ('tenant__name', 'feedback_form__name')
    list_filter = ('is_active',)
