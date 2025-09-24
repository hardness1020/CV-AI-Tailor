from django.urls import path
from . import views

urlpatterns = [
    path('cv/', views.generate_cv, name='generate_cv'),
    path('<uuid:generation_id>/', views.generation_status, name='generation_status'),
    path('', views.UserGenerationsListView.as_view(), name='user_generations_list'),
    path('<uuid:pk>/detail/', views.GenerationDetailView.as_view(), name='generation_detail'),
    path('<uuid:generation_id>/rate/', views.rate_generation, name='rate_generation'),
    path('templates/', views.CVTemplateListView.as_view(), name='cv_templates_list'),
    path('analytics/', views.generation_analytics, name='generation_analytics'),
]