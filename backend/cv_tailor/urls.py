"""
URL configuration for cv_tailor project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/auth/', include('accounts.urls')),
    path('api/v1/artifacts/', include('artifacts.urls')),
    path('api/v1/generate/', include('generation.urls')),
    path('api/v1/export/', include('export.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)