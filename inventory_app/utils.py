from django.db.models import F, Sum, Count
from datetime import datetime
from datetime import timedelta
from .models import Product, OrderItem, ProductCategory, Store, CustomUser, Expense
from django.utils.timezone import now
# from django.utils.timezone import make_aware


def total_revenue_day():
    today = datetime.now().date()
    revenue = (
        OrderItem.objects.filter(timestamp__date=today)
        .annotate(revenue=F('product__price') * F('quantity'))  # Calculate revenue per item
        .aggregate(total_revenue=Sum('revenue'))['total_revenue'] or 0.0
    )
    formatted_revenue = f"{revenue:,.2f}"
    return formatted_revenue


def total_revenue_week():
    today = datetime.now().date()
    week_start = today - timedelta(days=today.weekday())  # Start of the week
    week_end = week_start + timedelta(days=6)  # End of the week

    revenue = (
        OrderItem.objects.filter(timestamp__date__range=[week_start, week_end])
        .annotate(revenue=F('product__price') * F('quantity'))
        .aggregate(total_revenue=Sum('revenue'))['total_revenue'] or 0.0
    )
    formatted_revenue = f"{revenue:,.2f}"
    return formatted_revenue


def total_revenue_month():
    today = datetime.now()
    current_month = today.month
    current_year = today.year

    revenue = (
        OrderItem.objects.filter(timestamp__month=current_month, timestamp__year=current_year)
        .annotate(revenue=F('product__price') * F('quantity'))  # Calculate revenue per item
        .aggregate(total_revenue=Sum('revenue'))['total_revenue'] or 0.0
    )
    formatted_revenue = f"{revenue:,.2f}"
    return formatted_revenue


def total_revenue_annual():
    today = datetime.now()
    current_year = today.year

    revenue = (
        OrderItem.objects.filter(timestamp__year=current_year)
        .annotate(revenue=F('product__price') * F('quantity'))  # Calculate revenue per item
        .aggregate(total_revenue=Sum('revenue'))['total_revenue'] or 0.0
    )
    formatted_revenue = f"{revenue:,.2f}"
    return formatted_revenue


def create_order_items_from_invoice(invoice_data):

    for product_id, quantity in invoice_data.items():
        product = Product.objects.get(id=product_id)

        # Create an OrderItem
        OrderItem.objects.create(
            product=product,
            quantity=quantity,
            timestamp=now(),
        )





def get_top_products_by_quantity_today():
    today = datetime.now().date()
    return (
        OrderItem.objects.filter(timestamp__gte=today)
        .values('product__name')  # Group by product name
        .annotate(total_quantity=Sum('quantity'))  # Sum of quantities sold
        .order_by('-total_quantity')[:5]  # Top 5 results
    )


def get_top_products_by_quantity_week():
    today = datetime.now().date()
    week_start = today - timedelta(days=today.weekday())  # Start of the week
    week_end = week_start + timedelta(days=6)

    return (
            OrderItem.objects.filter(timestamp__date__range=[week_start, week_end])
            .values('product__name')  # Group by product name
            .annotate(total_quantity=Sum('quantity'))  # Sum of quantities sold
            .order_by('-total_quantity')[:5]  # Top 5 results
        )

def get_top_products_by_quantity_month():
    today = datetime.now()
    current_month = today.month
    current_year = today.year

    return (
        OrderItem.objects.filter(timestamp__month=current_month, timestamp__year=current_year)
        .values('product__name')  # Group by product name
        .annotate(total_quantity=Sum('quantity'))  # Sum of quantities sold
        .order_by('-total_quantity')[:5]  # Top 5 results
    )


def get_top_products_by_revenue_today():
    today = datetime.now().date()
    return (
        OrderItem.objects.filter(timestamp__gte=today)
        .values('product__name')  # Group by product name
        .annotate(total_revenue=Sum(F('quantity') * F('product__price')))  # Sum of quantities sold
        .order_by('-total_revenue')[:5]  # Top 5 results
    )

def get_top_products_by_revenue_week():
    today = datetime.now().date()
    week_start = today - timedelta(days=today.weekday())  # Start of the week
    week_end = week_start + timedelta(days=6)

    return (
        OrderItem.objects.filter(timestamp__date__range=[week_start, week_end])
        .values('product__name')  # Group by product name
        .annotate(total_revenue=Sum(F('quantity') * F('product__price')))  # Sum of quantities sold
        .order_by('-total_revenue')[:5]  # Top 5 results
    )

def get_top_products_by_revenue_month():
    today = datetime.now()
    current_month = today.month
    current_year = today.year

    return (
        OrderItem.objects.filter(timestamp__month=current_month, timestamp__year=current_year)
        .values('product__name')  # Group by product name
        .annotate(total_revenue=Sum(F('quantity') * F('product__price')))  # Sum of quantities sold
        .order_by('-total_revenue')[:5]  # Top 5 results
    )

