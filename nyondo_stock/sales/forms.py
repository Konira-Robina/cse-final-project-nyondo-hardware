from django import forms
from .models import Cart, CartItem
from stock.models import Product
from nyondo_stock.validators import validate_ugandan_phone


class CartCustomerForm(forms.ModelForm):
    """Step 1 — Set customer details before adding items."""
    customer_phone = forms.CharField(
        required=False,
        validators=[validate_ugandan_phone],
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '0772123456 (optional)'
        })
    )

    class Meta:
        model = Cart
        fields = [
            'customer_name', 'customer_phone', 'customer_type',
            'delivery_requested', 'within_10km',
        ]
        widgets = {
            'customer_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Customer name (optional)'
            }),
            'customer_type': forms.Select(attrs={'class': 'form-select'}),
            'delivery_requested': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'within_10km': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class AddToCartForm(forms.Form):
    """Step 2 — Add a product to the cart."""
    product = forms.ModelChoiceField(
        queryset=Product.objects.filter(quantity_in_stock__gt=0),
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    quantity = forms.IntegerField(
        min_value=1,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )

    def clean(self):
        cleaned_data = super().clean()
        product = cleaned_data.get('product')
        quantity = cleaned_data.get('quantity')

        if product and quantity:
            if quantity > product.quantity_in_stock:
                raise forms.ValidationError(
                    f"Only {product.quantity_in_stock} {product.unit}(s) in stock."
                )
        return cleaned_data


class UpdateCartItemForm(forms.Form):
    """Update quantity of an item already in cart."""
    quantity = forms.IntegerField(
        min_value=1,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )

    def __init__(self, *args, **kwargs):
        self.cart_item = kwargs.pop('cart_item', None)
        super().__init__(*args, **kwargs)

    def clean_quantity(self):
        quantity = self.cleaned_data.get('quantity')
        if self.cart_item and quantity > self.cart_item.product.quantity_in_stock:
            raise forms.ValidationError(
                f"Only {self.cart_item.product.quantity_in_stock} "
                f"{self.cart_item.product.unit}(s) available."
            )
        return quantity