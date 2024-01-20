# urls.py
from django.urls import path
from .views import home, generate_daily_profit,generate_monthly_profit,download_excel,reports

app_name = "sales"

urlpatterns = [
    path('', home, name='home'),
    path('reports/',reports,name='reports'),
    path('api/generate-daily-profit/', generate_daily_profit, name='generate_daily_profit'),
    path('api/generate-monthly-profit/', generate_monthly_profit, name='generate_monthly_profit'),
    path('api/download-excel/', download_excel, name='download_excel'), 
]
