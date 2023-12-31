from django.db import models

class Product(models.Model):
    name = models.CharField(max_length=255)
    class Meta:
        verbose_name_plural = "Products" 
    
    def __str__(self):
        return self.name

class Inventory(models.Model):
    date = models.DateField()
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    total_pieces = models.IntegerField()
    cost_price_per_piece = models.DecimalField(max_digits=5, decimal_places=2)
    selling_price_per_piece = models.DecimalField(max_digits=5, decimal_places=2)
    
    class Meta:
        verbose_name_plural = "Inventories"
    
    
    def __str__(self):
        date = self.date 
        product = self.product
        return f"{product}_{date}"

class Sales(models.Model):
    date = models.DateField()
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    pieces_sold = models.IntegerField()
    
    class Meta:
        verbose_name_plural = "Sales"
    def __str__(self):
        date = self.date 
        product = self.product
        return f"{product}_{date}"
    
    

class Expenditure(models.Model):
    date = models.DateField()
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    type = models.CharField(max_length=255)
    amount_spent = models.DecimalField(max_digits=8, decimal_places=2)
    def __str__(self):
        date = self.date 
        product = self.product
        return f"{product}_{date}"
    




