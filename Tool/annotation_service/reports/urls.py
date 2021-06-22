from reports.views import statistics
from django.urls import path

urlpatterns = [
    path('statistics', statistics, name='statistics'),
]
