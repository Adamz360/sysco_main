from django.contrib.auth import logout, get_user_model
from django.conf import settings
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.decorators.csrf import csrf_protect
from .models import Product, Transaction, ProductCategory, ReceiverEmail, LowStockNotification, CustomUser, Store,Expense
from .forms import TransactionForm, EmployeeCreationForm, ProductForm, CategoryForm, EmailForm, StoreForm, ExpenseForm
from django.contrib import messages
from django.http import JsonResponse, HttpResponseBadRequest
from django.utils import timezone
from django.contrib.auth.views import LoginView
from django.urls import reverse_lazy
import json
from .forms import TransactionFilterForm
from django.forms import TextInput, Select
from django.core.mail import send_mail
from django.db.models import F, Count
from django.apps import apps
from django.core.paginator import Paginator
from django.utils.timezone import now
from django.db.models import Sum
from .utils import (total_revenue_day, total_revenue_week,
                    total_revenue_month, total_revenue_annual,
                    create_order_items_from_invoice,
                    get_top_products_by_quantity_today, get_top_products_by_quantity_week,
                    get_top_products_by_quantity_month, get_top_products_by_revenue_today,
                    get_top_products_by_revenue_week, get_top_products_by_revenue_month,total_profit_day,
                    total_profit_week, total_profit_month, total_profit_year, get_totals, monthly_revenue_and_profit,
                    daily_revenue_profit_expense)
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.timezone import now, make_aware
from datetime import timedelta
from django.db import transaction as db_transaction  # For atomicity
import logging
# from .tasks import send_low_stock_email


logger = logging.getLogger(__name__)


################################################################

class CustomLoginView(LoginView):
    def get_redirect_url(self):
        # Check if the user is an employee and redirect accordingly
        if self.request.user.is_authenticated:
            # Assuming 'is_staff' field determines admin/admins, adjust this condition as needed
            if self.request.user.is_staff:
                # Redirect admin to a dashboard or admin page
                return reverse_lazy('dashboard')
            else:
                # Redirect employee to sales page
                return reverse_lazy('sales_page')
        return super().get_redirect_url()


def dashboard(request):
    daily_revenue = total_revenue_day()
    weekly_revenue = total_revenue_week()
    monthly_revenue = total_revenue_month()
    annual_revenue = total_revenue_annual()
    top_selling_products_today = get_top_products_by_quantity_today()
    top_selling_products_week = get_top_products_by_quantity_week()
    top_selling_products_month = get_top_products_by_quantity_month()
    top_selling_products_revenue_today = get_top_products_by_revenue_today()
    top_selling_products_revenue_week = get_top_products_by_revenue_week()
    top_selling_products_revenue_month = get_top_products_by_revenue_month()
    profit_day = total_profit_day()
    profit_week = total_profit_week()
    profit_month = total_profit_month()
    profit_year = total_profit_year()
    get_all_total = get_totals()
    monthly_data = monthly_revenue_and_profit()
    daily_data = daily_revenue_profit_expense()

    monthly_data = {
        "months": monthly_data["months"],
        "revenues": [float(revenue) for revenue in monthly_data["revenues"]],
        "profits": [float(profit) for profit in monthly_data["profits"]],
    }

    daily_data = {
        "days": daily_data["days"],
        "revenues": [float(revenue) for revenue in daily_data["revenues"]],
        "profits": [float(profit) for profit in daily_data["profits"]],
    }

    # Prepare context data with all revenue values
    context = {
        'total_revenue_day': daily_revenue,
        'total_revenue_week': weekly_revenue,
        'total_revenue_month': monthly_revenue,
        'total_revenue_year': annual_revenue,
        'top_sale_today': top_selling_products_today,
        'top_sale_week': top_selling_products_week,
        'top_sale_month': top_selling_products_month,
        'top_sale_revenue_today': top_selling_products_revenue_today,
        'top_sale_revenue_week': top_selling_products_revenue_week,
        'top_sale_revenue_month': top_selling_products_revenue_month,
        'profit_day_total': profit_day,
        'profit_week_total': profit_week,
        'profit_month_total': profit_month,
        'profit_year_total': profit_year,
        'totals': get_all_total,
        'monthly_data': monthly_data,
        'daily_data': daily_data,

    }
    return render(request, 'admin_dashboard/dashboard.html', context)


@login_required
def product_list(request):
    products = Product.objects.all()

    paginator = Paginator(products, 20)
    page_number = request.GET.get('page')
    paginated_products = paginator.get_page(page_number)

    return render(request, 'inventory_page/product_list_page.html', {
        'products': products,
        'products_paginated': paginated_products
    })


