# views.py
from django.shortcuts import render
from django.http import JsonResponse
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Inventory, Sales, Expenditure, Product
from datetime import datetime
from django.db.models import Sum

def calculate_daily_profit():
    results = []
    inventories = Inventory.objects.all()
    
    for inventory in inventories:
        sales = Sales.objects.filter(date=inventory.date, product=inventory.product).aggregate(Sum('pieces_sold'))
        total_selling_price = sales['pieces_sold__sum'] * inventory.selling_price_per_piece
        total_cost_price = sales['pieces_sold__sum'] * inventory.cost_price_per_piece
        profit = total_selling_price - total_cost_price

        result = {
            'product_name': inventory.product.name,
            'date': inventory.date.strftime("%d/%m/%Y"),
            'total_selling_price': total_selling_price,
            'total_cost_price': total_cost_price,
            'profit': profit,
        }

        results.append(result)

    return results

def calculate_actual_profit_for_month(month):
    results = []
    expenditures = Expenditure.objects.filter(date__month=month)
    total_expenditure = expenditures.aggregate(Sum('amount_spent'))['amount_spent__sum'] or 0
    print(total_expenditure,"total_expenditure")

    for product in Product.objects.all():
        # Retrieve the related Inventory for the Product
        inventory = Inventory.objects.filter(product=product).first()

        # If there is no related Inventory, skip this product
        if not inventory:
            continue

        sales = Sales.objects.filter(date__month=month, product=product).aggregate(Sum('pieces_sold'))
        total_selling_price = sales['pieces_sold__sum'] * inventory.selling_price_per_piece if sales['pieces_sold__sum'] else 0
        total_cost_price = inventory.total_pieces * inventory.cost_price_per_piece
        #Actual profit  = Total Profit for the entire month - Total expenditure for the entire month 
        total_profit = total_selling_price - total_cost_price
        actual_profit= total_profit - total_expenditure
        print(total_selling_price) 

        result = {
            'product_name': product.name,
            'actual_profit': actual_profit,
        }

        results.append(result)

    return results




@api_view(['GET'])
def api_daily_profit(request):
    daily_profit = calculate_daily_profit()
    return Response({'daily_profit': daily_profit})

@api_view(['GET'])
def api_monthly_profit(request, month):
    actual_profit_month = calculate_actual_profit_for_month(month)
    return Response({'actual_profit_month': actual_profit_month})