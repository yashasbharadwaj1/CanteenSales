import os
import logging
import requests
import tempfile
import pandas as pd
from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Inventory, Sales, Expenditure, Product
from datetime import datetime
from django.db.models import Sum
import boto3
from botocore.exceptions import NoCredentialsError
from dotenv import load_dotenv
import requests
from urllib.parse import unquote, urlencode, urlparse, urlunparse
from django.views.decorators.csrf import csrf_exempt
import json

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# AWS S3 Configuration
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_STORAGE_BUCKET_NAME = "canteensales"
AWS_REGION = "us-east-1"
S3_FOLDER_DAILY = "daily_reports/"
S3_FOLDER_MONTHLY = "monthly_reports/"
s3_client = boto3.client(
    "s3",
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name=AWS_REGION,
)


def generate_excel_file(data, filename):
    df = pd.DataFrame(data)
    temp_dir = tempfile.mkdtemp()
    # Save the Excel file in the temporary directory
    excel_file_path = os.path.join(temp_dir, f"{filename}.xlsx")
    df.to_excel(excel_file_path, index=False)
    return excel_file_path


def upload_to_s3(local_file_path, s3_folder, s3_filename):
    try:
        s3_client.upload_file(
            local_file_path, AWS_STORAGE_BUCKET_NAME, f"{s3_folder}{s3_filename}"
        )
        return True
    except NoCredentialsError:
        logger.error("Credentials not available")
        return False


def calculate_daily_profit(date):
    results = []
    inventories = Inventory.objects.filter(date=date)

    if not inventories.exists():
        return None

    for inventory in inventories:
        sales = Sales.objects.filter(date=date, product=inventory.product).aggregate(
            Sum("pieces_sold")
        )
        pieces_sold_sum = sales["pieces_sold__sum"] or 0
        total_selling_price = pieces_sold_sum * inventory.selling_price_per_piece
        total_cost_price = pieces_sold_sum * inventory.cost_price_per_piece
        profit = total_selling_price - total_cost_price

        result = {
            "product_name": inventory.product.name,
            "date": inventory.date.strftime("%d/%m/%Y"),
            "pieces_sold": pieces_sold_sum,
            "pieces": inventory.total_pieces,
            "cost_price_per_piece": inventory.cost_price_per_piece,
            "selling_price_per_piece": inventory.selling_price_per_piece,
            "total_selling_price": total_selling_price,
            "total_cost_price": total_cost_price,
            "profit": profit,
        }

        results.append(result)
    date_str = date.strftime("%d/%m/%Y")
    total_result = {
        "product_name": "all",
        "date": date_str,
        "pieces_sold": sum(entry["pieces_sold"] for entry in results),
        "pieces": sum(entry["pieces"] for entry in results),
        "cost_price_per_piece": sum(entry["cost_price_per_piece"] for entry in results),
        "selling_price_per_piece": sum(
            entry["selling_price_per_piece"] for entry in results
        ),
        "total_selling_price": sum(entry["total_selling_price"] for entry in results),
        "total_cost_price": sum(entry["total_cost_price"] for entry in results),
        "profit": sum(entry["profit"] for entry in results),
    }
    results.append(total_result)
    return results