@login_required
def email_list(request):
    mails = ReceiverEmail.objects.all()
    return render(request, 'inventory_page/email_list.html', {'mails': mails})

@login_required
def category_list(request):
    product_categories = ProductCategory.objects.all()
    return render(request, 'inventory_page/category_list_page.html', {'categories': product_categories})


@login_required
def product_detail(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    return render(request, 'inventory_page/product_detail.html', {'product': product})


@login_required
def transaction_create(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    if request.method == 'POST':
        form = TransactionForm(request.POST)
        if form.is_valid():
            with db_transaction.atomic():
                transaction = form.save(commit=False)
                transaction.product = product
                transaction.employee = request.user
                if transaction.transaction_type == 'REMOVE' and product.quantity < transaction.quantity:
                    messages.error(request, "Insufficient stock.")
                    return redirect('product_detail', product_id=product.id)
                transaction.save()
                product.quantity += transaction.quantity if transaction.transaction_type == 'ADD' else -transaction.quantity
                product.save()
                # notify_low_stock(request, product)

            messages.success(request, "Transaction processed successfully.")
            return redirect('product_detail', product_id=product.id)
    else:
        form = TransactionForm()

    return render(request, 'inventory/transaction_form.html', {'form': form, 'product': product})



# Admin check decorator
def admin_required(view_func):
    return user_passes_test(lambda u: u.is_staff)(view_func)


@login_required
@admin_required
def add_employee(request):
    if request.method == 'POST':
        form = EmployeeCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])  # Set the password
            # Check role and set is_staff accordingly
            if form.cleaned_data['role'] == 'admin':  # Role field value for "Admin"
                user.is_staff = True
            else:
                user.is_staff = False

            user.save()
            messages.success(request, f"Employee {user.first_name} {user.last_name} has been created successfully.")
            return redirect('employee_list')  # Redirect to a list of employees or a suitable page
    else:
        form = EmployeeCreationForm()

    return render(request, 'inventory_page/add_employee_page.html', {'form': form})


@login_required
@admin_required
def create_category(request):
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Category created successfully.")
            return redirect('category_list')
    else:
        form = CategoryForm()
    return render(request, 'inventory_page/create_category_page.html', {'form': form})


@login_required
@admin_required
def create_store(request):
    if request.method == 'POST':
        form = StoreForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Store created successfully.")
            return redirect('store_list')
    else:
        form = StoreForm()
    return render(request, 'inventory_page/create_store.html', {'form': form})


@login_required
@admin_required
def delete_store(request, store_id):
    store = get_object_or_404(Store, id=store_id)
    if request.method == 'POST':
        store.delete()
        messages.success(request, "store deleted successfully.")
        return redirect('store_list')
    return render(request, 'inventory_page/delete_store.html', {'store': store})


@login_required
@admin_required
def store_list(request):
    product_store = Store.objects.all()
    return render(request, 'inventory_page/store_list_page.html', {'stores': product_store})

@login_required
@admin_required
# def expense_list(request):
#     expenses = Expense.objects.all().order_by('-timestamp')
#     total_expenses = expenses.aggregate(total=Sum('amount'))['total'] or 0.0
#     return render(request, 'inventory_page/expense_list.html', {'expenses': expenses, 'total_expenses': total_expenses})


def expense_list(request):
    form = ExpenseForm(request.GET or None)
    expenses = Expense.objects.all().order_by('-timestamp')

    # Filter expenses by date if the form is valid
    if form.is_valid():
        if form.cleaned_data.get('start_date'):
            expenses = expenses.filter(timestamp__gte=form.cleaned_data['start_date'])
        if form.cleaned_data.get('end_date'):
            expenses = expenses.filter(timestamp__lte=form.cleaned_data['end_date'])

     # Add pagination
    paginator = Paginator(expenses, 10)  # Show 10 expenses per page
    page_number = request.GET.get('page')
    paginated_expenses = paginator.get_page(page_number)

    # Calculate the total expenses
    total_expenses = expenses.aggregate(total=Sum('amount'))['total'] or 0.0

    return render(
        request, 
        'inventory_page/expense_list.html', 
        {
            'form': form,
            'expenses': paginated_expenses, 
            'total_expenses': total_expenses
        }
    )


# def transaction_history(request):
#     form = TransactionFilterForm(request.GET or None)
#     transactions = Transaction.objects.all().order_by('-timestamp')

#     for field_name in form.fields:
#         field = form.fields[field_name]
#         if isinstance(field.widget, (TextInput, Select)):
#             field.widget.attrs['class'] = 'form-control'

#     if form.is_valid():
#         transactions = form.filter_transactions()

#     paginator = Paginator(transactions, 20)  
#     page_number = request.GET.get('page')
#     paginated_transactions = paginator.get_page(page_number)

