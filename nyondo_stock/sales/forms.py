from django import forms
from .models import Cart, CartItem
from stock.models import Product
from validators import validate_ugandan_phone


class CartCustomerForm(forms.ModelForm):
    customer_phone = forms.CharField(
        required=False,
        validators=[validate_ugandan_phone],
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '0772123456 (optional)'
        }),
        error_messages={
            'invalid': 'Enter a valid Ugandan phone number.'
        }
    )

    class Meta:
        model = Cart
        fields = [
            'customer_name', 'customer_phone',
            'customer_type', 'delivery_requested', 'within_10km',
        ]
        widgets = {
            'customer_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Customer name (optional)'
            }),
            'customer_type': forms.Select(attrs={'class': 'form-select'}),
            'delivery_requested': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'within_10km': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }


class AddToCartForm(forms.Form):
    product = forms.ModelChoiceField(
        queryset=Product.objects.filter(quantity_in_stock__gt=0),
        empty_label='— Select a product —',
        widget=forms.Select(attrs={'class': 'form-select'}),
        error_messages={
            'required': 'Please select a product.',
            'invalid_choice': 'Selected product is not available.',
        }
    )
    quantity = forms.IntegerField(
        min_value=1,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter quantity',
            'min': 1,
        }),
        error_messages={
            'required': 'Quantity is required.',
            'invalid': 'Enter a valid whole number.',
            'min_value': 'Quantity must be at least 1.',
        }
    )

    def clean(self):
        cleaned_data = super().clean()
        product = cleaned_data.get('product')
        quantity = cleaned_data.get('quantity')

        if product and quantity:
            if quantity > product.quantity_in_stock:
                raise forms.ValidationError(
                    f"Only {product.quantity_in_stock} "
                    f"{product.get_unit_display()}(s) available in stock. "
                    f"You requested {quantity}."
                )
        return cleaned_data


class UpdateCartItemForm(forms.Form):
    quantity = forms.IntegerField(
        min_value=1,
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
        error_messages={
            'required': 'Quantity is required.',
            'min_value': 'Quantity must be at least 1.',
        }
    )

    def __init__(self, *args, **kwargs):
        self.cart_item = kwargs.pop('cart_item', None)
        super().__init__(*args, **kwargs)

    def clean_quantity(self):
        quantity = self.cleaned_data.get('quantity')
        if self.cart_item and quantity:
            if quantity > self.cart_item.product.quantity_in_stock:
                raise forms.ValidationError(
                    f"Only {self.cart_item.product.quantity_in_stock} "
                    f"{self.cart_item.product.get_unit_display()}(s) available."
                )
        return quantity