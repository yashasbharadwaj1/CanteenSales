# urls.py
app_name = "sales"
from django.urls import path
from .views import api_daily_profit, api_monthly_profit

urlpatterns = [
    path('daily-profit/', api_daily_profit, name='api_daily_profit'),
    path('monthly-profit/<int:month>/', api_monthly_profit, name='api_monthly_profit'),
]
