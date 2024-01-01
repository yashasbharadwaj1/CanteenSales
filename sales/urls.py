# urls.py
from django.urls import path
from .views import home, daily_sales, monthly_sales

app_name = "sales"

urlpatterns = [
    path('', home, name='home'),
    path('daily-sales/', daily_sales, name='daily_sales'),
    path('monthly-sales/', monthly_sales, name='monthly_sales'),
]