#     return render(request, 'inventory_page/transaction_history.html', {
#         'form': form,
#         'transactions': paginated_transactions
#     })














@login_required
@admin_required
def add_expense(request):
    if request.method == 'POST':
        form = ExpenseForm(request.POST)
        if form.is_valid():
            form.save()  # Saves the form to the database
            messages.success(request, "Expense added successfully.")
            return redirect('expense_list')  # Adjust the redirect to your needs
        else:
            messages.error(request, "There was an error with your form submission.")
    else:
        form = ExpenseForm()

    return render(request, 'inventory_page/add_expense.html', {'form': form})


@login_required
@admin_required
def create_product(request):
    if request.method == 'POST':
        form = ProductForm(request.POST)
        if form.is_valid():
            product = form.save()

            transaction = Transaction(
                product=product,
                employee=request.user,  # The logged-in user
                transaction_type='ADD',  # Assuming items are being ADDED
                quantity=form.cleaned_data.get('quantity'),  # Get quantity from form data
            )
            transaction.save()

            messages.success(request, "Product created successfully.")
            return redirect('product_list')

        # # Create a transaction for each item

    else:
        form = ProductForm()
    return render(request, 'inventory_page/create_product_page.html', {'form': form})

@login_required
@admin_required
def add_email(request):
    if request.method == 'POST':
        form = EmailForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request,"Email Saved Successfully.")
            return redirect("email_list")
    else:
        form = EmailForm()
    return render(request, 'inventory_page/add_email.html', {'form': form})


@login_required
@admin_required
def delete_email(request, email_id):
    email = get_object_or_404(ReceiverEmail, id=email_id)
    if request.method == 'POST':
        email.delete()
        messages.success(request, "Email deleted successfully.")
        return redirect('email_list')
    return render(request, 'inventory_page/delete_email.html', {'email': email})


@login_required
@admin_required
def update_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    if request.method == 'POST':
        form = ProductForm(request.POST, instance=product)
        if form.is_valid():
            with db_transaction.atomic():  # Ensure data consistency
                updated_product = form.save()

                # Save transaction only if the form is valid and saved successfully
                Transaction.objects.create(
                    product=updated_product,
                    employee=request.user,  # Logged-in user
                    transaction_type='UPDATE',  # Use 'UPDATE' for clarity
                    quantity=form.cleaned_data.get('quantity'),  # Quantity from form
                )

            messages.success(request, "Product updated successfully.")
            return redirect('product_detail', product_id=product.id)
    else:
        form = ProductForm(instance=product)

    return render(request, 'inventory_page/update_product.html', {'form': form, 'product': product})




@login_required
@admin_required
def delete_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    if request.method == 'POST':
        product.delete()
        messages.success(request, "Product deleted successfully.")
        return redirect('product_list')
    return render(request, 'inventory_page/delete_product.html', {'product': product})


@login_required
@admin_required
def delete_category(request, category_id):
    category = get_object_or_404(ProductCategory, id=category_id)
    if request.method == 'POST':
        category.delete()
        messages.success(request, "Category deleted successfully.")
        return redirect('category_list')
    return render(request, 'inventory_page/delete_category.html', {'category': category})


@login_required
@admin_required
def employee_list(request):
    User = apps.get_model(settings.AUTH_USER_MODEL)
    # Now filter based on the user model
    employees = User.objects.filter(is_staff=False)
    admin_list = User.objects.filter(is_staff=True)

    return render(request, 'inventory_page/employee_list_page.html', {'employees': employees, 'admin_list': admin_list})


@login_required
def sales_page(request):
    categories = ProductCategory.objects.all()
    # Get products for the first category if any exists
    initial_products = []
    if categories.exists():
        initial_products = Product.objects.filter(category=categories.first())
    
    context = {
        'categories': categories,
        'initial_products': initial_products,
    }
    return render(request, 'inventory_page/product_sales_page.html', context)


@login_required
def products_by_category(request, category_id):
    try:
        products = Product.objects.filter(category_id=category_id)

        product_data = [
            {
                'id': product.id,
                'name': product.name,
                'price': float(product.price)
            }
            for product in products
        ]
        return JsonResponse({'products': product_data})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)




