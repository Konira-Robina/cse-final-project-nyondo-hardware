import re
from django.core.exceptions import ValidationError


def validate_ugandan_phone(value):
    """
    Valid formats:
    +256700000000, +256772000000, 0700000000, 0772000000
    Prefixes: 07XX and 06XX
    """
    pattern = r'^(\+256|0)(7|6)\d{8}$'
    if not re.match(pattern, value):
        raise ValidationError(
            "Enter a valid Ugandan phone number e.g. 0772123456 or +256772123456."
        )


def validate_nin(value):
    """
    Uganda NIN format: 14 alphanumeric characters
    Starts with CM (male) or CF (female)
    Example: CM90001234ABCD
    """
    pattern = r'^(CM|CF)[A-Z0-9]{12}$'
    if not re.match(pattern.upper(), value.upper()):
        raise ValidationError(
            "Enter a valid NIN. Format: CM or CF followed by 12 alphanumeric characters e.g. CM90001234ABCD."
        )


def validate_selling_price(wholesale, retailer, retail, cost):
    """
    Reusable price hierarchy validator.
    Called manually in form clean() methods.
    """
    errors = {}
    if wholesale <= cost:
        errors['wholesale_price'] = "Wholesale price must be greater than unit cost."
    if retailer <= cost:
        errors['retailer_price'] = "Retailer price must be greater than unit cost."
    if retail <= cost:
        errors['retail_price'] = "Retail price must be greater than unit cost."
    if wholesale >= retailer:
        errors['wholesale_price'] = "Wholesale price must be less than retailer price."
    if retailer >= retail:
        errors['retailer_price'] = "Retailer price must be less than individual retail price."
    return errors