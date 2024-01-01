# views.py
import logging
from django.shortcuts import render
from django.http import JsonResponse
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Inventory, Sales, Expenditure, Product
from datetime import datetime
from django.db.models import Sum

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def calculate_daily_profit(date):
    results = []
    inventories = Inventory.objects.filter(date=date)

    for inventory in inventories:
        sales = Sales.objects.filter(date=inventory.date, product=inventory.product).aggregate(Sum('pieces_sold'))
        pieces_sold_sum = sales['pieces_sold__sum'] or 0
        total_selling_price = pieces_sold_sum * inventory.selling_price_per_piece
        total_cost_price = pieces_sold_sum * inventory.cost_price_per_piece
        profit = total_selling_price - total_cost_price

        result = {
            'product_name': inventory.product.name,
            'date': inventory.date.strftime("%d/%m/%Y"),
            'pieces_sold_sum': pieces_sold_sum,
            'total_pieces': inventory.total_pieces,
            'cost_price_per_piece': inventory.cost_price_per_piece,
            'selling_price_per_piece': inventory.selling_price_per_piece,
            'total_selling_price': total_selling_price,
            'total_cost_price': total_cost_price,
            'profit': profit,
        }

        results.append(result)

    return results


def calculate_actual_profit_for_month(month, year):
    results = []

    for product in Product.objects.all():
        # Retrieve the related Inventory for the Product
        inventory = Inventory.objects.filter(product=product).first()

        # If there is no related Inventory, skip this product
        if not inventory:
            continue

        # Fetch expenditures for the specific product, month, and year
        expenditures = Expenditure.objects.filter(product=product, date__month=month, date__year=year)
        aggregated_result = expenditures.aggregate(Sum('amount_spent'))
        total_expenditure_raw = aggregated_result['amount_spent__sum']
        total_expenditure = total_expenditure_raw or 0 
        total_expenditure = round(total_expenditure, 2)
        
        logger.info(f'Total expenditure for {product.name} in month {month}: {total_expenditure}')

        # Fetch additional information from the Inventory model
        total_pieces = inventory.total_pieces
        cost_price_per_piece = inventory.cost_price_per_piece
        selling_price_per_piece = inventory.selling_price_per_piece

        sales = Sales.objects.filter(date__month=month, product=product).aggregate(Sum('pieces_sold'))
        pieces_sold_sum = sales['pieces_sold__sum'] or 0
        logger.info(f'Monthly total pieces_sold_sum for {product.name} in month {month}: {pieces_sold_sum}')
        total_selling_price = pieces_sold_sum * selling_price_per_piece
        total_cost_price = pieces_sold_sum * cost_price_per_piece
        total_profit = total_selling_price - total_cost_price
        logger.info(f'Total profit for {product.name} in month {month}: {total_profit}')
        logger.info(f'Total selling price for {product.name} in month {month}: {total_selling_price}')
        logger.info(f'Total cost price for {product.name} in month {month}: {total_cost_price}')
        
        actual_profit = total_profit - total_expenditure
        logger.info(f'Actual profit for {product.name} in month {month}: {actual_profit}')

        result = {
            'year': year,
            'month': month,
            'product_name': product.name,
            'total_pieces': total_pieces,
            'cost_price_per_piece': cost_price_per_piece,
            'selling_price_per_piece': selling_price_per_piece,
            'pieces_sold_sum': pieces_sold_sum,
            'total_selling_price': total_selling_price,
            'total_cost_price': total_cost_price,
            'profit':total_profit,
            'total_expenditure': total_expenditure,
            'actual_profit': actual_profit,
        }

        results.append(result)

    return results


def home(request):
    return render(request, 'home.html')

def daily_sales(request):
    if request.method == 'POST':
        date_str = request.POST.get('date')
        date = datetime.strptime(date_str, '%Y-%m-%d').date()
        daily_profit = calculate_daily_profit(date)
        return render(request, 'daily_sales.html', {'daily_profit': daily_profit})
    return render(request, 'daily_sales.html')

def monthly_sales(request):
    if request.method == 'POST':
        month = int(request.POST.get('month'))
        year = int(request.POST.get('year'))
        monthly_profit = calculate_actual_profit_for_month(month, year)
        return render(request, 'monthly_sales.html', {'monthly_profit': monthly_profit})
    return render(request, 'monthly_sales.html')