def calculate_actual_profit_for_month(month, year):
    results = []
    total_pieces_sold_sum = 0

    for product in Product.objects.all():
        # Retrieve the related Inventory for the Product
        inventory = Inventory.objects.filter(product=product).first()

        # If there is no related Inventory, skip this product
        if not inventory:
            continue

        # Fetch expenditures for the specific product, month, and year
        expenditures = Expenditure.objects.filter(date__month=month, date__year=year)
        aggregated_result = expenditures.aggregate(Sum("amount_spent"))
        total_expenditure_raw = aggregated_result["amount_spent__sum"]
        total_expenditure = total_expenditure_raw or 0
        total_expenditure = round(total_expenditure, 2)

        total_pieces = inventory.total_pieces
        cost_price_per_piece = inventory.cost_price_per_piece
        selling_price_per_piece = inventory.selling_price_per_piece

        sales = Sales.objects.filter(date__month=month, product=product).aggregate(
            Sum("pieces_sold")
        )
        pieces_sold_sum = sales["pieces_sold__sum"] or 0
        if pieces_sold_sum == 0 and total_expenditure == 0:
            continue
        total_pieces_sold_sum += pieces_sold_sum
        total_selling_price = pieces_sold_sum * selling_price_per_piece
        total_cost_price = pieces_sold_sum * cost_price_per_piece
        total_profit = total_selling_price - total_cost_price

        result = {
            "year": year,
            "month": month,
            "product_name": product.name,
            "pieces": total_pieces,
            "cost_price_per_piece": cost_price_per_piece,
            "selling_price_per_piece": selling_price_per_piece,
            "pieces_sold": pieces_sold_sum,
            "total_selling_price": total_selling_price,
            "total_cost_price": total_cost_price,
            "profit": total_profit,
        }

        results.append(result)
    if total_pieces_sold_sum == 0:
        return None
    total_result = {
        "year": year,
        "month": month,
        "product_name": "all",
        "pieces": sum(entry["pieces"] for entry in results),
        "cost_price_per_piece": sum(entry["cost_price_per_piece"] for entry in results),
        "selling_price_per_piece": sum(
            entry["selling_price_per_piece"] for entry in results
        ),
        "pieces_sold": sum(entry["pieces_sold"] for entry in results),
        "total_selling_price": sum(entry["total_selling_price"] for entry in results),
        "total_cost_price": sum(entry["total_cost_price"] for entry in results),
        "profit": sum(entry["profit"] for entry in results),
        "total_expenditure": total_expenditure,
        "actual_profit": sum(entry["profit"] for entry in results) - total_expenditure,
    }
    results.append(total_result)
    return results


@csrf_exempt
def home(request):
    if request.method == "POST":
        selected_date = request.POST.get("selected_date")
        all_data_json = request.POST.get("all_data")
        all_data = json.loads(all_data_json)

        for data in all_data:
            product_id = data['productId']
            pieces_sold = int(data['piecesSold'])
            logger.info(
                f"Product ID: {data['productId']}, Pieces Sold: {data['piecesSold']}"
            )

            # Check if a Sales entry with the same date and product exists
            existing_entry = Sales.objects.filter(date=selected_date, product__id=product_id).first()

            if existing_entry:
                # Update existing entry by adding pieces_sold
                existing_entry.pieces_sold += pieces_sold
                existing_entry.save()
            else:
                # Create a new Sales entry
                product = Product.objects.get(id=product_id)
                sales_entry = Sales.objects.create(
                    date=selected_date,
                    product=product,
                    pieces_sold=pieces_sold
                )
                sales_entry.save()

        return render(request, "success.html", {"message": "Data saved successfully"})
    
    products = Product.objects.all()
    return render(request, "home.html", {"products": products})


@api_view(["POST", "GET"])
def generate_daily_profit(request):
    if request.method == "POST":
        try:
            date_str = request.POST.get("date")
            date = datetime.strptime(date_str, "%Y-%m-%d").date()
            filename = f"daily_report_{date}.xlsx"
            s3_key = f"{S3_FOLDER_DAILY}{filename}"

            # Check if the file exists in S3
            try:
                s3_client.head_object(Bucket=AWS_STORAGE_BUCKET_NAME, Key=s3_key)
                logger.info(f"{filename}.xlsx already exists")
                presigned_url = generate_presigned_url(s3_key)
                if presigned_url is not None:
                    return render(
                        request,
                        "daily_sales.html",
                        {"success": True, "presigned_url": presigned_url},
                    )
                else:
                    return JsonResponse({"msg": "unable to generate presigned url"})
            except:
                results = calculate_daily_profit(date)
                if results is None:
                    return JsonResponse(
                        {"message": f"Daily report not found  for {date}"}
                    )
                else:
                    excel_file_path = generate_excel_file(results, filename)
                    upload_to_s3(excel_file_path, S3_FOLDER_DAILY, f"{filename}")
                    presigned_url = generate_presigned_url(s3_key)
                    if presigned_url is not None:
                        return render(
                            request,
                            "daily_sales.html",
                            {"success": True, "presigned_url": presigned_url},
                        )
                    else:
                        return JsonResponse({"msg": "unable to generate presigned url"})
        except ValueError:
            logger.exception("Error in daily_sales: Invalid date format")
            return JsonResponse(
                {"success": False, "msg": "Invalid date format. Please use YYYY-MM-DD."}
            )
        except Exception as e:
            logger.exception(f"Error in daily_sales: {e}")
            return JsonResponse(
                {
                    "success": False,
                    "msg": "An error occurred while processing the request.",
                }
            )

    return render(request, "daily_sales.html", {"filename": ""})


