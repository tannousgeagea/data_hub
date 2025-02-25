from threading import local
from tenants.models import Tenant

_thread_local = local()

class TenantRouter:
    """
    Routes database operations to the correct tenant database.
    """
    route_app_labels = {"auth", "users", "contenttypes", 'sessions', 'admin', "tenants"}

    def db_for_read(self, model, **hints):
        """ Directs read operations to the current tenant's database. """
        if model._meta.app_label in self.route_app_labels:
            return "default"
        return getattr(_thread_local, "TENANT_DB", "default")

    def db_for_write(self, model, **hints):
        """ Directs write operations to the current tenant's database. """
        if model._meta.app_label in self.route_app_labels:
            return 'default'
        return getattr(_thread_local, "TENANT_DB", "default")

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        """ Ensures that migrations only apply to the correct database. """
        if db == "default":
            return app_label in self.route_app_labels
        return db == getattr(_thread_local, "TENANT_DB", None)

def set_tenant_db(db_name):
    """
    Set the database dynamically for ORM queries.
    """
    _thread_local.TENANT_DB = db_name
