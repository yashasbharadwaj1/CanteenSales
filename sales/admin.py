from django.contrib import admin
from .models import Product,Inventory,Sales,Expenditure
# Register your models here.
admin.site.register(Product)
admin.site.register(Inventory) 
admin.site.register(Sales)
admin.site.register(Expenditure)

