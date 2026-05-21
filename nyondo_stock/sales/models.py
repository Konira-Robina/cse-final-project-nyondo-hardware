from django.db import models
from django.db import models
from django.contrib.auth.models import User
from stock.models import Product
# Create your models here.

class Sale(models.Model):
    CUSTOMER_TYPE_CHOICES = [
        ('wholesaler', 'Wholesaler'),
        ('retailer', 'Retailer'),
        ('individual', 'Individual Buyer'),
    ]

    TRANSPORT_CHOICES = [
        ('free', 'Free (within 10km, ≥500,000 UGX)'),
        ('charged', 'Charged (+30,000 UGX)'),
        ('none', 'No delivery'),
    ]

    receipt_number = models.CharField(max_length=20, unique=True, editable=False)
    served_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    customer_name = models.CharField(max_length=200, blank=True)
    customer_phone = models.CharField(max_length=15, blank=True)
    customer_type = models.CharField(max_length=15, choices=CUSTOMER_TYPE_CHOICES, default='individual')
    delivery_requested = models.BooleanField(default=False)
    within_10km = models.BooleanField(default=False)
    transport_charge = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    transport_status = models.CharField(max_length=10, choices=TRANSPORT_CHOICES, default='none')
    subtotal = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    grand_total = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    sale_date = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"Receipt #{self.receipt_number} — {self.sale_date.strftime('%d/%m/%Y')}"

    def save(self, *args, **kwargs):
        if not self.receipt_number:
            import datetime
            today = datetime.date.today().strftime('%Y%m%d')
            last = Sale.objects.filter(
                receipt_number__startswith=f'REC-{today}'
            ).count()
            self.receipt_number = f'REC-{today}-{str(last + 1).zfill(4)}'

        if self.delivery_requested:
            if self.within_10km and self.subtotal >= 500000:
                self.transport_charge = 0
                self.transport_status = 'free'
            else:
                self.transport_charge = 30000
                self.transport_status = 'charged'
        else:
            self.transport_charge = 0
            self.transport_status = 'none'

        self.grand_total = self.subtotal + self.transport_charge
        super().save(*args, **kwargs)

class SaleItem(models.Model):
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=12, decimal_places=2, editable=False)
    line_total = models.DecimalField(max_digits=14, decimal_places=2, editable=False)

    def save(self, *args, **kwargs):
        # Automatically apply correct price based on customer type
        self.unit_price = self.product.get_price_for(self.sale.customer_type)
        self.line_total = self.quantity * self.unit_price
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.quantity} × {self.product.name} @ {self.unit_price}"
    
class Cart(models.Model):
    attendant = models.OneToOneField(User, on_delete=models.CASCADE, related_name='cart')
    customer_name = models.CharField(max_length=200, blank=True)
    customer_phone = models.CharField(max_length=15, blank=True)
    customer_type = models.CharField(
        max_length=15,
        choices=[
            ('wholesaler', 'Wholesaler'),
            ('retailer', 'Retailer'),
            ('individual', 'Individual Buyer'),
        ],
        default='individual'
    )
    delivery_requested = models.BooleanField(default=False)
    within_10km = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Cart — {self.attendant.get_full_name()}"

    @property
    def subtotal(self):
        return sum(item.line_total for item in self.cart_items.all())

    @property
    def transport_charge(self):
        if self.delivery_requested:
            if self.within_10km and self.subtotal >= 500000:
                return 0
            return 30000
        return 0

    @property
    def transport_status(self):
        if not self.delivery_requested:
            return 'none'
        if self.within_10km and self.subtotal >= 500000:
            return 'free'
        return 'charged'

    @property
    def grand_total(self):
        return self.subtotal + self.transport_charge

    @property
    def item_count(self):
        return self.cart_items.count()

    def is_empty(self):
        return self.item_count == 0

    def clear(self):
        self.cart_items.all().delete()
        self.customer_name = ''
        self.customer_phone = ''
        self.customer_type = 'individual'
        self.delivery_requested = False
        self.within_10km = False
        self.save()


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='cart_items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.quantity} × {self.product.name}"

    @property
    def unit_price(self):
        return self.product.get_price_for(self.cart.customer_type)

    @property
    def line_total(self):
        return self.quantity * self.unit_price

    class Meta:
        # One product per cart — adding same product updates quantity instead
        unique_together = ('cart', 'product')
