from django.contrib import admin
from .models import Product,Inventory,Sales,Expenditure
from django.contrib.auth.models import User
from django.contrib.auth.models import Group
# Register your models here.
admin.site.register(Product)
admin.site.register(Inventory) 
admin.site.register(Sales)
admin.site.register(Expenditure)

admin.site.site_title = "Canteen Administration"
admin.site.site_header = "Canteen Admin"
admin.site.index_title = "Administration"

# unregister
admin.site.unregister(User)
admin.site.unregister(Group)
