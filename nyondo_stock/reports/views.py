from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count, F, Q
from django.db.models.functions import TruncDay, TruncWeek, TruncMonth
from django.utils import timezone
from datetime import date, timedelta

from stock.models import Product, Category
from sales.models import Sale, SaleItem
from suppliers.models import SupplierCreditAccount, SupplierDelivery, SupplierPayment
from deposits.models import DepositCustomer, DepositRecord, GoodsPickup
from stock.views import role_required

# Create your views here.
# ── Helpers ────────────────────────────────────────────────────

def parse_date(value, fallback):
    """Safely parse a date string from GET params."""
    try:
        return date.fromisoformat(value)
    except (TypeError, ValueError):
        return fallback


# ── Sales Report ───────────────────────────────────────────────

@role_required(['store_manager', 'admin'])
def sales_report(request):
    # Default date range — current month
    today = date.today()
    default_from = today.replace(day=1)
    default_to = today

    date_from = parse_date(request.GET.get('date_from'), default_from)
    date_to = parse_date(request.GET.get('date_to'), default_to)
    customer_type = request.GET.get('customer_type', '')
    group_by = request.GET.get('group_by', 'day')

    # Base queryset
    sales = Sale.objects.filter(
        sale_date__date__gte=date_from,
        sale_date__date__lte=date_to,
    )

    if customer_type:
        sales = sales.filter(customer_type=customer_type)

    # Summary totals
    summary = sales.aggregate(
        total_sales=Count('id'),
        total_revenue=Sum('grand_total'),
        total_subtotal=Sum('subtotal'),
        total_transport=Sum('transport_charge'),
    )

    # Totals by customer type
    by_customer_type = sales.values('customer_type').annotate(
        count=Count('id'),
        revenue=Sum('grand_total'),
    ).order_by('customer_type')

    # Totals by transport status
    by_transport = sales.values('transport_status').annotate(
        count=Count('id'),
        revenue=Sum('grand_total'),
    )

    # Group sales over time
    if group_by == 'week':
        trunc = TruncWeek('sale_date')
    elif group_by == 'month':
        trunc = TruncMonth('sale_date')
    else:
        trunc = TruncDay('sale_date')

    sales_over_time = sales.annotate(
        period=trunc
    ).values('period').annotate(
        count=Count('id'),
        revenue=Sum('grand_total'),
    ).order_by('period')

    # Top selling products in period
    top_products = SaleItem.objects.filter(
        sale__in=sales
    ).values(
        'product__name', 'product__unit'
    ).annotate(
        total_qty=Sum('quantity'),
        total_revenue=Sum('line_total'),
    ).order_by('-total_revenue')[:10]

    # Individual sales list
    sales_list = sales.select_related('served_by').order_by('-sale_date')

    context = {
        'date_from': date_from,
        'date_to': date_to,
        'customer_type': customer_type,
        'group_by': group_by,
        'summary': summary,
        'by_customer_type': by_customer_type,
        'by_transport': by_transport,
        'sales_over_time': sales_over_time,
        'top_products': top_products,
        'sales_list': sales_list,
        'customer_type_choices': Sale.CUSTOMER_TYPE_CHOICES,
        'today': today,
    }
    return render(request, 'reports/sales_report.html', context)


# ── Stock Report ───────────────────────────────────────────────

@role_required(['store_manager', 'admin'])
def stock_report(request):
    category_id = request.GET.get('category', '')
    status = request.GET.get('status', '')

    products = Product.objects.select_related('category').all()

    if category_id:
        products = products.filter(category_id=category_id)

    if status == 'low':
        products = products.filter(
            quantity_in_stock__lte=F('low_stock_threshold')
        )
    elif status == 'out':
        products = products.filter(quantity_in_stock=0)
    elif status == 'ok':
        products = products.filter(
            quantity_in_stock__gt=F('low_stock_threshold')
        )

    # Summary
    all_products = Product.objects.all()
    total_products = all_products.count()
    out_of_stock = all_products.filter(quantity_in_stock=0).count()
    low_stock = all_products.filter(
        quantity_in_stock__lte=F('low_stock_threshold'),
        quantity_in_stock__gt=0
    ).count()
    healthy = all_products.filter(
        quantity_in_stock__gt=F('low_stock_threshold')
    ).count()

    # Stock value calculations
    total_cost_value = sum(
        p.unit_cost * p.quantity_in_stock for p in all_products
    )
    total_retail_value = sum(
        p.retail_price * p.quantity_in_stock for p in all_products
    )
    potential_profit = total_retail_value - total_cost_value

    # Stock by category
    by_category = Category.objects.annotate(
        product_count=Count('product'),
        total_units=Sum('product__quantity_in_stock'),
    ).order_by('name')

    context = {
        'products': products,
        'categories': Category.objects.all(),
        'selected_category': category_id,
        'selected_status': status,
        'total_products': total_products,
        'out_of_stock': out_of_stock,
        'low_stock': low_stock,
        'healthy': healthy,
        'total_cost_value': total_cost_value,
        'total_retail_value': total_retail_value,
        'potential_profit': potential_profit,
        'by_category': by_category,
    }
    return render(request, 'reports/stock_report.html', context)


