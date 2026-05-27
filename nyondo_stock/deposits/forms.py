from django import forms
from .models import DepositCustomer, DepositRecord
from validators import validate_ugandan_phone, validate_nin


class DepositCustomerForm(forms.ModelForm):
    phone = forms.CharField(
        validators=[validate_ugandan_phone],
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '0772123456'
        })
    )
    nin = forms.CharField(
        validators=[validate_nin],
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'CM90001234ABCD'
        })
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

    def clean_nin(self):
        nin = self.cleaned_data.get('nin', '').upper()
        qs = DepositCustomer.objects.filter(nin=nin)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError(
                "A customer with this NIN is already registered."
            )
        return nin


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
                'placeholder': 'UGX'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control', 'rows': 2
            }),
        }

    def clean_target_quantity(self):
        qty = self.cleaned_data.get('target_quantity')
        if qty and qty <= 0:
            raise forms.ValidationError(
                "Target quantity must be greater than zero."
            )
        return qty

    def clean_amount_paid(self):
        amount = self.cleaned_data.get('amount_paid')
        if amount and amount <= 0:
            raise forms.ValidationError(
                "Amount must be greater than zero."
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
                    f"the target amount (UGX {target_amount:,.0f}) for "
                    f"{target_quantity} {product.get_unit_display()}(s) "
                    f"of {product.name}."
                )
        return cleaned_data