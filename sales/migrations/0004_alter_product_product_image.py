# Generated by Django 5.0 on 2024-01-20 05:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sales', '0003_product_product_image'),
    ]

    operations = [
        migrations.AlterField(
            model_name='product',
            name='product_image',
            field=models.ImageField(upload_to='products/'),
        ),
    ]