# ── Supplier Credit Report ─────────────────────────────────────

@role_required(['admin'])
def credit_report(request):
    today = date.today()
    default_from = today.replace(day=1)
    default_to = today

    date_from = parse_date(request.GET.get('date_from'), default_from)
    date_to = parse_date(request.GET.get('date_to'), default_to)
    status = request.GET.get('status', '')
    supplier_id = request.GET.get('supplier', '')

    credits = SupplierCreditAccount.objects.select_related(
        'delivery__supplier'
    ).all()

    if status == 'pending':
        credits = credits.filter(is_cleared=False)
    elif status == 'cleared':
        credits = credits.filter(is_cleared=True)
    elif status == 'overdue':
        credits = credits.filter(
            is_cleared=False,
            due_date__lt=today
        )

    if supplier_id:
        credits = credits.filter(delivery__supplier_id=supplier_id)

    # Summary
    all_credits = SupplierCreditAccount.objects.all()
    total_credit = all_credits.aggregate(
        total=Sum('total_amount')
    )['total'] or 0
    total_paid = all_credits.aggregate(
        total=Sum('amount_paid')
    )['total'] or 0
    total_outstanding = total_credit - total_paid
    overdue_count = all_credits.filter(
        is_cleared=False,
        due_date__lt=today
    ).count()

    # Payment history in period
    payments = SupplierPayment.objects.filter(
        payment_date__gte=date_from,
        payment_date__lte=date_to,
    ).select_related(
        'credit_account__delivery__supplier'
    ).order_by('-payment_date')

    payments_total = payments.aggregate(
        total=Sum('amount')
    )['total'] or 0

    # By supplier summary
    from suppliers.models import Supplier
    suppliers = Supplier.objects.annotate(
        delivery_count=Count('deliveries'),
    )

    context = {
        'credits': credits,
        'payments': payments,
        'date_from': date_from,
        'date_to': date_to,
        'status': status,
        'supplier_id': supplier_id,
        'total_credit': total_credit,
        'total_paid': total_paid,
        'total_outstanding': total_outstanding,
        'overdue_count': overdue_count,
        'payments_total': payments_total,
        'suppliers': suppliers,
        'today': today,
    }
    return render(request, 'reports/credit_report.html', context)


# ── Deposit Scheme Report ──────────────────────────────────────

@role_required(['admin', 'sales_attendant'])
def deposit_report(request):
    today = date.today()
    default_from = today.replace(day=1)
    default_to = today

    date_from = parse_date(request.GET.get('date_from'), default_from)
    date_to = parse_date(request.GET.get('date_to'), default_to)
    status = request.GET.get('status', '')

    # All customers
    customers = DepositCustomer.objects.filter(is_active=True)

    # Deposits in period
    deposits = DepositRecord.objects.filter(
        payment_date__date__gte=date_from,
        payment_date__date__lte=date_to,
    ).select_related('customer', 'product')

    # Pending pickups — customers who deposited enough
    pending_pickups = []
    for customer in customers:
        for deposit in customer.deposits.filter(pickups__isnull=True):
            total = customer.total_deposited()
            if total >= deposit.product.retail_price:
                pending_pickups.append({
                    'customer': customer,
                    'deposit': deposit,
                    'total_deposited': total,
                    'product': deposit.product,
                })

    # Completed pickups in period
    pickups = GoodsPickup.objects.filter(
        pickup_date__date__gte=date_from,
        pickup_date__date__lte=date_to,
    ).select_related('deposit__customer', 'deposit__product')

    # Summary
    total_customers = customers.count()
    total_deposits_amount = DepositRecord.objects.aggregate(
        total=Sum('amount_paid')
    )['total'] or 0
    period_deposits_amount = deposits.aggregate(
        total=Sum('amount_paid')
    )['total'] or 0
    period_deposits_count = deposits.count()
    pickups_count = pickups.count()

    # Deposits by product
    by_product = deposits.values(
        'product__name'
    ).annotate(
        count=Count('id'),
        total_amount=Sum('amount_paid'),
    ).order_by('-total_amount')

    context = {
        'date_from': date_from,
        'date_to': date_to,
        'status': status,
        'deposits': deposits,
        'pending_pickups': pending_pickups,
        'pickups': pickups,
        'total_customers': total_customers,
        'total_deposits_amount': total_deposits_amount,
        'period_deposits_amount': period_deposits_amount,
        'period_deposits_count': period_deposits_count,
        'pickups_count': pickups_count,
        'by_product': by_product,
    }
    return render(request, 'reports/deposit_report.html', context)