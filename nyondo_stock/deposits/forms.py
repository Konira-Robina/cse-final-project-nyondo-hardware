from django import forms
from .models import DepositCustomer, DepositRecord
from validators import validate_ugandan_phone, validate_nin


class DepositCustomerForm(forms.ModelForm):
    phone = forms.CharField(
        validators=[validate_ugandan_phone],
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '0772123456'
        }),
        error_messages={
            'required': 'Phone number is required.',
        }
    )
    nin = forms.CharField(
        validators=[validate_nin],
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'CM90001234ABCD'
        }),
        error_messages={
            'required': 'NIN is required.',
        }
    )

    class Meta:
        model = DepositCustomer
        fields = [
            'first_name', 'last_name', 'nin',
            'phone', 'address', 'employer',
        ]
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={
                'class': 'form-control', 'rows': 2
            }),
            'employer': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Employer / Organisation'
            }),
        }
        error_messages = {
            'first_name': {'required': 'First name is required.'},
            'last_name': {'required': 'Last name is required.'},
        }

    def clean_nin(self):
        nin = self.cleaned_data.get('nin', '').upper().strip()
        qs = DepositCustomer.objects.filter(nin=nin)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError(
                "A customer with this NIN is already registered."
            )
        return nin

    def clean_first_name(self):
        name = self.cleaned_data.get('first_name', '').strip()
        if not name:
            raise forms.ValidationError("First name is required.")
        return name

    def clean_last_name(self):
        name = self.cleaned_data.get('last_name', '').strip()
        if not name:
            raise forms.ValidationError("Last name is required.")
        return name


class DepositRecordForm(forms.ModelForm):
    class Meta:
        model = DepositRecord
        fields = ['product', 'target_quantity', 'amount_paid', 'notes']
        widgets = {
            'product': forms.Select(attrs={'class': 'form-select'}),
            'target_quantity': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. 50',
                'min': 1,
            }),
            'amount_paid': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'UGX',
                'min': 1,
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control', 'rows': 2
            }),
        }
        error_messages = {
            'product': {'required': 'Please select a product.'},
            'target_quantity': {
                'required': 'Target quantity is required.',
                'invalid': 'Enter a valid whole number.',
                'min_value': 'Quantity must be at least 1.',
            },
            'amount_paid': {
                'required': 'Amount paid is required.',
                'invalid': 'Enter a valid amount.',
            },
        }

    def clean_target_quantity(self):
        qty = self.cleaned_data.get('target_quantity')
        if qty is not None and qty <= 0:
            raise forms.ValidationError(
                "Target quantity must be greater than zero."
            )
        return qty

    def clean_amount_paid(self):
        amount = self.cleaned_data.get('amount_paid')
        if amount is not None and amount <= 0:
            raise forms.ValidationError(
                "Amount paid must be greater than zero."
            )
        return amount

    def clean(self):
        cleaned_data = super().clean()
        product = cleaned_data.get('product')
        target_quantity = cleaned_data.get('target_quantity')
        amount_paid = cleaned_data.get('amount_paid')

        if product and target_quantity:
            target_amount = product.retail_price * target_quantity
            if amount_paid and amount_paid > target_amount:
                raise forms.ValidationError(
                    f"Amount paid (UGX {amount_paid:,.0f}) cannot exceed "
                    f"the target amount of UGX {target_amount:,.0f} "
                    f"for {target_quantity} {product.get_unit_display()}(s) "
                    f"of {product.name}."
                )
        return cleaned_data