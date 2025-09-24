from django.urls import path
from . import views, editing_views

urlpatterns = [
    path('', views.ArtifactListCreateView.as_view(), name='artifact_list_create'),
    path('<int:pk>/', views.ArtifactDetailView.as_view(), name='artifact_detail'),
    path('<int:artifact_id>/upload/', views.upload_artifact_files, name='upload_artifact_files'),
    path('upload/', views.bulk_upload_artifacts, name='bulk_upload_artifacts'),
    path('<int:artifact_id>/status/', views.artifact_processing_status, name='artifact_processing_status'),
    path('upload-file/', views.upload_file, name='upload_file'),
    path('suggestions/', views.artifact_suggestions, name='artifact_suggestions'),

    # Artifact editing endpoints
    path('<int:artifact_id>/evidence-links/', editing_views.add_evidence_link, name='add_evidence_link'),
    path('evidence-links/<int:link_id>/', editing_views.evidence_link_detail, name='evidence_link_detail'),
    path('files/<uuid:file_id>/', editing_views.delete_artifact_file, name='delete_artifact_file'),
    path('bulk/', editing_views.bulk_update_artifacts, name='bulk_update_artifacts'),
]