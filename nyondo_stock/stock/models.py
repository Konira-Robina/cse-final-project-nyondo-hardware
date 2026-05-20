from django.db import models
from django.core.exceptions import ValidationError

# Create your models here.
class Category(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Categories"


class Product(models.Model):
    UNIT_CHOICES = [
        ('bag', 'Bag'),
        ('bar', 'Bar'),
        ('kg', 'Kilogram'),
        ('piece', 'Piece'),
        ('roll', 'Roll'),
        ('sheet', 'Sheet'),
        ('bundle', 'Bundle'),
    ]

    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    unit = models.CharField(max_length=20, choices=UNIT_CHOICES)
    unit_cost = models.DecimalField(max_digits=12, decimal_places=2)

    # Tiered selling prices
    wholesale_price = models.DecimalField(max_digits=12, decimal_places=2)
    retailer_price = models.DecimalField(max_digits=12, decimal_places=2)
    retail_price = models.DecimalField(max_digits=12, decimal_places=2)  # individual buyer

    quantity_in_stock = models.PositiveIntegerField(default=0)
    low_stock_threshold = models.PositiveIntegerField(default=10)
    is_deposit_eligible = models.BooleanField(default=False)
    date_added = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    def is_low_stock(self):
        return self.quantity_in_stock <= self.low_stock_threshold

    def get_price_for(self, customer_type):
        prices = {
            'wholesaler': self.wholesale_price,
            'retailer': self.retailer_price,
            'individual': self.retail_price,
        }
        return prices.get(customer_type, self.retail_price)

    def clean(self):
        from django.core.exceptions import ValidationError
        errors = {}
        if self.wholesale_price <= self.unit_cost:
            errors['wholesale_price'] = "Wholesale price must be greater than unit cost."
        if self.retailer_price <= self.unit_cost:
            errors['retailer_price'] = "Retailer price must be greater than unit cost."
        if self.retail_price <= self.unit_cost:
            errors['retail_price'] = "Retail price must be greater than unit cost."
        if self.wholesale_price >= self.retailer_price:
            errors['wholesale_price'] = "Wholesale price must be less than retailer price."
        if self.retailer_price >= self.retail_price:
            errors['retailer_price'] = "Retailer price must be less than individual retail price."
        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return self.name

    def is_low_stock(self):
        return self.quantity_in_stock <= self.low_stock_threshold

    def clean(self):
        
        if self.selling_price <= self.unit_cost:
            raise ValidationError("Selling price must be greater than unit cost.")

