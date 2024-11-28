from django.shortcuts import render

# Create your views here.
import json
from django.http import JsonResponse
from .models import Tenant, Language, TableType, TenantTable, TenantTableField
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required

def add_language(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        code = data.get('code')
        name = data.get('name')
        
        # Add validation if necessary
        if code and name:
            language, created = Language.objects.get_or_create(code=code, defaults={'name': name})
            if created:
                return JsonResponse({'status': 'success', 'message': 'Language added successfully!'})
            else:
                return JsonResponse({'status': 'error', 'message': 'Language already exists!'})
        return JsonResponse({'status': 'error', 'message': 'Invalid data'}, status=400)
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)

def get_tenant_tables(request, tenant_id):
    try:
        tenant_tables = TenantTable.objects.filter(tenant__tenant_id=tenant_id)  # Assuming tenant is linked via `name`
        tables_data = [{'id': table.id, 'type': table.table_type.name, 'description': table.description} for table in tenant_tables]
        
        return JsonResponse(tables_data, safe=False)
    except TenantTable.DoesNotExist:
        return JsonResponse({'error': 'Tenant not found or no tables available'}, status=404)


def get_tenant_table_fields(request, tenant_id, table_type_id):
    try:
        # Assuming `tenant_id` is the name or unique identifier of the tenant
        # Fetch the specific tenant's table of the specified type
        tenant_table = TenantTable.objects.get(tenant__tenant_id=tenant_id, table_type__id=table_type_id)
        
        # Retrieve the fields associated with this tenant table
        fields = TenantTableField.objects.filter(tenant_table=tenant_table)
        
        # Serialize the data
        fields_data = [{'id': field.id, 'name': field.field.name,'description': field.field.description, "type": field.field.type.type} for field in fields]
        
        return JsonResponse(fields_data, safe=False)
    
    except TenantTable.DoesNotExist:
        return JsonResponse({'error': 'Table not found for the specified tenant and table type'}, status=404)


@login_required(login_url='/login/')
def metadata_management(request):
    # Fetch initial data to populate dropdowns
    tenants = Tenant.objects.all()
    languages = Language.objects.all()
    table_types = TableType.objects.all()

    context = {
        'tenants': tenants,
        'languages': languages,
        'table_types': table_types,
    }
    
    return render(request, 'metadata/metadata_management.html', context)


