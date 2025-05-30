from django.urls import path
from . import views

app_name = 'applications'

urlpatterns = [
    # Application CRUD
    path('', views.IPOApplicationListCreateView.as_view(), name='list_create'),
    path('<uuid:id>/', views.IPOApplicationDetailView.as_view(), name='detail'),
    path('<uuid:id>/update/', views.IPOApplicationUpdateView.as_view(), name='update'),
    path('<uuid:id>/cancel/', views.cancel_application_view, name='cancel'),
    
    # Application statistics
    path('stats/', views.application_stats_view, name='stats'),
    path('ipo/<int:ipo_id>/stats/', views.ipo_application_stats_view, name='ipo_stats'),
    
    # Document management
    path('<uuid:application_id>/documents/', views.ApplicationDocumentListCreateView.as_view(), name='documents'),
    path('documents/<int:document_id>/', views.ApplicationDocumentDetailView.as_view(), name='document_detail'),
]