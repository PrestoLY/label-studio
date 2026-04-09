from analytics import api
from django.urls import path

app_name = 'analytics'

urlpatterns = [
    path('dashboard/', api.ProductivityDashboardAPI.as_view(), name='dashboard'),
    path('export/', api.ProductivityExportAPI.as_view(), name='export'),
]
