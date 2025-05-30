from django.urls import path
from . import views

app_name = 'ipos'

urlpatterns = [
    # IPO listing and details
    path('', views.IPOListView.as_view(), name='list'),
    path('<int:id>/', views.IPODetailView.as_view(), name='detail'),
    
    # IPO categories and statistics
    path('categories/', views.ipo_categories_view, name='categories'),
    path('statistics/', views.ipo_statistics_view, name='statistics'),
    path('search/', views.ipo_search_view, name='search'),
    
    # Admin endpoints
    path('create/', views.IPOCreateView.as_view(), name='create'),
    path('<int:id>/update/', views.IPOUpdateView.as_view(), name='update'),
    path('<int:ipo_id>/update-status/', views.update_ipo_status_view, name='update_status'),
]