@api_view(["POST", "GET"])
def generate_monthly_profit(request):
    if request.method == "POST":
        try:
            month = int(request.POST.get("month"))
            year = int(request.POST.get("year"))
            filename = f"monthly_report_{month}_{year}.xlsx"
            s3_key = f"{S3_FOLDER_MONTHLY}{filename}"
            # Check if the file exists in S3
            try:
                s3_client.head_object(Bucket=AWS_STORAGE_BUCKET_NAME, Key=s3_key)
                logger.info(f"{filename}.xlsx already exists")
                presigned_url = generate_presigned_url(s3_key)
                if presigned_url is not None:
                    return render(
                        request,
                        "monthly_sales.html",
                        {"success": True, "presigned_url": presigned_url},
                    )
                else:
                    return JsonResponse({"msg": "unable to generate presigned url"})
            except:
                results = calculate_actual_profit_for_month(month, year)
                if results is None:
                    return JsonResponse(
                        {"message": f"Monthly report not found for {month}_{year}"}
                    )
                else:
                    excel_file_path = generate_excel_file(results, filename)
                    upload_to_s3(excel_file_path, S3_FOLDER_MONTHLY, f"{filename}")
                    presigned_url = generate_presigned_url(s3_key)
                    if presigned_url is not None:
                        return render(
                            request,
                            "monthly_sales.html",
                            {"success": True, "presigned_url": presigned_url},
                        )
                    else:
                        return JsonResponse({"msg": "unable to generate presigned url"})
        except ValueError:
            logger.exception("Error in monthly_sales: Invalid month or year format")
            return JsonResponse(
                {"success": False, "msg": "Invalid month or year format."}
            )
        except Exception as e:
            logger.exception(f"Error in monthly_sales: {e}")
            return JsonResponse(
                {
                    "success": False,
                    "msg": "An error occurred while processing the request.",
                }
            )

    return render(request, "monthly_sales.html")


def reports(request):
    return render(request, "reports.html")


def download_excel(request):
    presigned_url = unquote(request.GET.get("presigned_url", ""))

    try:
        # Parse the presigned URL
        parsed_url = urlparse(presigned_url)

        # Extract and decode query parameters
        query_params = dict(qp.split("=", 1) for qp in parsed_url.query.split("&"))
        decoded_query_params = {k: unquote(v) for k, v in query_params.items()}

        # Reconstruct the URL with decoded query parameters
        decoded_presigned_url = urlunparse(
            parsed_url._replace(query=urlencode(decoded_query_params))
        )
        print("Decoded Presigned URL:", decoded_presigned_url)

        response = requests.get(decoded_presigned_url)

        if response.status_code == 200:
            # Set the content type and headers for the response
            content_type = response.headers.get(
                "Content-Type", "application/octet-stream"
            )
            content_disposition = 'attachment; filename="downloaded_file.xlsx"'

            # Create an HttpResponse with the file content
            response = HttpResponse(response.content, content_type=content_type)
            response["Content-Disposition"] = content_disposition
            return response
        else:
            print("Error Response Content:", response.content)
            print("Error Response Headers:", response.headers)
            return HttpResponse(
                f"Error downloading file. Status code: {response.status_code}",
                status=500,
            )
    except Exception as e:
        return HttpResponse(f"Error downloading file: {str(e)}", status=500)


def generate_presigned_url(s3_key):
    try:
        presigned_url = s3_client.generate_presigned_url(
            "get_object",
            Params={"Bucket": AWS_STORAGE_BUCKET_NAME, "Key": s3_key},
            ExpiresIn=3600,  # Set the expiration time (in seconds)
        )
        return presigned_url
    except Exception as e:
        logger.error(f"Error generating presigned URL for {s3_key}: {e}")
        return None
