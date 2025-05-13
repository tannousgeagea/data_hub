# app/api/storage_settings.py

import django
django.setup()
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from django.core.exceptions import ObjectDoesNotExist
from tenants.models import Tenant, TenantStorageSettings  # adjust path

router = APIRouter()

class StorageKeyUpdateIn(BaseModel):
    tenant_domain: str = Field(..., example="example.wasteant.com")
    account_key: str = Field(..., example="new-secret-key")

class StorageKeyUpdateOut(BaseModel):
    tenant_domain: str
    provider_name: str
    account_name: str
    message: str


@router.patch("/tenant/storage-key", response_model=StorageKeyUpdateOut)
def update_storage_key(payload: StorageKeyUpdateIn):
    try:
        tenant = Tenant.objects.get(domain=payload.tenant_domain)
    except ObjectDoesNotExist:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found")

    try:
        storage_settings = tenant.storage_settings
    except TenantStorageSettings.DoesNotExist:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Storage settings not found for this tenant")

    try:
        storage_settings.account_key = payload.account_key
        storage_settings.save()

        return StorageKeyUpdateOut(
            tenant_domain=tenant.domain,
            provider_name=storage_settings.provider_name,
            account_name=storage_settings.account_name,
            message="Storage key updated successfully"
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
