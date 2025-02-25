
from django.utils.deprecation import MiddlewareMixin
from tenants.models import Tenant
from tenants.database_router import set_tenant_db

class TenantMiddleware(MiddlewareMixin):
    """
    Middleware that sets the correct database for the tenant based on the request's domain.
    """

    def process_request(self, request):
        """ Identify tenant from subdomain and switch database. """
        hostname = request.get_host().split(":")[0]  # Get the host
        tenant_name = hostname.split(".")[0]  # Extract the subdomain
        
        try:
            tenant = Tenant.objects.get(tenant_id=tenant_name)
            set_tenant_db(tenant.tenant_id)  # Use tenant ID as the database name
        except Tenant.DoesNotExist:
            set_tenant_db("default")  # Default to central database if no match
