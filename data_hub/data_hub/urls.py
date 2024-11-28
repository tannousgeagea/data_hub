"""
URL configuration for data_hub project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.contrib.auth.views import LoginView, LogoutView
from django.conf.urls.static import static
from metadata.views import metadata_management, add_language, get_tenant_tables, get_tenant_table_fields

urlpatterns = [
    path('admin/', admin.site.urls),
    path('metadata/', view=metadata_management, name='metadata_management'),
    path('api/languages/', add_language, name='add_language'),
    path('api/tenants/<str:tenant_id>/tables/', get_tenant_tables, name='get_tenant_tables'),
    path('api/tenants/<str:tenant_id>/table-types/<int:table_type_id>/fields/', get_tenant_table_fields, name='get_tenant_table_fields'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(next_page='login'), name='logout'),
    path('accounts/', include('django.contrib.auth.urls')),
]

urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)