# calculate total profit

def total_profit_day():
    today = datetime.now().date()
    profit_data = (
        OrderItem.objects.filter(timestamp__date=today)
        .annotate(profit=(F('product__price') - F('product__price_bought')) * F('quantity'))
        .aggregate(total_profit=Sum('profit'))
    )
    profit = profit_data['total_profit'] or 0.0  # Ensure profit is a number, even if None
    formatted_profit = f"{profit:,.2f}"  # Properly format the profit as a float
    return formatted_profit


def total_profit_week():
    today = datetime.now().date()
    week_start = today - timedelta(days=today.weekday())  # Start of the week
    week_end = week_start + timedelta(days=6)  # End of the week

    profit_data = (
        OrderItem.objects.filter(timestamp__date__range=[week_start, week_end])
        .annotate(profit=(F('product__price') - F('product__price_bought')) * F('quantity'))
        .aggregate(total_profit=Sum('profit'))
    )
    profit = profit_data['total_profit'] or 0.0  # Ensure profit is a number, even if None
    formatted_profit = f"{profit:,.2f}"  # Properly format the profit as a float
    return formatted_profit




def total_profit_month():
    today = datetime.now().date()
    current_month = today.month
    current_year = today.year

    profit_data = (
        OrderItem.objects.filter(timestamp__month=current_month, timestamp__year=current_year)
        .annotate(profit=(F('product__price') - F('product__price_bought')) * F('quantity'))
        .aggregate(total_profit=Sum('profit'))
    )
    profit = profit_data['total_profit'] or 0.0  # Ensure profit is a number, even if None
    formatted_profit = f"{profit:,.2f}"  # Properly format the profit as a float
    return formatted_profit



def total_profit_year():
    today = datetime.now().date()
    current_year = today.year

    profit_data = (
        OrderItem.objects.filter(timestamp__year=current_year)
        .annotate(profit=(F('product__price') - F('product__price_bought')) * F('quantity'))
        .aggregate(total_profit=Sum('profit'))
    )
    profit = profit_data['total_profit'] or 0.0  # Ensure profit is a number, even if None
    formatted_profit = f"{profit:,.2f}"  # Properly format the profit as a float
    return formatted_profit


def get_totals():
    # Fetch totals for the desired models
    total_products = Product.objects.count()
    total_categories = ProductCategory.objects.count()
    total_stores = Store.objects.count()
    total_employees = CustomUser.objects.filter(role__in=['cashier', 'admin', 'manager']).count()

    # Return results as a dictionary
    return {
        "total_products": total_products,
        "total_categories": total_categories,
        "total_stores": total_stores,
        "total_employees": total_employees,
    }


# function to calculate monthly revenue and profit in chart
def monthly_revenue_and_profit():
    current_year = datetime.now().year
    data = (
        OrderItem.objects.filter(timestamp__year=current_year)
        .annotate(
            month=F('timestamp__month'),
            profit=(F('product__price') - F('product__price_bought')) * F('quantity'),
            revenue=F('product__price') * F('quantity'),
        )
        .values('month')
        .annotate(
            total_revenue=Sum('revenue'),
            total_profit=Sum('profit'),
        )
        .order_by('month')
    )

    # Format results for use in the chart
    chart_data = {
        "months": [],
        "revenues": [],
        "profits": [],
    }

    for entry in data:
        chart_data["months"].append(entry['month'])
        chart_data["revenues"].append(entry['total_revenue'] or 0.0)
        chart_data["profits"].append(entry['total_profit'] or 0.0)

    return chart_data




# utils.py
def daily_revenue_profit_expense():
    current_date = datetime.now().date()
    data = (
        OrderItem.objects.filter(timestamp__date=current_date)
        .annotate(
            day=F('timestamp__day'),
            profit=(F('product__price') - F('product__price_bought')) * F('quantity'),
            revenue=F('product__price') * F('quantity'),
        )
        .values('day')
        .annotate(
            total_revenue=Sum('revenue'),
            total_profit=Sum('profit'),
        )
    )

    expenses = (
        Expense.objects.filter(timestamp__date=current_date)
        .aggregate(total=Sum('amount'))['total'] or 0.0
    )

    chart_data = {
        "days": [],
        "revenues": [],
        "profits": [],
        "expenses": [expenses],  # Include daily expenses
    }

    for entry in data:
        chart_data["days"].append(entry['day'])
        chart_data["revenues"].append(entry['total_revenue'] or 0.0)
        chart_data["profits"].append(entry['total_profit'] or 0.0)

    return chart_data
