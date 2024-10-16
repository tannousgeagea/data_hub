import string
from django.db import models
from tenants.models import Tenant
from django.core.exceptions import ValidationError

def clean_field(value):
    new_value = ''
    for i, char in enumerate(value):
        if char == '_':
            new_value += char
            continue
        
        if char in string.punctuation:
            if new_value[-1] == '_':
                continue
            
            new_value += '_'
            continue

        new_value += char

    return new_value
    
class Language(models.Model):
    """
    Model to define and manage supported languages.
    """
    code = models.CharField(max_length=10, unique=True)  # ISO 639-1 language codes, e.g., 'en', 'fr'
    name = models.CharField(max_length=50)  # e.g., 'English', 'French'
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'language'
        verbose_name_plural = 'Languages'

    def __str__(self):
        return f"{self.name} ({self.code})"
    
class TableType(models.Model):
    name = models.CharField(max_length=255)
    desciption = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = "table_type"
        verbose_name_plural = "Table Types"
        verbose_name = "Table Type"
        
    def __str__(self):
        return f"{self.name}"
    
class DataType(models.Model):
    type = models.CharField(max_length=50)
    desciption = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'data_type'
        verbose_name_plural = "Data Types"
        
    def __str__(self):
        return self.type
    
class TableField(models.Model):
    name = models.CharField(max_length=255)
    type = models.ForeignKey(DataType, on_delete=models.CASCADE)
    description = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'table_field'
        verbose_name_plural = "Table Fields"
        
    def __str__(self):
        return f"{self.name} ({self.type})"
    
    def save(self, *args, **kwargs):
        self.name = clean_field(self.name)
        super(TableField, self).save(*args, **kwargs)
    
class TenantTable(models.Model):
    tenant = models.ForeignKey(Tenant, on_delete=models.RESTRICT)
    table_type = models.ForeignKey(TableType, on_delete=models.RESTRICT)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    description = models.TextField(null=True, blank=True)

    class Meta:
        db_table = 'tenant_table'
        verbose_name_plural = "Tenant Tables"
        
    def __str__(self):
        return f"{self.tenant}: {self.table_type}"
    
class FieldOrder(models.Model):
    field_position = models.PositiveSmallIntegerField(unique=True) 
    created_at = models.DateTimeField(auto_now_add=True)
    description = models.TextField(null=True, blank=True)

    class Meta:
        db_table = 'field_order'
        verbose_name_plural = "Field Orders"
    
    def __str__(self):
        return f"{self.field_position}"
    
class TenantTableField(models.Model):
    field = models.ForeignKey(TableField, on_delete=models.RESTRICT)
    tenant_table = models.ForeignKey(TenantTable, on_delete=models.RESTRICT, )
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    is_hidden = models.BooleanField(default=False)
    field_order = models.ForeignKey(FieldOrder, models.RESTRICT)
    description = models.TextField(null=True, blank=True)
    
    class Meta:
        db_table = 'tenant_table_field'
        verbose_name_plural = "Tenant Table Fields"
        unique_together = ('field', 'tenant_table')
        
    def __str__(self):
        return f"{self.tenant_table}: {self.field}"
    
class TableFieldLocalization(models.Model):
    field = models.ForeignKey(
        TableField,
        on_delete=models.RESTRICT,
        related_name='table_field_localizations'
    )
    
    language = models.ForeignKey(Language, on_delete=models.RESTRICT)
    title = models.CharField(max_length=255, help_text="Localized title of the column.")
    description = models.TextField(blank=True, null=True, help_text="Localized description of the column.")
    created_at = models.DateTimeField(auto_now_add=True)

    
    class Meta:
        db_table = 'table_field_localization'
        verbose_name_plural = 'Table Field Localizations'
        unique_together = ('field', 'language')  # Ensure unique localization per column-language pair
        indexes = [
            models.Index(fields=['field', 'language']),
        ]

    def __str__(self):
        return f"Localization for '{self.field.name}' in {self.language}"
    
class TableFilter(models.Model):
    """
    Represents filters used to filter the metadata events.
    
    Attributes:
        - filter_name (CharField): The internal name of the filter.
        - title (CharField): The display name of the filter.
        - type (CharField): The data type of the filter (e.g., "enum").
        - is_active (BooleanField): Whether the filter is currently active.
    """
    filter_name = models.CharField(max_length=255, help_text="The internal name of the filter.")
    type = models.CharField(max_length=50, help_text="The data type of the filter (e.g., 'enum').")
    is_active = models.BooleanField(default=True, help_text="Indicates if the filter is currently active.")
    is_external = models.BooleanField(default=False, help_text="Indicated whether the filter items are given from external url")
    url = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


    class Meta:
        db_table = 'table filter'
        verbose_name_plural = 'Table Filters'
        unique_together = ('filter_name',)
        indexes = [
            models.Index(fields=['filter_name']),
        ]

    def __str__(self):
        return f"Filter: {self.filter_name} (Type: {self.type})"


