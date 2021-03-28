from django.db import models

class Customer(models.Model):
    name = models.CharField(max_length=50, null=True)
    telegram_id = models.PositiveIntegerField(null=True, unique=True)

    def __str__(self):
        return self.name

class Product(models.Model):
    name = models.CharField(max_length=100,null=True)
    price = models.FloatField(null=False)

    def __str__(self):
        return self.name

class Cart(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(null=False)

class Order(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(null=False)
    created_at = models.DateTimeField(auto_now_add=True)
    total = models.FloatField(null=False)
