from .models import Notification


# ── Stock ──────────────────────────────────────────────────────

def notify_low_stock(product):
    """Triggered when stock drops at or below threshold."""
    Notification.notify(
        category='low_stock',
        title=f'Low stock — {product.name}',
        message=(
            f'{product.name} has only {product.quantity_in_stock} '
            f'{product.get_unit_display()}(s) left in stock. '
            f'Threshold is {product.low_stock_threshold}.'
        ),
        level='danger',
        link='/stock/',
        target_role='store_manager',
    )


# ── Sales ──────────────────────────────────────────────────────

def notify_new_sale(sale):
    """Triggered when a sale is confirmed."""
    Notification.notify(
        category='new_sale',
        title=f'New sale — Receipt #{sale.receipt_number}',
        message=(
            f'A new sale of UGX {sale.grand_total:,.0f} was recorded '
            f'for {sale.get_customer_type_display()} '
            f'{sale.customer_name or "Walk-in"} '
            f'by {sale.served_by.get_full_name()}.'
        ),
        level='success',
        link=f'/sales/receipt/{sale.pk}/',
        target_role='store_manager',
    )


# ── Supplier & Credit ──────────────────────────────────────────

def notify_new_delivery(delivery):
    """Triggered when a new supplier delivery is recorded."""
    Notification.notify(
        category='new_delivery',
        title=f'New delivery — {delivery.supplier.name}',
        message=(
            f'A new {"credit" if delivery.is_credit else "cash"} delivery '
            f'from {delivery.supplier.name} worth '
            f'UGX {delivery.total_amount:,.0f} was recorded on '
            f'{delivery.delivery_date.strftime("%d %b %Y")}.'
        ),
        level='info',
        link=f'/suppliers/deliveries/{delivery.pk}/',
        target_role='admin',
    )


def notify_overdue_credit(credit):
    """Triggered when a credit account passes its due date unpaid."""
    Notification.notify(
        category='overdue_credit',
        title=f'Overdue credit — {credit.delivery.supplier.name}',
        message=(
            f'Supplier credit from {credit.delivery.supplier.name} '
            f'is overdue. Balance due: UGX {credit.balance_due:,.0f}. '
            f'Due date was {credit.due_date.strftime("%d %b %Y")}.'
        ),
        level='danger',
        link=f'/suppliers/credits/{credit.pk}/pay/',
        target_role='admin',
    )


def notify_credit_payment(payment):
    """Triggered when a payment is made towards a credit account."""
    credit = payment.credit_account
    Notification.notify(
        category='credit_payment',
        title=f'Credit payment — {credit.delivery.supplier.name}',
        message=(
            f'Payment of UGX {payment.amount:,.0f} recorded for '
            f'{credit.delivery.supplier.name}. '
            f'Remaining balance: UGX {credit.balance_due:,.0f}.'
        ),
        level='success' if credit.is_cleared else 'info',
        link=f'/suppliers/deliveries/{credit.delivery.pk}/',
        target_role='admin',
    )


# ── Deposits ───────────────────────────────────────────────────

def notify_new_deposit(deposit):
    """Triggered when a deposit payment is recorded."""
    Notification.notify(
        category='new_deposit',
        title=f'New deposit — {deposit.customer.full_name}',
        message=(
            f'{deposit.customer.full_name} deposited '
            f'UGX {deposit.amount_paid:,.0f} for '
            f'{deposit.product.name}. '
            f'Receipt #{deposit.receipt_number}.'
        ),
        level='info',
        link=f'/deposits/{deposit.customer.pk}/',
        target_role='admin',
    )

def notify_deposit_ready(deposit):
    """
    Only fires when the customer has fully paid
    the target amount for their specific deposit.
    """
    customer = deposit.customer
    product = deposit.product

    # Use the deposit's target amount — not just the product unit price
    total_paid_for_product = sum(
        d.amount_paid for d in customer.deposits.filter(
            product=product
        )
    )

    # Only notify when fully paid
    if total_paid_for_product >= deposit.target_amount:
        Notification.notify(
            category='deposit_ready',
            title=f'Ready for pickup — {customer.full_name}',
            message=(
                f'{customer.full_name} has fully paid '
                f'UGX {total_paid_for_product:,.0f} for '
                f'{deposit.target_quantity} {product.get_unit_display()}(s) '
                f'of {product.name}. '
                f'Please prepare the goods for collection.'
            ),
            level='warning',
            link=f'/deposits/{customer.pk}/',
            target_role='sales_attendant',
        )