########################################################################################################################
@csrf_protect
@login_required
def invoice_print(request):
    if request.method == "POST":
        items_json = request.POST.get('items')
        if not items_json or items_json == "[]":
            return HttpResponseBadRequest("No items were added to the invoice.")

        try:
            items = json.loads(items_json)
        except json.JSONDecodeError:
            return HttpResponseBadRequest("Invalid JSON data.")

        insufficient_products = []

        for item in items:
            product_id = item.get('id')
            quantity = item.get('quantity', 0)
            try:
                product = Product.objects.get(id=product_id)
                if product.quantity < quantity:
                    insufficient_products.append({
                        'name': product.name,
                        'available_quantity': product.quantity,
                        'requested_quantity': quantity
                    })
            except Product.DoesNotExist:
                return HttpResponseBadRequest(f"Product with ID {product_id} does not exist.")

        if insufficient_products:
            # Render a page showing insufficient products
            return render(request, 'inventory_page/insufficient_stock.html', {
                'insufficient_products': insufficient_products,
                'back_url': 'sales_page'  # Update with your actual sales page URL name
            })

        # Process the transaction if all products have sufficient stock
        invoice_data = {}

        for item in items:
            product_id = item.get('id')
            quantity = item.get('quantity', 0)
            product = Product.objects.get(id=product_id)

            # Create a transaction
            transaction = Transaction(
                product=product,
                employee=request.user,
                transaction_type='REMOVE',
                quantity=quantity,
            )
            transaction.save()

            # Update product stock
            product.quantity -= quantity
            product.save()

            invoice_data[product_id] = quantity

        # Handle the invoice creation
        create_order_items_from_invoice(invoice_data)

        # Calculate grand total
        grand_total = sum(item.get('quantity', 0) * item.get('price', 0) for item in items)

        # Prepare context for the invoice
        context = {
            'items': items,
            'grand_total': grand_total,
            'payment_method': request.POST.get('payment_method', 'Cash'),
            'employee_name': f"{request.user.first_name} {request.user.last_name}",
            'date': timezone.now().strftime("%Y-%m-%d"),
            'time': timezone.now().strftime("%H:%M:%S"),
        }
        return render(request, 'inventory_page/invoice_print.html', context)
    else:
        return redirect('sales_page')



def get_product_quantity(request, product_id):
    try:
        product = Product.objects.get(id=product_id)
        return JsonResponse({'available_quantity': product.quantity})
    except Product.DoesNotExist:
        return JsonResponse({'error': 'Product not found'}, status=404)



@login_required
@admin_required
def update_category(request, category_id):
    category = get_object_or_404(ProductCategory, id=category_id)
    if request.method == 'POST':
        name = request.POST.get('name')
        if name:
            category.name = name
            category.save()
            messages.success(request, "Category updated successfully.")
            return redirect('category_list')
    return render(request, 'inventory/update_category.html', {'category': category})


@login_required
@admin_required
def delete_employee(request, employee_id):
    User = get_user_model()
    employee = get_object_or_404(User, id=employee_id)
    if request.method == 'POST':
        employee.delete()
        messages.success(request, "Employee deleted successfully.")
        return redirect('employee_list')
    return render(request, 'inventory_page/delete_employee.html', {'employee': employee})

@login_required
@admin_required
def delete_admin(request, admin_id):
    admin = get_object_or_404(CustomUser, pk=admin_id)
    if request.method == 'POST':
        admin.delete()
        messages.success(request, "Admin deleted successfully.")
        return redirect('employee_list')
    return render(request, 'inventory_page/delete_employee.html', {'admin_list': admin})



@login_required
@admin_required
def transaction_history(request):
    form = TransactionFilterForm(request.GET or None)
    transactions = Transaction.objects.all().order_by('-timestamp')

    for field_name in form.fields:
        field = form.fields[field_name]
        if isinstance(field.widget, (TextInput, Select)):
            field.widget.attrs['class'] = 'form-control'

    if form.is_valid():
        transactions = form.filter_transactions()

    paginator = Paginator(transactions, 20)  
    page_number = request.GET.get('page')
    paginated_transactions = paginator.get_page(page_number)

    return render(request, 'inventory_page/transaction_history.html', {
        'form': form,
        'transactions': paginated_transactions
    })




@login_required
@admin_required
def notification_view(request):
    low_stock_products = Product.objects.filter(quantity__lte=F('low_stock_threshold'))

    alerts = []
    for product in low_stock_products:
        alerts.append({
            'product_name': product.name,
            'quantity': product.quantity,
            'low_stock_threshold': product.low_stock_threshold,
            'timestamp': product.updated_at,
        })

    return render(request, 'inventory_page/notification_page.html', {'alerts': alerts})




@receiver(post_save, sender=Product)
def create_low_stock_notification(sender, instance, **kwargs):
    if instance.quantity <= instance.low_stock_threshold:
        if not LowStockNotification.objects.filter(product=instance, resolved=False).exists():
            LowStockNotification.objects.create(product=instance)
    else:
        LowStockNotification.objects.filter(product=instance, resolved=False).update(resolved=True)


