from django.db import models

# Create your models here.
class Tenant(models.Model):
    tenant_id = models.CharField(max_length=255, unique=True)
    tenant_name = models.CharField(max_length=255)
    location = models.CharField(max_length=100)
    domain = models.CharField(max_length=50)
    is_active = models.BooleanField(default=True, help_text="Indicates if the filter is currently active.")
    created_at = models.DateTimeField(auto_now_add=True)
    meta_info = models.JSONField(null=True, blank=True)
    
    class Meta:
        db_table = "wa_tenant"
        verbose_name_plural = "Tenants"
        
    def __str__(self):
        return f"{self.tenant_name}"
    
class EntityType(models.Model):
    """
    Represents a type of entity within the application. This model is used to store distinct entity types, characterized by their 'entity_type' field.

    Attributes:
    - entity_type (CharField): A string field to store the type of the entity. Max length is set to 250 characters.
    - entry_timestamp (DateTimeField): A timestamp indicating when the entity type was created or registered in the system. It defaults to the current time when the entity type instance is created.

    The Meta class defines the database table name 'entity_type' and sets a verbose name in plural form 'Entity Types'.
    The __str__ method returns the string representation of the entity type, making it more readable and identifiable in admin interfaces or when queried.
    """
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)
    entity_type = models.CharField(max_length=250)
    created_at = models.DateTimeField(auto_now_add=True)
    meta_info = models.JSONField(null=True, blank=True)


    class Meta:
        db_table = "entity_type"
        verbose_name_plural = "Entity Types"

    def __str__(self):
        return f"{self.tenant} - {self.entity_type}"
    
class PlantEntity(models.Model):

    """
    Represents a plant entity within the application, associated with a specific type of entity defined in EntityType. This model is used to store and manage plant entities, keeping track of their types, unique identifiers, and descriptions.

    Attributes:
    - entity_type (ForeignKey): A foreign key linking to the EntityType model, defining the type of the plant entity.
    - entity_uid (CharField): A unique identifier for the plant entity. Max length is set to 250 characters.
    - description (CharField): A brief description of the plant entity. Max length is set to 250 characters.
    - entry_timestamp (DateTimeField): A timestamp indicating when the plant entity was created or registered in the system. It defaults to the current time when the plant entity instance is created.

    The Meta class defines the database table name 'plant_entity' and sets a verbose name in plural form ' Plant Entities'.
    The __str__ method returns a string representation of the plant entity, combining the entity type and the unique identifier, making it easily identifiable and readable, especially in admin interfaces or when queried.
    """

    entity_type = models.ForeignKey(EntityType, on_delete=models.CASCADE)
    entity_uid = models.CharField(max_length=250)
    description = models.CharField(max_length=250)
    created_At = models.DateTimeField(auto_now_add=True)
    meta_info = models.JSONField(null=True, blank=True)

    class Meta:
        db_table = "plant_entity"
        verbose_name_plural = "Plant Entities"

    def __str__(self):
        return f'Entity {self.entity_uid} in {self.entity_type.tenant.tenant_name}'
