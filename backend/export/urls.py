from django.urls import path
from . import views

urlpatterns = [
    path('<uuid:generation_id>/', views.export_document, name='export_document'),
    path('<uuid:export_id>/status/', views.export_status, name='export_status'),
    path('<uuid:export_id>/download/', views.download_export, name='download_export'),
    path('', views.UserExportsListView.as_view(), name='user_exports_list'),
    path('<uuid:pk>/detail/', views.ExportJobDetailView.as_view(), name='export_job_detail'),
    path('templates/', views.ExportTemplateListView.as_view(), name='export_templates_list'),
    path('analytics/', views.export_analytics, name='export_analytics'),
]