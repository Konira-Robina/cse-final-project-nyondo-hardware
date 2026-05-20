from django.db import models
from stock.models import Product, Category


class Supplier(models.Model):
    name = models.CharField(max_length=200)
    contact_person = models.CharField(max_length=100, blank=True)
    phone = models.CharField(max_length=15)
    address = models.TextField(blank=True)
    date_added = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class SupplierDelivery(models.Model):
    PAYMENT_CHOICES = [
        ('cash', 'Cash — Paid Immediately'),
        ('credit', 'Credit — Pay Later'),
    ]

    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, related_name='deliveries')
    delivery_date = models.DateField()
    payment_type = models.CharField(max_length=10, choices=PAYMENT_CHOICES, default='cash')
    notes = models.TextField(blank=True)
    recorded_by = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return f"{self.supplier.name} — {self.delivery_date} ({self.get_payment_type_display()})"

    @property
    def total_amount(self):
        return sum(item.line_total for item in self.items.all())

    @property
    def is_credit(self):
        return self.payment_type == 'credit'


class SupplierDeliveryItem(models.Model):
    """
    Each row is one product in a delivery.
    Automatically updates stock when saved.
    """
    delivery = models.ForeignKey(SupplierDelivery, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    unit_cost = models.DecimalField(max_digits=12, decimal_places=2)
    wholesale_price = models.DecimalField(max_digits=12, decimal_places=2)
    retailer_price = models.DecimalField(max_digits=12, decimal_places=2)
    retail_price = models.DecimalField(max_digits=12, decimal_places=2)
    line_total = models.DecimalField(max_digits=14, decimal_places=2, editable=False)

    def __str__(self):
        return f"{self.quantity} × {self.product.name}"

    def clean(self):
        from django.core.exceptions import ValidationError
        errors = {}
        if self.wholesale_price <= self.unit_cost:
            errors['wholesale_price'] = "Wholesale price must exceed unit cost."
        if self.retailer_price <= self.unit_cost:
            errors['retailer_price'] = "Retailer price must exceed unit cost."
        if self.retail_price <= self.unit_cost:
            errors['retail_price'] = "Retail price must exceed unit cost."
        if self.wholesale_price >= self.retailer_price:
            errors['wholesale_price'] = "Wholesale price must be less than retailer price."
        if self.retailer_price >= self.retail_price:
            errors['retailer_price'] = "Retailer price must be less than individual retail price."
        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        # Calculate line total
        self.line_total = self.quantity * self.unit_cost

        # Update the product's prices and stock quantity
        self.product.unit_cost = self.unit_cost
        self.product.wholesale_price = self.wholesale_price
        self.product.retailer_price = self.retailer_price
        self.product.retail_price = self.retail_price
        self.product.quantity_in_stock += self.quantity
        self.product.save()

        super().save(*args, **kwargs)


class SupplierCreditAccount(models.Model):
    """
    Created automatically when a credit delivery is made.
    Tracks the outstanding balance for that delivery.
    """
    delivery = models.OneToOneField(
        SupplierDelivery,
        on_delete=models.CASCADE,
        related_name='credit_account'
    )
    total_amount = models.DecimalField(max_digits=14, decimal_places=2)
    amount_paid = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    due_date = models.DateField(null=True, blank=True)
    is_cleared = models.BooleanField(default=False)

    def __str__(self):
        return f"Credit — {self.delivery.supplier.name} | Balance: {self.balance_due}"

    @property
    def balance_due(self):
        return self.total_amount - self.amount_paid

    def save(self, *args, **kwargs):
        self.is_cleared = self.balance_due <= 0
        super().save(*args, **kwargs)


class SupplierPayment(models.Model):
    """
    Records each payment made towards a credit account.
    """
    credit_account = models.ForeignKey(
        SupplierCreditAccount,
        on_delete=models.CASCADE,
        related_name='payments'
    )
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    payment_date = models.DateField(auto_now_add=True)
    received_by = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"Payment of {self.amount} UGX on {self.payment_date}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Update the credit account balance after every payment
        account = self.credit_account
        account.amount_paid = sum(p.amount for p in account.payments.all())
        account.save()