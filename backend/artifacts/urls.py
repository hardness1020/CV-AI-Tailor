from django.urls import path
from . import views

urlpatterns = [
    path('', views.ArtifactListCreateView.as_view(), name='artifact_list_create'),
    path('<int:pk>/', views.ArtifactDetailView.as_view(), name='artifact_detail'),
    path('upload/', views.bulk_upload_artifacts, name='bulk_upload_artifacts'),
    path('<int:artifact_id>/status/', views.artifact_processing_status, name='artifact_processing_status'),
    path('upload-file/', views.upload_file, name='upload_file'),
    path('suggestions/', views.artifact_suggestions, name='artifact_suggestions'),
]