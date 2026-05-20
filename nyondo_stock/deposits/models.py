from django.db import models
from stock.models import Product

# Create your models here.



class DepositCustomer(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    nin = models.CharField(max_length=14, unique=True)   # National ID Number
    phone = models.CharField(max_length=15)
    address = models.TextField(blank=True)
    employer = models.CharField(max_length=200, blank=True)
    registration_date = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.nin})"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    def total_deposited(self):
        return sum(d.amount for d in self.deposits.all())


class DepositRecord(models.Model):
    customer = models.ForeignKey(DepositCustomer, on_delete=models.CASCADE, related_name='deposits')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, limit_choices_to={'is_deposit_eligible': True})
    amount_paid = models.DecimalField(max_digits=14, decimal_places=2)
    receipt_number = models.CharField(max_length=20, unique=True, editable=False)
    payment_date = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"{self.customer.full_name} — {self.amount_paid} UGX on {self.payment_date.strftime('%d/%m/%Y')}"

    def save(self, *args, **kwargs):
        if not self.receipt_number:
            import datetime
            today = datetime.date.today().strftime('%Y%m%d')
            last = DepositRecord.objects.filter(
                receipt_number__startswith=f'DEP-{today}'
            ).count()
            self.receipt_number = f'DEP-{today}-{str(last + 1).zfill(4)}'
        super().save(*args, **kwargs)


class GoodsPickup(models.Model):
    deposit = models.ForeignKey(DepositRecord, on_delete=models.CASCADE, related_name='pickups')
    quantity_picked = models.PositiveIntegerField()
    amount_used = models.DecimalField(max_digits=14, decimal_places=2)
    pickup_date = models.DateTimeField(auto_now_add=True)
    served_by = models.CharField(max_length=100)
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"Pickup by {self.deposit.customer.full_name} on {self.pickup_date.strftime('%d/%m/%Y')}"