class FilterItem(models.Model):
    """
    Represents filter items (e.g., individual options for a filter).
    
    Attributes:
        - filter (ForeignKey): A reference to the Filter object.
        - item_key (CharField): The internal key of the filter item (e.g., "impurity").
        - item_value (CharField): The display value of the filter item (e.g., "Störstoff").
        - is_active (BooleanField): Whether the filter item is currently active.
    """
    table_filter = models.ForeignKey(TableFilter, on_delete=models.RESTRICT)
    item_key = models.CharField(max_length=255, help_text="The internal key for the filter item (e.g., 'impurity').")
    is_active = models.BooleanField(default=True, help_text="Indicates if the filter item is currently active.")
    created_at = models.DateTimeField(auto_now_add=True)
    field_order = models.ForeignKey(FieldOrder, on_delete=models.RESTRICT)


    class Meta:
        db_table = 'filter_item'
        verbose_name_plural = 'Filter Items'
        unique_together = ('table_filter', 'item_key')  # Ensure unique filter items per filter
        indexes = [
            models.Index(fields=['table_filter', 'item_key']),
        ]

    def __str__(self):
        return f"Filter Item: {self.item_key} (Key: {self.item_key})"
    
class FilterLocalization(models.Model):
    """
    Represents localized metadata for filters.
    
    Attributes:
        - filter (ForeignKey): A reference to the Filter object.
        - language (CharField): The language code (e.g., "en", "de").
        - title (CharField): Localized title of the filter.
        - description (TextField): Localized description of the filter.
    """
    table_filter = models.ForeignKey(
        TableFilter,
        on_delete=models.RESTRICT, 
        related_name='localizations', 
        help_text="The filter being localized."
    )
    language = models.ForeignKey(Language, on_delete=models.RESTRICT)
    title = models.CharField(max_length=255, help_text="Localized title of the filter.")
    description = models.TextField(blank=True, null=True, help_text="Localized description of the filter.")
    placeholder = models.CharField(max_length=255, default='Select')
    created_at = models.DateTimeField(auto_now_add=True)


    class Meta:
        db_table = 'filter_localization'
        verbose_name_plural = 'Filter Localizations'
        unique_together = ('table_filter', 'language')  # Ensure unique localization per filter-language pair
        indexes = [
            models.Index(fields=['table_filter', 'language']),
        ]

    def __str__(self):
        return f"Filter Localization for '{self.title}' in {self.language}"


class FilterItemLocalization(models.Model):
    """
    Represents localized metadata for filter items.
    
    Attributes:
        - filter_item (ForeignKey): A reference to the FilterItem object.
        - language (CharField): The language code (e.g., "en", "de").
        - item_value (CharField): Localized value of the filter item.
    """
    filter_item = models.ForeignKey(
        'FilterItem', 
        on_delete=models.RESTRICT, 
        related_name='localizations', 
        help_text="The filter item being localized."
    )
    language = models.ForeignKey(Language, on_delete=models.RESTRICT)
    item_value = models.CharField(max_length=255, help_text="Localized value of the filter item.")
    created_at = models.DateTimeField(auto_now_add=True)


    class Meta:
        db_table = 'filter_item_localization'
        verbose_name_plural = 'Filter Item Localizations'
        unique_together = ('filter_item', 'language')  # Ensure unique localization per filter item-language pair
        indexes = [
            models.Index(fields=['filter_item', 'language']),
        ]

    def __str__(self):
        return f"Filter Item Localization for '{self.filter_item.item_key}' in {self.language}"

class TenantTableFilter(models.Model):
    table_filter = models.ForeignKey(TableFilter, on_delete=models.RESTRICT,)
    tenant_table = models.ForeignKey(TenantTable, on_delete=models.RESTRICT, )
    is_active = models.BooleanField(default=True, help_text="Indicates if the filter item is currently active.")
    field_order = models.ForeignKey(FieldOrder, on_delete=models.RESTRICT,)
    created_at = models.DateTimeField(auto_now_add=True)
    description = models.TextField(blank=True, null=True)
    
    class Meta:
        db_table = 'tenant_table_filter'
        verbose_name_plural = "Tenant Table Filters"
        
    def __str__(self):
        return f"{self.tenant_table}: {self.table_filter.filter_name}"